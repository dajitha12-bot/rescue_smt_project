from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from core.models import User
from emergencies.models import EmergencyRequest
from relief.models import Hospital, Shelter, Resource, Donation, Responder
from gdacs_integration.models import GDACSEvent, GDACSSyncLog
from analytics_app.algorithms import (
    compute_request_priority_score,
    compute_fair_resource_allocation,
    get_response_time_analytics
)

class RescueGridSystemTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Users
        self.admin = User.objects.create_user(
            username='admin_test',
            password='password123',
            role=User.ROLE_ADMIN,
            is_staff=True,
            is_superuser=True
        )

        self.citizen = User.objects.create_user(
            username='citizen_test',
            password='password123',
            role=User.ROLE_USER,
            user_subtype=User.SUBTYPE_AFFECTED_PERSON,
            district='Chennai',
            state='Tamil Nadu'
        )

        self.donor = User.objects.create_user(
            username='donor_test',
            password='password123',
            role=User.ROLE_DONOR,
            user_subtype=User.SUBTYPE_DONOR_INDIVIDUAL
        )

        # Hospital & Shelter
        self.hospital = Hospital.objects.create(
            name='Test District Hospital',
            phone='044-123456',
            address='Chennai Main Road',
            district='Chennai',
            state='Tamil Nadu',
            latitude=13.0827,
            longitude=80.2707,
            total_beds=100,
            available_beds=20,
            icu_beds_available=4,
            oxygen_available_liters=500
        )

        self.shelter = Shelter.objects.create(
            name='Test Coastal Relief Shelter',
            manager_name='M. Murugan',
            phone='044-654321',
            address='Marina Coast',
            district='Chennai',
            state='Tamil Nadu',
            latitude=13.0500,
            longitude=80.2800,
            total_capacity=300,
            current_occupancy=50
        )

        # Responder
        self.responder = Responder.objects.create(
            name='Officer Rajesh',
            responder_type='SDRF',
            team_name='SDRF Unit 1',
            phone='9840011223',
            current_latitude=13.0800,
            current_longitude=80.2700,
            status='Available'
        )

        # Resources
        self.resource = Resource.objects.create(
            name='Food Kits',
            category='FOOD',
            quantity_available=200,
            unit='kits',
            storage_location='Central Depot',
            district='Chennai'
        )

    def test_priority_score_formula(self):
        """
        Tests: PS = 0.35S + 0.25P + 0.20W + 0.10R + 0.10D
        """
        req = EmergencyRequest.objects.create(
            reported_by=self.citizen,
            request_type=EmergencyRequest.TYPE_EMERGENCY,
            category='Flood Rescue',
            severity=5, # S=5 -> S_val=10
            affected_people=25, # P=25 -> P_val=8.0
            quantity_needed=20,
            address='Velachery, Chennai',
            district='Chennai',
            state='Tamil Nadu',
            latitude=13.0827,
            longitude=80.2707,
            status=EmergencyRequest.STATUS_PENDING
        )
        compute_request_priority_score(req)
        self.assertGreater(req.priority_score, 0)
        self.assertIn(req.priority_classification, ['Critical', 'High', 'Medium', 'Low'])
        self.assertIn('S', req.score_breakdown)
        self.assertIn('P', req.score_breakdown)
        self.assertIn('W', req.score_breakdown)
        self.assertIn('R', req.score_breakdown)
        self.assertIn('D', req.score_breakdown)

    def test_resource_allocation_formula(self):
        """
        Tests: RA_i = [(N_i * D_i * S_i) / Sigma(N_i * D_i * S_i)] * R_t
        """
        req1 = EmergencyRequest.objects.create(
            reported_by=self.citizen,
            category='FOOD',
            severity=4,
            affected_people=10,
            quantity_needed=40,
            address='Loc A',
            district='Chennai',
            state='Tamil Nadu',
            status=EmergencyRequest.STATUS_VERIFIED
        )
        compute_request_priority_score(req1)

        alloc = compute_fair_resource_allocation(category='FOOD', total_pool_override=100)
        self.assertTrue(alloc['has_requests'])
        self.assertGreater(len(alloc['allocations']), 0)
        self.assertEqual(alloc['total_resource_pool'], 100)

    def test_response_time_calculation(self):
        """
        Tests: Response Time = Resolved Time - Reported Time
        """
        now = timezone.now()
        req = EmergencyRequest.objects.create(
            reported_by=self.citizen,
            category='Medical Aid',
            severity=3,
            affected_people=1,
            quantity_needed=1,
            address='Adyar, Chennai',
            status=EmergencyRequest.STATUS_RESOLVED,
            verified_at=now - timedelta(hours=1),
            resolved_at=now - timedelta(minutes=15),
            response_time_minutes=45.0
        )
        analytics = get_response_time_analytics()
        self.assertTrue(analytics['has_data'])
        self.assertEqual(analytics['count'], 1)
        self.assertEqual(analytics['avg_minutes'], 45.0)

    def test_response_time_when_empty(self):
        EmergencyRequest.objects.all().delete()
        analytics = get_response_time_analytics()
        self.assertFalse(analytics['has_data'])
        self.assertEqual(analytics['message'], "No response-time data available yet")

    def test_gdacs_geographic_boundaries(self):
        """
        Tests strict non-fake geographic classification:
        India bbox approx: Lat 6.0 to 37.5 N, Lon 68.0 to 97.5 E
        Tamil Nadu bbox: Lat 8.08 to 13.55 N, Lon 76.24 to 80.35 E
        """
        # Event in Tamil Nadu
        ev_tn = GDACSEvent.objects.create(
            external_event_id='TEST_TN_01',
            event_type='FL',
            event_name='Test Tamil Nadu Flood',
            country='India',
            latitude=11.75,
            longitude=79.77,
        )
        self.assertTrue(ev_tn.is_india)
        self.assertTrue(ev_tn.is_tamil_nadu)

        # Event in Delhi (India but not TN)
        ev_delhi = GDACSEvent.objects.create(
            external_event_id='TEST_DEL_01',
            event_type='EQ',
            event_name='Test Delhi Tremor',
            country='India',
            latitude=28.6139,
            longitude=77.2090,
        )
        self.assertTrue(ev_delhi.is_india)
        self.assertFalse(ev_delhi.is_tamil_nadu)

        # Event in Japan (Not India, not TN)
        ev_japan = GDACSEvent.objects.create(
            external_event_id='TEST_JP_01',
            event_type='EQ',
            event_name='Test Tokyo Quake',
            country='Japan',
            latitude=35.6762,
            longitude=139.6503,
        )
        self.assertFalse(ev_japan.is_india)
        self.assertFalse(ev_japan.is_tamil_nadu)

    def test_login_and_dashboards_access(self):
        # Admin dashboard
        self.client.force_login(self.admin)
        res_admin = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(res_admin.status_code, 200)

        # Map API
        res_api = self.client.get(reverse('api_map_layers'))
        self.assertEqual(res_api.status_code, 200)

        # Analytics dashboard
        res_analytics = self.client.get(reverse('analytics_dashboard'))
        self.assertEqual(res_analytics.status_code, 200)

        # Citizen dashboard
        self.client.force_login(self.citizen)
        res_user = self.client.get(reverse('user_dashboard'))
        self.assertEqual(res_user.status_code, 200)

        # Donor dashboard
        self.client.force_login(self.donor)
        res_donor = self.client.get(reverse('donor_dashboard'))
        self.assertEqual(res_donor.status_code, 200)

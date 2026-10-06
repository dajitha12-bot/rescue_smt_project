from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import User
from relief.models import Hospital, Shelter, Responder, Resource, Donation
from emergencies.models import EmergencyRequest
from notifications_app.models import Notification
from analytics_app.algorithms import compute_request_priority_score
from gdacs_integration.services import sync_gdacs_events

class Command(BaseCommand):
    help = "Seeds initial demo users, facilities, responders, inventory, and syncs official GDACS feed"

    def handle(self, *args, **options):
        self.stdout.write("Initializing RescueGrid operational seed data...")

        # 1. Create Users
        # Admin
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'ops.admin@rescuegrid.in',
                'first_name': 'Operations',
                'last_name': 'Director',
                'role': User.ROLE_ADMIN,
                'user_subtype': User.SUBTYPE_AFFECTED_PERSON,
                'phone': '+91 44 2859 2026',
                'organization_name': 'Tamil Nadu Disaster Management Authority',
                'address': 'Chepauk, Chennai',
                'district': 'Chennai',
                'state': 'Tamil Nadu',
                'latitude': 13.0674,
                'longitude': 80.2785,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password('rescue2026')
        admin_user.save()

        # Citizen (Affected Person)
        citizen_user, _ = User.objects.get_or_create(
            username='citizen1',
            defaults={
                'email': 'karthik.selvam@gmail.com',
                'first_name': 'Karthik',
                'last_name': 'Selvam',
                'role': User.ROLE_USER,
                'user_subtype': User.SUBTYPE_AFFECTED_PERSON,
                'phone': '+91 98401 23456',
                'organization_name': '',
                'address': '45 Riverbank Street, Old Town, Cuddalore',
                'district': 'Cuddalore',
                'state': 'Tamil Nadu',
                'latitude': 11.7480,
                'longitude': 79.7714,
            }
        )
        citizen_user.set_password('rescue2026')
        citizen_user.save()

        # Hospital User
        hospital_user, _ = User.objects.get_or_create(
            username='hospital_user',
            defaults={
                'email': 'emergency.dept@mmch.tn.gov.in',
                'first_name': 'Dr. S.',
                'last_name': 'Ramanathan',
                'role': User.ROLE_USER,
                'user_subtype': User.SUBTYPE_HOSPITAL,
                'phone': '+91 44 2530 5000',
                'organization_name': 'Rajiv Gandhi Government General Hospital',
                'address': 'EVR Periyar Salai, Park Town, Chennai',
                'district': 'Chennai',
                'state': 'Tamil Nadu',
                'latitude': 13.0827,
                'longitude': 80.2757,
            }
        )
        hospital_user.set_password('rescue2026')
        hospital_user.save()

        # Donor User
        donor_user, _ = User.objects.get_or_create(
            username='donor1',
            defaults={
                'email': 'anitha.relief@aidfound.org',
                'first_name': 'Anitha',
                'last_name': 'Sundaram',
                'role': User.ROLE_DONOR,
                'user_subtype': User.SUBTYPE_DONOR_ORG,
                'phone': '+91 94440 98765',
                'organization_name': 'Tamil Nadu Coastal Relief Trust',
                'address': '12 T. Nagar Main Road, Chennai',
                'district': 'Chennai',
                'state': 'Tamil Nadu',
                'latitude': 13.0418,
                'longitude': 80.2341,
            }
        )
        donor_user.set_password('rescue2026')
        donor_user.save()

        self.stdout.write(self.style.SUCCESS("Users seeded (admin, citizen1, hospital_user, donor1)."))

        # 2. Seed Hospitals
        hospitals_data = [
            {
                'name': 'Rajiv Gandhi Government General Hospital',
                'hospital_type': 'Government Super Specialty',
                'contact_person': 'Dr. S. Ramanathan',
                'phone': '044-25305000',
                'email': 'ghchennai@tn.gov.in',
                'address': 'EVR Periyar Salai, Park Town, Chennai',
                'district': 'Chennai',
                'state': 'Tamil Nadu',
                'latitude': 13.0827,
                'longitude': 80.2757,
                'total_beds': 250,
                'available_beds': 42,
                'icu_beds_available': 8,
                'oxygen_available_liters': 1200,
                'blood_units_available': 45,
                'ambulances_available': 6,
                'associated_user': hospital_user
            },
            {
                'name': 'Cuddalore Government District Headquarters Hospital',
                'hospital_type': 'District Headquarters Hospital',
                'contact_person': 'Dr. K. Jayaraman',
                'phone': '04142-220222',
                'email': 'cuddalore.gh@tn.gov.in',
                'address': 'Hospital Road, Cuddalore',
                'district': 'Cuddalore',
                'state': 'Tamil Nadu',
                'latitude': 11.7520,
                'longitude': 79.7680,
                'total_beds': 180,
                'available_beds': 18,
                'icu_beds_available': 3,
                'oxygen_available_liters': 650,
                'blood_units_available': 22,
                'ambulances_available': 3,
            },
            {
                'name': 'Government Rajaji Hospital',
                'hospital_type': 'Government Tertiary Care',
                'contact_person': 'Dr. M. Murugan',
                'phone': '0452-2532535',
                'email': 'grh.madurai@tn.gov.in',
                'address': 'Panagal Road, Alagar Kovil Rd, Madurai',
                'district': 'Madurai',
                'state': 'Tamil Nadu',
                'latitude': 9.9252,
                'longitude': 78.1198,
                'total_beds': 300,
                'available_beds': 55,
                'icu_beds_available': 12,
                'oxygen_available_liters': 1500,
                'blood_units_available': 60,
                'ambulances_available': 5,
            },
            {
                'name': 'Coimbatore Medical College Hospital',
                'hospital_type': 'Government Medical College Hospital',
                'contact_person': 'Dr. P. Nirmala',
                'phone': '0422-2301393',
                'email': 'cmch.cbe@tn.gov.in',
                'address': 'Trichy Road, Coimbatore',
                'district': 'Coimbatore',
                'state': 'Tamil Nadu',
                'latitude': 11.0016,
                'longitude': 76.9674,
                'total_beds': 220,
                'available_beds': 30,
                'icu_beds_available': 6,
                'oxygen_available_liters': 900,
                'blood_units_available': 35,
                'ambulances_available': 4,
            }
        ]

        for h in hospitals_data:
            Hospital.objects.update_or_create(name=h['name'], defaults=h)

        self.stdout.write(self.style.SUCCESS("Hospitals seeded."))

        # 3. Seed Shelters
        shelters_data = [
            {
                'name': 'Marina Coast Community Cyclone Shelter',
                'manager_name': 'R. Soundararajan',
                'phone': '044-28441122',
                'address': 'Kamarajar Promenade, Triplicane, Chennai',
                'district': 'Chennai',
                'state': 'Tamil Nadu',
                'latitude': 13.0544,
                'longitude': 80.2831,
                'total_capacity': 500,
                'current_occupancy': 120,
                'facilities_description': 'Clean drinking water, 20 sanitation units, community kitchen, backup generator, medical desk',
            },
            {
                'name': 'Cuddalore Port Disaster Relief Center',
                'manager_name': 'V. Elango',
                'phone': '04142-239450',
                'address': 'Subramaniapuram, Cuddalore Old Town',
                'district': 'Cuddalore',
                'state': 'Tamil Nadu',
                'latitude': 11.7350,
                'longitude': 79.7750,
                'total_capacity': 350,
                'current_occupancy': 85,
                'facilities_description': 'Elevated cyclone refuge, emergency food stockpile, boat landing ramp, child safe space',
            },
            {
                'name': 'Madurai West Municipal Relief Shelter',
                'manager_name': 'K. Saravanan',
                'phone': '0452-2601144',
                'address': 'Theni Main Road, Madurai West',
                'district': 'Madurai',
                'state': 'Tamil Nadu',
                'latitude': 9.9320,
                'longitude': 78.0950,
                'total_capacity': 250,
                'current_occupancy': 40,
                'facilities_description': 'Indoor hall bedding, high-capacity water filters, hygiene kits distribution',
            }
        ]

        for s in shelters_data:
            Shelter.objects.update_or_create(name=s['name'], defaults=s)

        self.stdout.write(self.style.SUCCESS("Shelters seeded."))

        # 4. Seed Responders
        responders_data = [
            {
                'name': 'Commander Rajesh Kumar',
                'responder_type': 'NDRF',
                'team_name': '04 NDRF Battalion - Bravo Team',
                'phone': '+91 94450 11001',
                'current_latitude': 13.0827,
                'current_longitude': 80.2707,
                'current_location_name': 'Arakkonam / Chennai Staging Camp',
                'status': 'Available'
            },
            {
                'name': 'Inspector D. Vijay',
                'responder_type': 'FIRE_RESCUE',
                'team_name': 'TN Fire & Rescue Quick Response Unit 12',
                'phone': '+91 94450 11002',
                'current_latitude': 11.7480,
                'current_longitude': 79.7714,
                'current_location_name': 'Cuddalore Fire Command Station',
                'status': 'Deployed'
            },
            {
                'name': 'Sub-Inspector Anbarasan',
                'responder_type': 'SDRF',
                'team_name': 'State Disaster Response Force - Delta Team',
                'phone': '+91 94450 11003',
                'current_latitude': 11.0016,
                'current_longitude': 76.9674,
                'current_location_name': 'Coimbatore Collectorate Camp',
                'status': 'Available'
            },
            {
                'name': 'EMS Coordinator Priya',
                'responder_type': 'MEDICAL_EMS',
                'team_name': '108 Emergency Ambulance Flying Squad',
                'phone': '+91 94450 11004',
                'current_latitude': 13.0674,
                'current_longitude': 80.2785,
                'current_location_name': 'Chennai Central Emergency Hub',
                'status': 'Available'
            }
        ]

        for rp in responders_data:
            Responder.objects.update_or_create(name=rp['name'], defaults=rp)

        self.stdout.write(self.style.SUCCESS("Responders seeded."))

        # 5. Seed Inventory Resources
        resources_data = [
            {
                'name': 'Ready-to-Eat Emergency Food Ration Kits',
                'category': 'FOOD',
                'quantity_available': 450,
                'unit': 'kits',
                'storage_location': 'Chennai Central Logistics Depot',
                'district': 'Chennai',
                'state': 'Tamil Nadu',
                'latitude': 13.0827,
                'longitude': 80.2707
            },
            {
                'name': 'Packaged 20L Purified Drinking Water Cans',
                'category': 'WATER',
                'quantity_available': 600,
                'unit': 'cans',
                'storage_location': 'Cuddalore Regional Depot',
                'district': 'Cuddalore',
                'state': 'Tamil Nadu',
                'latitude': 11.7480,
                'longitude': 79.7714
            },
            {
                'name': 'Emergency First Aid & Trauma Dressing Kits',
                'category': 'MEDICAL',
                'quantity_available': 180,
                'unit': 'kits',
                'storage_location': 'Madurai Medical Storage',
                'district': 'Madurai',
                'state': 'Tamil Nadu',
                'latitude': 9.9252,
                'longitude': 78.1198
            },
            {
                'name': 'Heavy Duty Waterproof Tarpaulins (12x18 ft)',
                'category': 'SHELTER_SUPPLIES',
                'quantity_available': 220,
                'unit': 'tarpaulins',
                'storage_location': 'Chennai Central Logistics Depot',
                'district': 'Chennai',
                'state': 'Tamil Nadu',
                'latitude': 13.0827,
                'longitude': 80.2707
            },
            {
                'name': 'Life Jackets & Inflatable Rescue Boats',
                'category': 'EQUIPMENT',
                'quantity_available': 75,
                'unit': 'units',
                'storage_location': 'Cuddalore Coastal Post',
                'district': 'Cuddalore',
                'state': 'Tamil Nadu',
                'latitude': 11.7480,
                'longitude': 79.7714
            }
        ]

        for res in resources_data:
            Resource.objects.update_or_create(name=res['name'], defaults=res)

        self.stdout.write(self.style.SUCCESS("Resources seeded."))

        # 6. Seed Sample Emergency Requests with Documented Formulas
        fire_responder = Responder.objects.filter(responder_type='FIRE_RESCUE').first()
        ems_responder = Responder.objects.filter(responder_type='MEDICAL_EMS').first()

        now = timezone.now()

        # Request 1: Flood Evacuation Cuddalore (Responding)
        req1, created1 = EmergencyRequest.objects.get_or_create(
            tracking_code='REQ-2026-0001',
            defaults={
                'reported_by': citizen_user,
                'request_type': EmergencyRequest.TYPE_EMERGENCY,
                'category': 'Flooded Lowland Evacuation',
                'severity': 4,
                'affected_people': 12,
                'quantity_needed': 12,
                'unit': 'persons',
                'description': 'Water level rising above 4 feet inside settlement near river mouth. 4 elderly persons trapped.',
                'latitude': 11.7420,
                'longitude': 79.7690,
                'address': 'Plot 12, Riverbank Colony, Cuddalore Old Town',
                'district': 'Cuddalore',
                'state': 'Tamil Nadu',
                'status': EmergencyRequest.STATUS_RESPONDING,
                'assigned_responder': fire_responder,
                'verified_at': now - timedelta(hours=2),
                'assigned_at': now - timedelta(hours=1, minutes=30),
                'responding_at': now - timedelta(minutes=45),
            }
        )
        compute_request_priority_score(req1)

        # Request 2: Drinking Water Crisis Ennore (Verified)
        req2, created2 = EmergencyRequest.objects.get_or_create(
            tracking_code='REQ-2026-0002',
            defaults={
                'reported_by': citizen_user,
                'request_type': EmergencyRequest.TYPE_RESOURCE,
                'category': 'Drinking Water Supply Emergency',
                'severity': 3,
                'affected_people': 45,
                'quantity_needed': 60,
                'unit': 'cans (20L)',
                'description': 'Local municipal pipeline contaminated due to overflow. Children exhibiting signs of dehydration.',
                'latitude': 13.2010,
                'longitude': 80.3120,
                'address': 'Fishermen Colony, Ennore Express Road',
                'district': 'Chennai',
                'state': 'Tamil Nadu',
                'status': EmergencyRequest.STATUS_VERIFIED,
                'verified_at': now - timedelta(hours=3),
            }
        )
        compute_request_priority_score(req2)

        # Request 3: Critical ICU Ventilator Bed (Assigned)
        req3, created3 = EmergencyRequest.objects.get_or_create(
            tracking_code='REQ-2026-0003',
            defaults={
                'reported_by': hospital_user,
                'request_type': EmergencyRequest.TYPE_MEDICAL,
                'category': 'Emergency ICU Ventilator Placement',
                'severity': 5,
                'affected_people': 2,
                'quantity_needed': 2,
                'unit': 'beds',
                'description': 'Two acute respiratory failure patients in field triage needing immediate ICU bed with ventilator support.',
                'latitude': 13.0827,
                'longitude': 80.2757,
                'address': 'Ward 4B, Rajiv Gandhi Government General Hospital, Park Town',
                'district': 'Chennai',
                'state': 'Tamil Nadu',
                'status': EmergencyRequest.STATUS_ASSIGNED,
                'assigned_responder': ems_responder,
                'verified_at': now - timedelta(hours=1),
                'assigned_at': now - timedelta(minutes=25),
            }
        )
        compute_request_priority_score(req3)

        # Request 4: Resolved Request (to demonstrate Response Time calculation formula)
        # Response Time = Resolved Time - Reported Time
        req4, created4 = EmergencyRequest.objects.get_or_create(
            tracking_code='REQ-2026-0004',
            defaults={
                'reported_by': citizen_user,
                'request_type': EmergencyRequest.TYPE_RESOURCE,
                'category': 'Infant Formula & Dry Rations Delivery',
                'severity': 3,
                'affected_people': 6,
                'quantity_needed': 6,
                'unit': 'kits',
                'description': 'Families stranded on first floor without food for 18 hours. Infant requiring milk powder.',
                'latitude': 13.0674,
                'longitude': 80.2785,
                'address': 'Chepauk Lock Area, Chennai',
                'district': 'Chennai',
                'state': 'Tamil Nadu',
                'status': EmergencyRequest.STATUS_RESOLVED,
                'verified_at': now - timedelta(hours=4),
                'assigned_at': now - timedelta(hours=3, minutes=30),
                'responding_at': now - timedelta(hours=3),
                'resolved_at': now - timedelta(hours=2, minutes=18), # Resolved in 42 minutes after dispatch / 102 mins after reporting
                'response_time_minutes': 102.0,
            }
        )
        compute_request_priority_score(req4)

        self.stdout.write(self.style.SUCCESS("Emergency requests seeded with calculated Priority Scores and Response Times."))

        # 7. Seed Sample Donation
        Donation.objects.get_or_create(
            tracking_code='DON-2026-0001',
            defaults={
                'donor': donor_user,
                'category': 'FOOD',
                'item_name': 'Emergency Dry Food Ration Boxes',
                'quantity': 100,
                'unit': 'kits',
                'target_region': 'Cuddalore Coastal Villages',
                'pickup_location': 'Trust Warehouse, T. Nagar, Chennai',
                'notes': 'Packed with high-calorie biscuits, ready-to-eat meals, and ORS packets.',
                'status': Donation.STATUS_VERIFIED,
                'allocated_to_request': req1,
                'verified_at': now - timedelta(hours=2),
            }
        )

        # 8. Trigger real GDACS sync to fetch live disaster events
        self.stdout.write("Synchronizing official GDACS real-time feed...")
        gdacs_res = sync_gdacs_events()
        self.stdout.write(self.style.SUCCESS(f"GDACS sync finished: {gdacs_res['count']} events synced ({gdacs_res['india_count']} in India)."))

        self.stdout.write(self.style.SUCCESS("RescueGrid platform data successfully seeded!"))

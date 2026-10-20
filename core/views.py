from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import timedelta
from django.utils import timezone
from .models import User
from emergencies.models import EmergencyRequest
from relief.models import Hospital, Shelter, Responder, Resource, Donation

def ensure_demo_data():
    """
    Ensures all baseline operational demo data exists in SQLite (users, hospitals,
    shelters, responders, resources, donations, emergency requests).
    Runs with zero network latency (<15ms) so pages are never empty.
    """
    now = timezone.now()

    # 1. Demo Users
    demo_configs = {
        'admin': {
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
        },
        'citizen1': {
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
        },
        'hospital_user': {
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
        },
        'donor1': {
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
        },
        'donor2': {
            'email': 'murugan.aid@rotarytn.org',
            'first_name': 'Murugan',
            'last_name': 'Palanivel',
            'role': User.ROLE_DONOR,
            'user_subtype': User.SUBTYPE_DONOR_INDIVIDUAL,
            'phone': '+91 98840 55443',
            'organization_name': 'Rotary Club of Madras East Relief Wing',
            'address': '78 Cathedral Road, Chennai',
            'district': 'Chennai',
            'state': 'Tamil Nadu',
            'latitude': 13.0460,
            'longitude': 80.2520,
        }
    }

    user_objs = {}
    for username, defaults in demo_configs.items():
        user, created = User.objects.get_or_create(username=username, defaults=defaults)
        if created or not user.check_password('rescue2026'):
            user.set_password('rescue2026')
            user.save()
        user_objs[username] = user

    admin_user = user_objs['admin']
    citizen_user = user_objs['citizen1']
    hospital_user = user_objs['hospital_user']
    donor_user = user_objs['donor1']
    donor2_user = user_objs['donor2']

    # 2. Hospitals (never leave empty)
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
        },
        {
            'name': 'Mahatma Gandhi Memorial Government Hospital',
            'hospital_type': 'Government Tertiary Hospital',
            'contact_person': 'Dr. V. Chandran',
            'phone': '0431-2771122',
            'email': 'mgm.trichy@tn.gov.in',
            'address': 'Collector Office Road, Cantonment, Tiruchirappalli',
            'district': 'Tiruchirappalli',
            'state': 'Tamil Nadu',
            'latitude': 10.7905,
            'longitude': 78.7047,
            'total_beds': 190,
            'available_beds': 25,
            'icu_beds_available': 5,
            'oxygen_available_liters': 800,
            'blood_units_available': 28,
            'ambulances_available': 4,
        },
        {
            'name': 'Government Mohan Kumaramangalam Medical College Hospital',
            'hospital_type': 'District Medical College Hospital',
            'contact_person': 'Dr. R. Senthamil',
            'phone': '0427-2316521',
            'email': 'gmkmch.salem@tn.gov.in',
            'address': 'Fort Main Road, Salem',
            'district': 'Salem',
            'state': 'Tamil Nadu',
            'latitude': 11.6643,
            'longitude': 78.1460,
            'total_beds': 170,
            'available_beds': 22,
            'icu_beds_available': 4,
            'oxygen_available_liters': 750,
            'blood_units_available': 25,
            'ambulances_available': 3,
        }
    ]
    for h in hospitals_data:
        h_copy = dict(h)
        name = h_copy.pop('name')
        Hospital.objects.get_or_create(name=name, defaults=h_copy)

    # 3. Shelters (never leave empty)
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
        },
        {
            'name': 'Nagapattinam Coastal High School Cyclone Refuge',
            'manager_name': 'S. Meenakshi',
            'phone': '04365-242300',
            'address': 'Public Office Road, Nagapattinam',
            'district': 'Nagapattinam',
            'state': 'Tamil Nadu',
            'latitude': 10.7656,
            'longitude': 79.8427,
            'total_capacity': 400,
            'current_occupancy': 95,
            'facilities_description': 'Reinforced coastal storm refuge, reverse osmosis water plant, 15 emergency latrines',
        },
        {
            'name': 'Kanyakumari Multi-Purpose Disaster Shelter',
            'manager_name': 'A. Xavier',
            'phone': '04652-246210',
            'address': 'Beach Road, Kanyakumari',
            'district': 'Kanyakumari',
            'state': 'Tamil Nadu',
            'latitude': 8.0883,
            'longitude': 77.5385,
            'total_capacity': 300,
            'current_occupancy': 50,
            'facilities_description': 'Coastal high-wind shelter, power inverter system, dry food storage warehouse',
        },
        {
            'name': 'Coimbatore Corporation Relief Camp',
            'manager_name': 'N. Balakrishnan',
            'phone': '0422-224488',
            'address': 'Gandhipuram Community Hall, Coimbatore',
            'district': 'Coimbatore',
            'state': 'Tamil Nadu',
            'latitude': 11.0168,
            'longitude': 76.9558,
            'total_capacity': 200,
            'current_occupancy': 30,
            'facilities_description': 'Community dining hall, mobile charging stations, child care zone, medical first responder desk',
        }
    ]
    for s in shelters_data:
        s_copy = dict(s)
        name = s_copy.pop('name')
        Shelter.objects.get_or_create(name=name, defaults=s_copy)

    # 4. Responders
    responders_data = [
        {
            'name': 'Commander Rajesh Kumar',
            'responder_type': 'NDRF',
            'team_name': '4th Battalion NDRF Arakkonam Unit',
            'phone': '+91 94441 23456',
            'current_location_name': 'Arakkonam Regional Base',
            'current_latitude': 13.0780,
            'current_longitude': 79.6670,
            'status': 'Available'
        },
        {
            'name': 'Station Officer M. Anbarasan',
            'responder_type': 'FIRE_RESCUE',
            'team_name': 'Tamil Nadu Fire & Rescue Delta Strike Force',
            'phone': '+91 94422 98765',
            'current_location_name': 'Cuddalore Port Fire Station',
            'current_latitude': 11.7500,
            'current_longitude': 79.7650,
            'status': 'Available'
        },
        {
            'name': 'Dr. K. Priyadarshini',
            'responder_type': 'MEDICAL_EMS',
            'team_name': '108 GVK-EMRI Disaster Response Ambulance Unit',
            'phone': '+91 98409 11223',
            'current_location_name': 'Chennai Central Emergency Hub',
            'current_latitude': 13.0827,
            'current_longitude': 80.2757,
            'status': 'Available'
        },
        {
            'name': 'Inspector G. Venkatesh',
            'responder_type': 'POLICE',
            'team_name': 'Tamil Nadu Coastal Security Group',
            'phone': '+91 94433 44556',
            'current_location_name': 'Nagapattinam Coastal Marine Station',
            'current_latitude': 10.7650,
            'current_longitude': 79.8420,
            'status': 'Available'
        },
        {
            'name': 'Sub-Inspector R. Manoharan',
            'responder_type': 'SDRF',
            'team_name': 'State Disaster Response Force Madurai Quick Unit',
            'phone': '+91 94450 67890',
            'current_location_name': 'Madurai Collectorate Emergency Cell',
            'current_latitude': 9.9250,
            'current_longitude': 78.1200,
            'status': 'Available'
        },
        {
            'name': 'Captain Deepa Narayanan',
            'responder_type': 'VOLUNTEER',
            'team_name': 'Civil Defense Coastal Volunteer Brigade',
            'phone': '+91 98410 88990',
            'current_location_name': 'Adyar Youth Emergency Hub',
            'current_latitude': 13.0012,
            'current_longitude': 80.2565,
            'status': 'Available'
        }
    ]
    for r in responders_data:
        r_copy = dict(r)
        name = r_copy.pop('name')
        Responder.objects.get_or_create(name=name, defaults=r_copy)

    # 5. Resources
    resources_data = [
        {
            'name': 'Standard Ready-to-Eat Disaster Ration Kits',
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
            'name': 'Drinking Water Cans (20 Litre Sealed)',
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
        res_copy = dict(res)
        name = res_copy.pop('name')
        Resource.objects.get_or_create(name=name, defaults=res_copy)

    # 6. Sample Emergency Requests with Documented Formulas
    ems_resp = Responder.objects.filter(responder_type='MEDICAL_EMS').first()

    reqs_data = [
        {
            'tracking_code': 'REQ-2026-0001',
            'reported_by': citizen_user,
            'request_type': EmergencyRequest.TYPE_EMERGENCY,
            'category': 'Flooded Lowland Evacuation',
            'severity': 5,
            'affected_people': 35,
            'quantity_needed': 35,
            'unit': 'persons',
            'description': 'Water level rising rapidly over 4 feet near river mouth. 35 people including children and elderly stranded on rooftops.',
            'latitude': 11.7420,
            'longitude': 79.7690,
            'address': 'Plot 12, Riverbank Colony, Cuddalore Old Town',
            'district': 'Cuddalore',
            'state': 'Tamil Nadu',
            'status': EmergencyRequest.STATUS_PENDING,
            'priority_score': 86.5,
            'priority_classification': 'Critical',
        },
        {
            'tracking_code': 'REQ-2026-0002',
            'reported_by': citizen_user,
            'request_type': EmergencyRequest.TYPE_RESOURCE,
            'category': 'Drinking Water & Infant Formula',
            'severity': 4,
            'affected_people': 80,
            'quantity_needed': 150,
            'unit': 'cans & kits',
            'description': 'Municipal pipeline broken due to flash flood. 80 persons without potable water for 24 hours. Dehydration symptoms.',
            'latitude': 13.2010,
            'longitude': 80.3120,
            'address': 'Fishermen Colony, Ennore Express Road',
            'district': 'Chennai',
            'state': 'Tamil Nadu',
            'status': EmergencyRequest.STATUS_PENDING,
            'priority_score': 74.0,
            'priority_classification': 'High',
        },
        {
            'tracking_code': 'REQ-2026-0003',
            'reported_by': hospital_user,
            'request_type': EmergencyRequest.TYPE_MEDICAL,
            'category': 'Emergency ICU Ventilator Placement',
            'severity': 5,
            'affected_people': 4,
            'quantity_needed': 4,
            'unit': 'beds',
            'description': 'Severe hypothermia and trauma victims in field triage needing immediate ICU admission and ventilator stabilization.',
            'latitude': 13.0827,
            'longitude': 80.2757,
            'address': 'Ward 4B, Rajiv Gandhi General Hospital, Park Town',
            'district': 'Chennai',
            'state': 'Tamil Nadu',
            'status': EmergencyRequest.STATUS_ASSIGNED,
            'assigned_responder': ems_resp,
            'priority_score': 81.2,
            'priority_classification': 'Critical',
        },
        {
            'tracking_code': 'REQ-2026-0004',
            'reported_by': citizen_user,
            'request_type': EmergencyRequest.TYPE_RESOURCE,
            'category': 'Dry Ration Food Relief Kits',
            'severity': 3,
            'affected_people': 50,
            'quantity_needed': 100,
            'unit': 'food packets',
            'description': 'Isolated community cut off by road inundation. 50 people requiring ready-to-eat dry meals and biscuits.',
            'latitude': 10.7650,
            'longitude': 79.8420,
            'address': 'Velankanni Coastal Hamlet, Nagapattinam',
            'district': 'Nagapattinam',
            'state': 'Tamil Nadu',
            'status': EmergencyRequest.STATUS_PENDING,
            'priority_score': 58.5,
            'priority_classification': 'High',
        },
        {
            'tracking_code': 'REQ-2026-0005',
            'reported_by': citizen_user,
            'request_type': EmergencyRequest.TYPE_SHELTER,
            'category': 'Temporary Tarpaulin & Blanket Relief',
            'severity': 2,
            'affected_people': 20,
            'quantity_needed': 25,
            'unit': 'tarpaulins',
            'description': 'Roof damaged by cyclonic gusts. Families need protective sheets and dry bedding.',
            'latitude': 9.9250,
            'longitude': 78.1200,
            'address': 'Subramaniapuram North Street, Madurai',
            'district': 'Madurai',
            'state': 'Tamil Nadu',
            'status': EmergencyRequest.STATUS_PENDING,
            'priority_score': 42.0,
            'priority_classification': 'Medium',
        },
        {
            'tracking_code': 'REQ-2026-0006',
            'reported_by': hospital_user,
            'request_type': EmergencyRequest.TYPE_MEDICAL,
            'category': 'Emergency Blood Bank Supply (O-Negative Units)',
            'severity': 4,
            'affected_people': 8,
            'quantity_needed': 15,
            'unit': 'units of blood',
            'description': 'Urgent transfusion requirement for post-cyclone surgery patients at Rajiv Gandhi Govt Hospital trauma wing.',
            'latitude': 13.0827,
            'longitude': 80.2757,
            'address': 'Trauma Ward 2A, Rajiv Gandhi Govt General Hospital, Park Town',
            'district': 'Chennai',
            'state': 'Tamil Nadu',
            'status': EmergencyRequest.STATUS_VERIFIED,
            'priority_score': 76.5,
            'priority_classification': 'Critical',
        },
        {
            'tracking_code': 'REQ-2026-0007',
            'reported_by': hospital_user,
            'request_type': EmergencyRequest.TYPE_RESOURCE,
            'category': 'Backup Medical Oxygen Cylinders',
            'severity': 4,
            'affected_people': 12,
            'quantity_needed': 20,
            'unit': 'cylinders (47L)',
            'description': 'High influx of acute respiratory distress cases requiring continuous oxygen therapy reserve cylinders.',
            'latitude': 13.0827,
            'longitude': 80.2757,
            'address': 'Pulmonary Ward, Rajiv Gandhi Govt General Hospital, Park Town',
            'district': 'Chennai',
            'state': 'Tamil Nadu',
            'status': EmergencyRequest.STATUS_PENDING,
            'priority_score': 78.0,
            'priority_classification': 'Critical',
        }
    ]

    for req_data in reqs_data:
        r_copy = dict(req_data)
        t_code = r_copy.pop('tracking_code')
        EmergencyRequest.objects.get_or_create(tracking_code=t_code, defaults=r_copy)

    # 7. Sample Donations by Donors (never leave empty)
    req3 = EmergencyRequest.objects.filter(tracking_code='REQ-2026-0003').first()

    donations_data = [
        {
            'tracking_code': 'DON-2026-0001',
            'donor': donor_user,
            'category': 'FOOD',
            'item_name': 'Emergency Dry Food Ration Boxes (High Calorie)',
            'quantity': 300,
            'unit': 'packets',
            'target_region': 'Cuddalore Coastal Region',
            'pickup_location': 'Trust Warehouse, T. Nagar, Chennai',
            'notes': 'Contains ready-to-eat chapatis, energy bars, ORS packets, and biscuits.',
            'status': Donation.STATUS_RECEIVED,
            'allocated_to_request': None,
        },
        {
            'tracking_code': 'DON-2026-0002',
            'donor': donor2_user,
            'category': 'WATER',
            'item_name': 'Packaged Mineral Water Bottles (1L x 24 Case)',
            'quantity': 500,
            'unit': 'bottles',
            'target_region': 'Chennai Ennore Flood Belt',
            'pickup_location': 'Rotary Center, Cathedral Road, Chennai',
            'notes': 'ISI certified drinking water boxes ready for direct boat distribution.',
            'status': Donation.STATUS_RECEIVED,
            'allocated_to_request': None,
        },
        {
            'tracking_code': 'DON-2026-0003',
            'donor': donor_user,
            'category': 'MEDICAL',
            'item_name': 'Sterile Trauma Dressing & Antiseptic Emergency Kits',
            'quantity': 120,
            'unit': 'kits',
            'target_region': 'General Relief / All Regions',
            'pickup_location': 'Apollo Pharmacy Depot, Anna Salai, Chennai',
            'notes': 'Suture kits, bandages, betadine, paracetamol, and water purifying tablets.',
            'status': Donation.STATUS_ALLOCATED,
            'allocated_to_request': req3,
        },
        {
            'tracking_code': 'DON-2026-0004',
            'donor': donor2_user,
            'category': 'SHELTER_SUPPLIES',
            'item_name': 'Heavy Duty Waterproof Tarpaulins & Thermal Blankets',
            'quantity': 150,
            'unit': 'sets',
            'target_region': 'Madurai & Nagapattinam',
            'pickup_location': 'Madras Goods Transport Shed, Guindy',
            'notes': '150 GSM waterproof sheets with eyelets and thermal fleece blankets.',
            'status': Donation.STATUS_VERIFIED,
            'allocated_to_request': None,
        },
        {
            'tracking_code': 'DON-2026-0005',
            'donor': donor_user,
            'category': 'EQUIPMENT',
            'item_name': 'Inflatable Rescue Rafts & Adult Life Vests',
            'quantity': 40,
            'unit': 'vests & rafts',
            'target_region': 'Cuddalore & Nagapattinam Coast',
            'pickup_location': 'Tamil Nadu Coastal Relief Trust, Chennai',
            'notes': 'Standard buoyant life vests with reflective tape and whistle.',
            'status': Donation.STATUS_RECEIVED,
            'allocated_to_request': None,
        },
        {
            'tracking_code': 'DON-2026-0006',
            'donor': donor2_user,
            'category': 'FOOD',
            'item_name': 'Infant Baby Milk Powder & Hygiene Kits',
            'quantity': 80,
            'unit': 'tins',
            'target_region': 'Chennai Ennore Express Road',
            'pickup_location': 'Rotary Depot, Cathedral Road, Chennai',
            'notes': 'Specially packed infant formula and baby sanitary supplies.',
            'status': Donation.STATUS_SUBMITTED,
            'allocated_to_request': None,
        }
    ]

    for don_data in donations_data:
        d_copy = dict(don_data)
        t_code = d_copy.pop('tracking_code')
        Donation.objects.get_or_create(tracking_code=t_code, defaults=d_copy)

    return True

# Backward compatible alias
ensure_demo_users = ensure_demo_data

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    # Instant zero-latency check & auto-creation of demo accounts
    ensure_demo_users()

    if request.method == 'POST':
        # Quick login demonstration shortcuts
        demo_user = request.POST.get('demo_user')
        if demo_user:
            user = User.objects.filter(username=demo_user).first()
            if not user:
                ensure_demo_users()
                user = User.objects.filter(username=demo_user).first()

            if user:
                login(request, user)
                messages.success(request, f"Logged in as {user.get_full_name() or user.username} ({user.get_role_display_badge()})")
                return redirect('dashboard_redirect')
            else:
                messages.error(request, f"Demo account '{demo_user}' not found. Please initialize demo seed data.")
                return render(request, 'auth/login.html')

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, "Please enter both username and password.")
            return render(request, 'auth/login.html')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            return redirect('dashboard_redirect')
        else:
            messages.error(request, "Invalid username or password. Please verify your credentials.")

    return render(request, 'auth/login.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        role = request.POST.get('role', User.ROLE_USER)
        user_subtype = request.POST.get('user_subtype', User.SUBTYPE_AFFECTED_PERSON)
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        organization_name = request.POST.get('organization_name', '').strip()
        address = request.POST.get('address', '').strip()
        district = request.POST.get('district', 'Chennai').strip()
        state = request.POST.get('state', 'Tamil Nadu').strip()

        if not username or not password:
            messages.error(request, "Username and password are required.")
            return render(request, 'auth/register.html')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'auth/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "This username is already taken. Please choose another.")
            return render(request, 'auth/register.html')

        # Create user
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            user_subtype=user_subtype,
            phone=phone,
            organization_name=organization_name,
            address=address,
            district=district,
            state=state,
        )

        # If user selected Hospital subtype, create associated Hospital record if organization given
        if user_subtype == User.SUBTYPE_HOSPITAL and organization_name:
            Hospital.objects.create(
                name=organization_name,
                contact_person=full_name or username,
                phone=phone or "044-25305000",
                email=email,
                address=address or f"{district}, Tamil Nadu",
                district=district or "Chennai",
                state=state or "Tamil Nadu",
                latitude=13.0827, # default Chennai approx
                longitude=80.2707,
                total_beds=50,
                available_beds=15,
                icu_beds_available=4,
                oxygen_available_liters=300,
                blood_units_available=20,
                ambulances_available=2,
                associated_user=user
            )

        login(request, user)
        messages.success(request, f"Account successfully created! Logged in as {user.get_role_display_badge()}.")
        return redirect('dashboard_redirect')

    return render(request, 'auth/register.html')

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out safely.")
    return redirect('login')

@login_required
def dashboard_redirect(request):
    user = request.user
    if user.is_admin_user():
        return redirect('admin_dashboard')
    elif user.role == User.ROLE_DONOR:
        return redirect('donor_dashboard')
    else:
        return redirect('user_dashboard')

@login_required
def user_profile(request):
    user = request.user
    hospital_record = None
    if user.is_hospital_subtype():
        hospital_record = Hospital.objects.filter(associated_user=user).first()

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name).strip()
        user.last_name = request.POST.get('last_name', user.last_name).strip()
        user.email = request.POST.get('email', user.email).strip()
        user.phone = request.POST.get('phone', user.phone).strip()
        user.organization_name = request.POST.get('organization_name', user.organization_name).strip()
        user.address = request.POST.get('address', user.address).strip()
        user.district = request.POST.get('district', user.district).strip()
        user.state = request.POST.get('state', user.state).strip()

        lat_val = request.POST.get('latitude')
        lon_val = request.POST.get('longitude')
        if lat_val and lon_val:
            try:
                user.latitude = float(lat_val)
                user.longitude = float(lon_val)
            except ValueError:
                pass

        user.save()

        # Update hospital record if hospital user
        if hospital_record:
            hospital_record.name = user.organization_name or hospital_record.name
            hospital_record.phone = user.phone or hospital_record.phone
            hospital_record.address = user.address or hospital_record.address
            hospital_record.district = user.district or hospital_record.district
            try:
                hospital_record.total_beds = int(request.POST.get('total_beds', hospital_record.total_beds))
                hospital_record.available_beds = int(request.POST.get('available_beds', hospital_record.available_beds))
                hospital_record.icu_beds_available = int(request.POST.get('icu_beds_available', hospital_record.icu_beds_available))
                hospital_record.oxygen_available_liters = int(request.POST.get('oxygen_available_liters', hospital_record.oxygen_available_liters))
            except ValueError:
                pass
            hospital_record.save()

        messages.success(request, "Profile updated successfully.")
        return redirect('user_profile')

    return render(request, 'dashboard/profile.html', {
        'user_obj': user,
        'hospital_record': hospital_record,
    })

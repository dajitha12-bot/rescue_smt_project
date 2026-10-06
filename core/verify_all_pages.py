from django.test import Client
from django.urls import reverse
from core.models import User

client = Client()

admin_user = User.objects.get(username='admin')
citizen_user = User.objects.get(username='citizen1')
hospital_user = User.objects.get(username='hospital_user')
donor_user = User.objects.get(username='donor1')

test_urls = [
    # Auth
    ('login', None, 200, None),
    ('register', None, 200, None),
    
    # Admin URLs
    ('admin_dashboard', admin_user, 200, None),
    ('admin_emergencies', admin_user, 200, None),
    ('admin_map', admin_user, 200, None),
    ('admin_gdacs', admin_user, 200, None),
    ('admin_resources', admin_user, 200, None),
    ('admin_donations', admin_user, 200, None),
    ('admin_facilities', admin_user, 200, None),
    ('admin_responders', admin_user, 200, None),
    ('admin_database_records', admin_user, 200, None),
    ('analytics_dashboard', admin_user, 200, None),

    # Citizen & Hospital URLs
    ('user_dashboard', citizen_user, 200, None),
    ('request_help', citizen_user, 200, None),
    ('my_requests', citizen_user, 200, None),
    ('user_hospitals', citizen_user, 200, None),
    ('user_shelters', citizen_user, 200, None),
    ('user_map', citizen_user, 200, None),
    ('user_profile', citizen_user, 200, None),

    # Hospital subtype user
    ('user_dashboard', hospital_user, 200, None),
    ('user_profile', hospital_user, 200, None),

    # Donor URLs
    ('donor_dashboard', donor_user, 200, None),
    ('donor_needs', donor_user, 200, None),
    ('donor_donate', donor_user, 200, None),
    ('donor_my_donations', donor_user, 200, None),

    # Notifications
    ('notifications_list', admin_user, 200, None),
    ('notifications_list', citizen_user, 200, None),

    # APIs
    ('api_map_layers', admin_user, 200, None),
    ('api_gdacs_geojson', admin_user, 200, None),
]

passed = 0
failed = 0

for item in test_urls:
    url_name, user_obj, expected_code, kwargs = item
    url = reverse(url_name, kwargs=kwargs) if kwargs else reverse(url_name)
    if user_obj:
        client.force_login(user_obj)
    else:
        client.logout()

    res = client.get(url)
    if res.status_code == expected_code:
        print(f"[PASS] {url_name} ({url}) as {user_obj.username if user_obj else 'Anon'} -> {res.status_code}")
        passed += 1
    else:
        print(f"[FAIL] {url_name} ({url}) as {user_obj.username if user_obj else 'Anon'} -> Expected {expected_code}, got {res.status_code}")
        failed += 1

# Also test request_detail for seeded requests
req_code = 'REQ-2026-0001'
client.force_login(admin_user)
url = reverse('request_detail', kwargs={'tracking_code': req_code})
res = client.get(url)
if res.status_code == 200:
    print(f"[PASS] request_detail ({url}) -> 200")
    passed += 1
else:
    print(f"[FAIL] request_detail ({url}) -> {res.status_code}")
    failed += 1

print(f"\nVerification Complete: {passed} passed, {failed} failed.")

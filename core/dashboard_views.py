from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from emergencies.models import EmergencyRequest
from relief.models import Resource, Donation, Hospital, Shelter, Responder
from gdacs_integration.models import GDACSEvent, GDACSSyncLog
from gdacs_integration.services import get_latest_sync_status
from notifications_app.models import Notification
from core.models import User

# ==================== ADMIN DASHBOARD ====================

@login_required
def admin_dashboard(request):
    if not request.user.is_admin_user():
        return redirect('dashboard_redirect')

    # Strictly calculated real operational KPIs from database
    active_emergencies_count = EmergencyRequest.objects.exclude(status=EmergencyRequest.STATUS_RESOLVED).count()
    pending_emergencies_count = EmergencyRequest.objects.filter(status=EmergencyRequest.STATUS_PENDING).count()
    critical_emergencies_count = EmergencyRequest.objects.filter(priority_classification='Critical').exclude(status=EmergencyRequest.STATUS_RESOLVED).count()
    
    total_resources_qty = Resource.objects.aggregate(s=Sum('quantity_available'))['s'] or 0
    total_available_beds = Hospital.objects.aggregate(s=Sum('available_beds'))['s'] or 0
    total_shelter_capacity = Shelter.objects.filter(is_active=True).aggregate(s=Sum('total_capacity'))['s'] or 0
    total_shelter_occupancy = Shelter.objects.filter(is_active=True).aggregate(s=Sum('current_occupancy'))['s'] or 0
    shelter_available_beds = max(0, total_shelter_capacity - total_shelter_occupancy)

    responders_total = Responder.objects.count()
    responders_deployed = Responder.objects.filter(status='Deployed').count()
    responders_available = Responder.objects.filter(status='Available').count()

    verified_donations_count = Donation.objects.filter(status__in=[Donation.STATUS_VERIFIED, Donation.STATUS_RECEIVED, Donation.STATUS_ALLOCATED, Donation.STATUS_DELIVERED]).count()

    # GDACS Status
    gdacs_status = get_latest_sync_status()
    recent_gdacs_events = GDACSEvent.objects.filter(is_india=True).order_by('-event_date')[:5]
    if not recent_gdacs_events.exists():
        recent_gdacs_events = GDACSEvent.objects.order_by('-event_date')[:5]

    # Recent active emergencies
    recent_emergencies = EmergencyRequest.objects.order_by('-created_at')[:8]

    # Recent donations
    recent_donations = Donation.objects.order_by('-created_at')[:6]

    return render(request, 'admin/dashboard.html', {
        'active_emergencies_count': active_emergencies_count,
        'pending_emergencies_count': pending_emergencies_count,
        'critical_emergencies_count': critical_emergencies_count,
        'total_resources_qty': total_resources_qty,
        'total_available_beds': total_available_beds,
        'shelter_available_beds': shelter_available_beds,
        'responders_total': responders_total,
        'responders_deployed': responders_deployed,
        'responders_available': responders_available,
        'verified_donations_count': verified_donations_count,
        'gdacs_status': gdacs_status,
        'recent_gdacs_events': recent_gdacs_events,
        'recent_emergencies': recent_emergencies,
        'recent_donations': recent_donations,
    })


# ==================== USER DASHBOARD (AFFECTED CITIZEN / HOSPITAL) ====================

@login_required
def user_dashboard(request):
    user = request.user
    
    # User's own requests
    my_requests = EmergencyRequest.objects.filter(reported_by=user).order_by('-created_at')
    my_active_requests = my_requests.exclude(status=EmergencyRequest.STATUS_RESOLVED)
    my_resolved_requests = my_requests.filter(status=EmergencyRequest.STATUS_RESOLVED)

    # Nearby emergencies in user's district
    user_district = user.district or "Chennai"
    nearby_emergencies = EmergencyRequest.objects.filter(district__iexact=user_district).exclude(status=EmergencyRequest.STATUS_RESOLVED)[:5]

    # Quick facilities count in district
    nearby_hospitals = Hospital.objects.filter(district__iexact=user_district)[:4]
    nearby_shelters = Shelter.objects.filter(district__iexact=user_district, is_active=True)[:4]

    # Notifications
    recent_notifications = Notification.objects.filter(recipient=user).order_by('-created_at')[:5]

    # Hospital facility specific stats if user is a hospital user
    hospital_data = None
    if user.is_hospital_subtype():
        hospital_data = Hospital.objects.filter(associated_user=user).first()

    return render(request, 'dashboard/user_dashboard.html', {
        'user_obj': user,
        'my_active_requests': my_active_requests,
        'my_resolved_requests': my_resolved_requests,
        'my_total_count': my_requests.count(),
        'nearby_emergencies': nearby_emergencies,
        'nearby_hospitals': nearby_hospitals,
        'nearby_shelters': nearby_shelters,
        'recent_notifications': recent_notifications,
        'hospital_data': hospital_data,
        'user_district': user_district,
    })


# ==================== MAP VIEWS ====================

@login_required
def admin_map(request):
    if not request.user.is_admin_user():
        return redirect('dashboard_redirect')
    return render(request, 'map/admin_map.html')

@login_required
def user_map(request):
    return render(request, 'map/user_map.html')


# ==================== ADMIN EMERGENCIES MANAGEMENT ====================

@login_required
def admin_emergencies(request):
    if not request.user.is_admin_user():
        return redirect('dashboard_redirect')

    query = EmergencyRequest.objects.all().order_by('-priority_score', '-created_at')

    status_filter = request.GET.get('status')
    if status_filter:
        query = query.filter(status=status_filter)

    priority_filter = request.GET.get('priority')
    if priority_filter:
        query = query.filter(priority_classification=priority_filter)

    district_filter = request.GET.get('district')
    if district_filter:
        query = query.filter(district__icontains=district_filter)

    return render(request, 'admin/emergencies.html', {
        'emergencies': query,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'district_filter': district_filter,
        'STATUS_FLOW': EmergencyRequest.STATUS_FLOW,
        'PRIORITY_LEVELS': EmergencyRequest.PRIORITY_LEVEL_CHOICES,
    })


# ==================== DATABASE RECORDS VIEWER ====================

@login_required
def admin_database_records(request):
    if not request.user.is_admin_user():
        return redirect('dashboard_redirect')

    model_name = request.GET.get('table', 'EmergencyRequest')
    
    records = []
    headers = []
    title = ""

    if model_name == 'User':
        title = "User Accounts (Django Auth & Roles)"
        headers = ['ID', 'Username', 'Role', 'Subtype', 'Full Name', 'Phone', 'District', 'Date Joined']
        users = User.objects.all().order_by('-date_joined')
        for u in users:
            records.append([u.id, u.username, u.get_role_display(), u.get_user_subtype_display(), u.get_full_name(), u.phone, u.district, u.date_joined.strftime('%Y-%m-%d %H:%M')])
    elif model_name == 'GDACSEvent':
        title = "GDACS Live Disaster Events"
        headers = ['ID', 'Type', 'Event Name', 'Country', 'Alert Level', 'Lat', 'Lon', 'India?', 'Tamil Nadu?', 'Date']
        events = GDACSEvent.objects.all().order_by('-event_date')[:50]
        for e in events:
            records.append([e.external_event_id, e.event_type, e.event_name[:35], e.country, e.alert_level, e.latitude, e.longitude, "Yes" if e.is_india else "No", "Yes" if e.is_tamil_nadu else "No", e.event_date.strftime('%Y-%m-%d') if e.event_date else ''])
    elif model_name == 'Donation':
        title = "Relief Donations Pipeline"
        headers = ['Tracking Code', 'Donor', 'Category', 'Item Name', 'Quantity', 'Status', 'Target Region', 'Created']
        dons = Donation.objects.all().order_by('-created_at')
        for d in dons:
            records.append([d.tracking_code, d.donor.username, d.category, d.item_name, f"{d.quantity} {d.unit}", d.status, d.target_region, d.created_at.strftime('%Y-%m-%d %H:%M')])
    elif model_name == 'Resource':
        title = "Resource Inventory Stock"
        headers = ['ID', 'Name', 'Category', 'Available Quantity', 'Storage Location', 'District', 'Last Restocked']
        res = Resource.objects.all().order_by('category')
        for r in res:
            records.append([r.id, r.name, r.get_category_display(), f"{r.quantity_available} {r.unit}", r.storage_location, r.district, r.last_restocked.strftime('%Y-%m-%d %H:%M')])
    elif model_name == 'Hospital':
        title = "Hospital Facilities & Bed Capacities"
        headers = ['ID', 'Hospital Name', 'Type', 'District', 'Available Beds', 'ICU Beds', 'Oxygen (L)', 'Phone']
        hosps = Hospital.objects.all().order_by('name')
        for h in hosps:
            records.append([h.id, h.name, h.hospital_type, h.district, f"{h.available_beds}/{h.total_beds}", h.icu_beds_available, h.oxygen_available_liters, h.phone])
    elif model_name == 'Shelter':
        title = "Emergency Relief Shelters"
        headers = ['ID', 'Shelter Name', 'Manager', 'Phone', 'District', 'Capacity', 'Occupancy', 'Available']
        shelters = Shelter.objects.all().order_by('name')
        for s in shelters:
            records.append([s.id, s.name, s.manager_name, s.phone, s.district, s.total_capacity, s.current_occupancy, s.available_capacity])
    elif model_name == 'Responder':
        title = "Emergency Responders on Duty"
        headers = ['ID', 'Name', 'Type', 'Team Name', 'Status', 'Phone', 'Current Location']
        resps = Responder.objects.all().order_by('name')
        for r in resps:
            records.append([r.id, r.name, r.responder_type, r.team_name, r.status, r.phone, r.current_location_name])
    else: # Default EmergencyRequest
        model_name = 'EmergencyRequest'
        title = "Emergency Requests & Priority Scores"
        headers = ['Tracking Code', 'Type', 'Category', 'Severity', 'Affected', 'District', 'Status', 'Priority (PS)', 'Classification']
        reqs = EmergencyRequest.objects.all().order_by('-priority_score')
        for rq in reqs:
            records.append([rq.tracking_code, rq.get_request_type_display(), rq.category, rq.severity, rq.affected_people, rq.district, rq.status, rq.priority_score, rq.priority_classification])

    return render(request, 'admin/database_records.html', {
        'model_name': model_name,
        'title': title,
        'headers': headers,
        'records': records,
        'count': len(records),
    })

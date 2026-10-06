from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from gdacs_integration.models import GDACSEvent
from emergencies.models import EmergencyRequest
from relief.models import Hospital, Shelter, Responder

@login_required
def api_map_layers(request):
    """
    Returns multi-layer geographical data for RescueGrid Leaflet map:
    - GDACS events (filtered by region: all, india, tamil_nadu)
    - Active Emergency Requests
    - Hospitals (with beds, ICU, oxygen)
    - Shelters (with capacity and occupancy)
    - Responders (with status and team)
    """
    region = request.GET.get('region', 'all') # 'all', 'india', 'tamil_nadu'

    # 1. GDACS Events (Strictly real from live sync)
    gdacs_qs = GDACSEvent.objects.all()
    if region == 'india':
        gdacs_qs = gdacs_qs.filter(is_india=True)
    elif region == 'tamil_nadu':
        gdacs_qs = gdacs_qs.filter(is_tamil_nadu=True)

    gdacs_data = []
    for g in gdacs_qs:
        gdacs_data.append({
            'id': g.external_event_id,
            'name': g.event_name,
            'type': g.event_type,
            'country': g.country,
            'lat': g.latitude,
            'lon': g.longitude,
            'alert_level': g.alert_level,
            'severity': g.severity_level,
            'area': g.affected_area[:180],
            'date': g.event_date.strftime('%Y-%m-%d %H:%M') if g.event_date else '',
            'url': g.details_url,
            'is_india': g.is_india,
            'is_tamil_nadu': g.is_tamil_nadu,
        })

    # 2. Emergency Requests (Filter if Tamil Nadu requested)
    req_qs = EmergencyRequest.objects.exclude(status=EmergencyRequest.STATUS_RESOLVED)
    if region == 'tamil_nadu':
        req_qs = req_qs.filter(state__iexact='Tamil Nadu')

    emergencies_data = []
    for r in req_qs:
        if r.latitude and r.longitude:
            emergencies_data.append({
                'id': r.id,
                'tracking_code': r.tracking_code,
                'type': r.get_request_type_display(),
                'category': r.category,
                'severity': r.severity,
                'affected_people': r.affected_people,
                'lat': r.latitude,
                'lon': r.longitude,
                'address': r.address,
                'district': r.district,
                'status': r.status,
                'priority_score': r.priority_score,
                'priority_classification': r.priority_classification,
                'reported_by': r.reported_by.get_full_name() or r.reported_by.username,
                'created_at': r.created_at.strftime('%Y-%m-%d %H:%M'),
            })

    # 3. Hospitals
    hosp_qs = Hospital.objects.all()
    if region == 'tamil_nadu':
        hosp_qs = hosp_qs.filter(state__iexact='Tamil Nadu')

    hospitals_data = []
    for h in hosp_qs:
        hospitals_data.append({
            'id': h.id,
            'name': h.name,
            'type': h.hospital_type,
            'phone': h.phone,
            'lat': h.latitude,
            'lon': h.longitude,
            'address': h.address,
            'district': h.district,
            'total_beds': h.total_beds,
            'available_beds': h.available_beds,
            'icu_beds': h.icu_beds_available,
            'oxygen': h.oxygen_available_liters,
        })

    # 4. Shelters
    shelter_qs = Shelter.objects.filter(is_active=True)
    if region == 'tamil_nadu':
        shelter_qs = shelter_qs.filter(state__iexact='Tamil Nadu')

    shelters_data = []
    for s in shelter_qs:
        shelters_data.append({
            'id': s.id,
            'name': s.name,
            'manager': s.manager_name,
            'phone': s.phone,
            'lat': s.latitude,
            'lon': s.longitude,
            'address': s.address,
            'district': s.district,
            'total_capacity': s.total_capacity,
            'current_occupancy': s.current_occupancy,
            'available_capacity': s.available_capacity,
        })

    # 5. Responders
    resp_qs = Responder.objects.filter(current_latitude__isnull=False, current_longitude__isnull=False)
    responders_data = []
    for rp in resp_qs:
        responders_data.append({
            'id': rp.id,
            'name': rp.name,
            'team': rp.team_name,
            'type': rp.get_responder_type_display(),
            'phone': rp.phone,
            'lat': rp.current_latitude,
            'lon': rp.current_longitude,
            'status': rp.status,
            'location_name': rp.current_location_name,
        })

    return JsonResponse({
        'region': region,
        'gdacs_events': gdacs_data,
        'emergencies': emergencies_data,
        'hospitals': hospitals_data,
        'shelters': shelters_data,
        'responders': responders_data,
    })

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import GDACSEvent, GDACSSyncLog
from .services import sync_gdacs_events, get_latest_sync_status

@login_required
def gdacs_events_list(request):
    """
    Displays official GDACS disaster feed events.
    Supports filtering by:
    - Region: All Global, India, Tamil Nadu
    - Alert Level: Red, Orange, Green
    - Event Type: EQ, TC, FL, DR, VO, WF
    - Search query
    """
    query = GDACSEvent.objects.all()

    region_filter = request.GET.get('region', 'all')
    if region_filter == 'india':
        query = query.filter(is_india=True)
    elif region_filter == 'tamil_nadu':
        query = query.filter(is_tamil_nadu=True)

    alert_filter = request.GET.get('alert_level')
    if alert_filter:
        query = query.filter(alert_level=alert_filter)

    type_filter = request.GET.get('event_type')
    if type_filter:
        query = query.filter(event_type=type_filter)

    search = request.GET.get('search')
    if search:
        query = query.filter(event_name__icontains=search) | query.filter(country__icontains=search) | query.filter(affected_area__icontains=search)

    paginator = Paginator(query, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    sync_status = get_latest_sync_status()
    sync_logs = GDACSSyncLog.objects.order_by('-sync_time')[:10]

    return render(request, 'admin/gdacs.html', {
        'page_obj': page_obj,
        'region_filter': region_filter,
        'alert_filter': alert_filter,
        'type_filter': type_filter,
        'search': search,
        'sync_status': sync_status,
        'sync_logs': sync_logs,
        'total_count': query.count(),
    })

@login_required
def trigger_gdacs_sync(request):
    """
    Triggers manual GDACS sync.
    Can be called via regular POST or JSON AJAX request.
    """
    if not request.user.is_admin_user():
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'success': False, 'error': 'Admin permissions required'}, status=403)
        messages.error(request, "Only operations administrators can synchronize external feeds.")
        return redirect('admin_gdacs')

    result = sync_gdacs_events()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse(result)

    if result['success']:
        messages.success(request, f"Official GDACS feed synchronized! Synced {result['count']} real global events ({result['india_count']} in India).")
    else:
        messages.error(request, f"GDACS Sync failed: {result['error']}")

    return redirect('admin_gdacs')

def api_gdacs_geojson(request):
    """
    JSON API returning GeoJSON FeatureCollection of actual GDACS events for Leaflet map.
    """
    region = request.GET.get('region', 'all')
    events = GDACSEvent.objects.all()

    if region == 'india':
        events = events.filter(is_india=True)
    elif region == 'tamil_nadu':
        events = events.filter(is_tamil_nadu=True)

    features = []
    for ev in events:
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [ev.longitude, ev.latitude]
            },
            'properties': {
                'id': ev.external_event_id,
                'name': ev.event_name,
                'type': ev.event_type,
                'type_display': ev.get_event_type_display(),
                'country': ev.country,
                'affected_area': ev.affected_area[:200],
                'alert_level': ev.alert_level,
                'severity_level': ev.severity_level,
                'is_india': ev.is_india,
                'is_tamil_nadu': ev.is_tamil_nadu,
                'event_date': ev.event_date.strftime('%Y-%m-%d %H:%M') if ev.event_date else '',
                'url': ev.details_url,
            }
        })

    return JsonResponse({
        'type': 'FeatureCollection',
        'features': features
    })

import math
from django.utils import timezone
from django.db.models import Avg, Min, Max, Count, F
from emergencies.models import EmergencyRequest
from relief.models import Resource, Responder, Hospital, Shelter

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculates great circle distance between two points on Earth in kilometers.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 15.0 # fallback default distance in km

    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)

def compute_request_priority_score(emergency_request):
    """
    Calculates the documented Emergency Priority Score:
    PS = 0.35S + 0.25P + 0.20W + 0.10R + 0.10D
    Classifies into Critical, High, Medium, Low using actual request data.
    """
    # Find nearest available responder or shelter
    nearest_dist = None
    if emergency_request.latitude and emergency_request.longitude:
        # Check active responders
        responders = Responder.objects.filter(status='Available', current_latitude__isnull=False)
        for resp in responders:
            d = calculate_haversine_distance(
                emergency_request.latitude, emergency_request.longitude,
                resp.current_latitude, resp.current_longitude
            )
            if nearest_dist is None or d < nearest_dist:
                nearest_dist = d
        
        # If no responder with coords, check hospitals/shelters
        if nearest_dist is None:
            facilities = list(Hospital.objects.all()) + list(Shelter.objects.filter(is_active=True))
            for fac in facilities:
                d = calculate_haversine_distance(
                    emergency_request.latitude, emergency_request.longitude,
                    fac.latitude, fac.longitude
                )
                if nearest_dist is None or d < nearest_dist:
                    nearest_dist = d

    # Check resource stock for category
    total_stock = None
    matching_res = Resource.objects.filter(category=emergency_request.category).first()
    if matching_res:
        total_stock = matching_res.quantity_available

    score = emergency_request.calculate_priority_score(
        nearest_help_distance_km=nearest_dist,
        total_stock_available=total_stock
    )
    emergency_request.save(update_fields=['priority_score', 'priority_classification', 'score_breakdown'])
    return emergency_request

def compute_fair_resource_allocation(category=None, total_pool_override=None):
    """
    Implements the documented Fair Resource Allocation formula:
    RA_i = [(N_i * D_i * S_i) / Sigma(N_i * D_i * S_i)] * R_t
    
    Where:
    N_i = Quantity needed for request i
    D_i = Distance factor (1 + dist_km / 50.0)
    S_i = Severity factor (1 to 5)
    R_t = Total available resource pool
    """
    # Query active unfulfilled requests
    query = EmergencyRequest.objects.exclude(status=EmergencyRequest.STATUS_RESOLVED)
    if category:
        query = query.filter(category=category)

    active_requests = list(query)
    if not active_requests:
        return {
            'has_requests': False,
            'requests_count': 0,
            'allocations': [],
            'total_resource_pool': 0,
            'sum_weights': 0,
            'message': 'No active unfulfilled requests to allocate resources for.'
        }

    # Determine total resource pool R_t
    if total_pool_override is not None:
        R_t = total_pool_override
    else:
        # Sum from actual inventory
        res_query = Resource.objects.all()
        if category:
            res_query = res_query.filter(category=category)
        R_t = sum(r.quantity_available for r in res_query)
        if R_t <= 0:
            R_t = 100 # default demonstration pool if stock empty

    # Compute individual weights W_i = N_i * D_i * S_i
    weighted_items = []
    total_weight = 0.0

    for req in active_requests:
        N_i = max(1, req.quantity_needed)
        S_i = max(1, req.severity)
        
        # Distance factor D_i
        dist_km = 10.0
        if req.score_breakdown and 'D' in req.score_breakdown:
            dist_km = req.score_breakdown['D'] * 5.0
        D_i = max(1.0, 1.0 + (dist_km / 50.0))

        weight = N_i * D_i * S_i
        total_weight += weight
        weighted_items.append({
            'request': req,
            'N_i': N_i,
            'D_i': round(D_i, 2),
            'S_i': S_i,
            'weight': round(weight, 3),
        })

    # Calculate allocated share for each request
    allocations = []
    for item in weighted_items:
        if total_weight > 0:
            share_ratio = item['weight'] / total_weight
            ra_i = round(share_ratio * R_t, 1)
        else:
            share_ratio = 0
            ra_i = 0

        allocations.append({
            'request_id': item['request'].id,
            'tracking_code': item['request'].tracking_code,
            'category': item['request'].category,
            'district': item['request'].district,
            'severity': item['request'].severity,
            'needed_quantity': item['N_i'],
            'unit': item['request'].unit,
            'distance_factor': item['D_i'],
            'severity_factor': item['S_i'],
            'weight': item['weight'],
            'share_pct': round(share_ratio * 100, 1),
            'allocated_units': ra_i,
            'priority_classification': item['request'].priority_classification,
        })

    return {
        'has_requests': True,
        'requests_count': len(active_requests),
        'allocations': allocations,
        'total_resource_pool': R_t,
        'sum_weights': round(total_weight, 3),
        'message': f'Allocated across {len(active_requests)} requests using documented RA formula.'
    }

def get_response_time_analytics():
    """
    Computes documented Response Time:
    Response Time = Resolved Time - Reported Time
    If there are no resolved records, display:
    'No response-time data available yet'
    """
    resolved_requests = EmergencyRequest.objects.filter(
        status=EmergencyRequest.STATUS_RESOLVED,
        resolved_at__isnull=False
    ).exclude(response_time_minutes__isnull=True)

    count = resolved_requests.count()
    if count == 0:
        return {
            'has_data': False,
            'message': 'No response-time data available yet',
            'count': 0,
            'avg_minutes': None,
            'avg_hours': None,
            'min_minutes': None,
            'max_minutes': None,
            'resolved_list': []
        }

    agg = resolved_requests.aggregate(
        avg_time=Avg('response_time_minutes'),
        min_time=Min('response_time_minutes'),
        max_time=Max('response_time_minutes'),
    )

    avg_m = round(agg['avg_time'] or 0.0, 1)
    min_m = round(agg['min_time'] or 0.0, 1)
    max_m = round(agg['max_time'] or 0.0, 1)

    return {
        'has_data': True,
        'count': count,
        'avg_minutes': avg_m,
        'avg_hours': round(avg_m / 60.0, 2),
        'min_minutes': min_m,
        'max_minutes': max_m,
        'resolved_list': list(resolved_requests.order_by('-resolved_at')[:10])
    }

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import EmergencyRequest
from analytics_app.algorithms import compute_request_priority_score
from notifications_app.models import Notification
from relief.models import Responder, Resource

@login_required
def request_help(request):
    """
    Creates an emergency, resource, shelter or medical request.
    Supports:
    - Type: EMERGENCY, RESOURCE, SHELTER, MEDICAL
    - Category
    - Quantity & Unit
    - Severity (1-5)
    - Affected people
    - Description
    - GPS / Manual location (Latitude, Longitude, Address, District)
    """
    if request.method == 'POST':
        request_type = request.POST.get('request_type', EmergencyRequest.TYPE_EMERGENCY)
        category = request.POST.get('category', '').strip() or "General Emergency Aid"
        quantity_needed = int(request.POST.get('quantity_needed', 1) or 1)
        unit = request.POST.get('unit', 'persons / units').strip()
        severity = int(request.POST.get('severity', 3))
        affected_people = int(request.POST.get('affected_people', 1) or 1)
        description = request.POST.get('description', '').strip()
        address = request.POST.get('address', '').strip() or "Location not specified"
        district = request.POST.get('district', 'Chennai').strip()
        state = request.POST.get('state', 'Tamil Nadu').strip()

        lat_val = request.POST.get('latitude')
        lon_val = request.POST.get('longitude')
        lat = float(lat_val) if lat_val else 13.0827
        lon = float(lon_val) if lon_val else 80.2707

        # Create request in Pending status
        req_obj = EmergencyRequest.objects.create(
            reported_by=request.user,
            request_type=request_type,
            category=category,
            quantity_needed=quantity_needed,
            unit=unit,
            severity=severity,
            affected_people=affected_people,
            description=description,
            latitude=lat,
            longitude=lon,
            address=address,
            district=district,
            state=state,
            status=EmergencyRequest.STATUS_PENDING,
        )

        # Compute priority score
        compute_request_priority_score(req_obj)

        # Notify user
        Notification.objects.create(
            recipient=request.user,
            title=f"Request Submitted: {req_obj.tracking_code}",
            message=f"Your {req_obj.get_request_type_display()} request has been logged and queued with priority {req_obj.priority_classification}.",
            notification_type=Notification.TYPE_STATUS_UPDATE,
            link_url=f"/emergencies/track/{req_obj.tracking_code}/"
        )

        messages.success(request, f"Emergency request {req_obj.tracking_code} submitted successfully. Assigned Priority: {req_obj.priority_classification} (Score: {req_obj.priority_score}).")
        return redirect('my_requests')

    # Pre-fill user location if known
    user_lat = request.user.latitude or 13.0827
    user_lon = request.user.longitude or 80.2707
    user_district = request.user.district or "Chennai"
    user_address = request.user.address or ""

    return render(request, 'emergencies/request_help.html', {
        'user_lat': user_lat,
        'user_lon': user_lon,
        'user_district': user_district,
        'user_address': user_address,
    })

@login_required
def my_requests(request):
    """
    Lists the current user's requests with priority, status timeline, and filters.
    """
    user_reqs = EmergencyRequest.objects.filter(reported_by=request.user).order_by('-created_at')
    
    # Status filter
    status_filter = request.GET.get('status')
    if status_filter:
        user_reqs = user_reqs.filter(status=status_filter)

    return render(request, 'emergencies/my_requests.html', {
        'requests': user_reqs,
        'status_filter': status_filter,
    })

@login_required
def request_detail(request, tracking_code):
    req_obj = get_object_or_404(EmergencyRequest, tracking_code=tracking_code)
    
    # Permission check: owner or admin
    if req_obj.reported_by != request.user and not request.user.is_admin_user():
        messages.error(request, "You do not have permission to view this request.")
        return redirect('dashboard_redirect')

    available_responders = Responder.objects.filter(status='Available') if request.user.is_admin_user() else []

    return render(request, 'emergencies/request_detail.html', {
        'req': req_obj,
        'available_responders': available_responders,
    })

@login_required
def update_request_status(request, tracking_code):
    """
    Admin action to transition status:
    Pending -> Verified -> Assigned -> Responding -> Resolved
    Calculates Response Time = Resolved Time - Reported Time on resolution.
    """
    if not request.user.is_admin_user():
        messages.error(request, "Unauthorized. Only administrators can update emergency statuses.")
        return redirect('dashboard_redirect')

    req_obj = get_object_or_404(EmergencyRequest, tracking_code=tracking_code)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        responder_id = request.POST.get('responder_id')

        if new_status in [s[0] for s in EmergencyRequest.STATUS_FLOW]:
            req_obj.status = new_status
            now = timezone.now()

            if new_status == EmergencyRequest.STATUS_VERIFIED and not req_obj.verified_at:
                req_obj.verified_at = now
            elif new_status == EmergencyRequest.STATUS_ASSIGNED and not req_obj.assigned_at:
                req_obj.assigned_at = now
            elif new_status == EmergencyRequest.STATUS_RESPONDING and not req_obj.responding_at:
                req_obj.responding_at = now
            elif new_status == EmergencyRequest.STATUS_RESOLVED:
                req_obj.resolved_at = now
                if req_obj.created_at:
                    delta = now - req_obj.created_at
                    req_obj.response_time_minutes = round(delta.total_seconds() / 60.0, 2)

            if responder_id:
                try:
                    responder = Responder.objects.get(id=responder_id)
                    req_obj.assigned_responder = responder
                    responder.status = 'Deployed'
                    responder.save()
                    if req_obj.status == EmergencyRequest.STATUS_PENDING:
                        req_obj.status = EmergencyRequest.STATUS_ASSIGNED
                        req_obj.assigned_at = now
                except Responder.DoesNotExist:
                    pass

            req_obj.save()

            # Re-compute priority score with fresh state
            compute_request_priority_score(req_obj)

            # Notify reporter
            Notification.objects.create(
                recipient=req_obj.reported_by,
                title=f"Status Updated: {req_obj.tracking_code}",
                message=f"Your emergency request is now marked as '{req_obj.status}'.",
                notification_type=Notification.TYPE_STATUS_UPDATE,
                link_url=f"/emergencies/track/{req_obj.tracking_code}/"
            )

            messages.success(request, f"Request {req_obj.tracking_code} updated to '{new_status}'.")

    return redirect('request_detail', tracking_code=tracking_code)

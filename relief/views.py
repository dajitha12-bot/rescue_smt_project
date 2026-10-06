from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q
from .models import Donation, Resource, Hospital, Shelter, Responder
from emergencies.models import EmergencyRequest
from notifications_app.models import Notification

# ==================== DONOR VIEWS ====================

@login_required
def donor_dashboard(request):
    if request.user.role != 'DONOR' and not request.user.is_admin_user():
        return redirect('dashboard_redirect')

    user_donations = Donation.objects.filter(donor=request.user)

    # Strictly calculated statistics from real database records (no fake data)
    total_donations_count = user_donations.count()
    verified_count = user_donations.filter(status__in=[Donation.STATUS_VERIFIED, Donation.STATUS_RECEIVED, Donation.STATUS_ALLOCATED, Donation.STATUS_DELIVERED]).count()
    delivered_count = user_donations.filter(status=Donation.STATUS_DELIVERED).count()
    total_items_delivered = user_donations.filter(status=Donation.STATUS_DELIVERED).aggregate(s=Sum('quantity'))['s'] or 0

    # Relief Need Summary: Actual active unfulfilled requests in DB
    active_needs = EmergencyRequest.objects.exclude(status=EmergencyRequest.STATUS_RESOLVED).order_by('-priority_score')[:6]

    recent_donations = user_donations.order_by('-created_at')[:8]

    return render(request, 'donor/dashboard.html', {
        'total_donations_count': total_donations_count,
        'verified_count': verified_count,
        'delivered_count': delivered_count,
        'total_items_delivered': total_items_delivered,
        'active_needs': active_needs,
        'recent_donations': recent_donations,
    })

@login_required
def donor_needs(request):
    """
    Displays actual relief needs from verified or pending emergency requests.
    """
    needs = EmergencyRequest.objects.exclude(status=EmergencyRequest.STATUS_RESOLVED).order_by('-priority_score')
    
    # Filter by category
    category_filter = request.GET.get('category')
    if category_filter:
        needs = needs.filter(category__icontains=category_filter)

    return render(request, 'donor/needs.html', {
        'needs': needs,
        'category_filter': category_filter,
    })

@login_required
def donor_donate(request):
    """
    Form to pledge/donate relief items.
    """
    prefill_request_id = request.GET.get('request_id')
    prefill_request = None
    if prefill_request_id:
        prefill_request = EmergencyRequest.objects.filter(id=prefill_request_id).first()

    if request.method == 'POST':
        category = request.POST.get('category', 'FOOD')
        item_name = request.POST.get('item_name', '').strip()
        quantity = int(request.POST.get('quantity', 1) or 1)
        unit = request.POST.get('unit', 'units').strip()
        target_region = request.POST.get('target_region', 'Tamil Nadu - General Relief').strip()
        pickup_location = request.POST.get('pickup_location', '').strip()
        notes = request.POST.get('notes', '').strip()
        req_id = request.POST.get('allocated_to_request_id')

        allocated_request = None
        if req_id:
            allocated_request = EmergencyRequest.objects.filter(id=req_id).first()

        donation = Donation.objects.create(
            donor=request.user,
            category=category,
            item_name=item_name,
            quantity=quantity,
            unit=unit,
            target_region=target_region,
            pickup_location=pickup_location,
            notes=notes,
            allocated_to_request=allocated_request,
            status=Donation.STATUS_SUBMITTED
        )

        # Notify donor
        Notification.objects.create(
            recipient=request.user,
            title=f"Donation Pledged: {donation.tracking_code}",
            message=f"Thank you! Your donation of {quantity} {unit} of {item_name} has been submitted for ops verification.",
            notification_type=Notification.TYPE_DONATION,
            link_url="/relief/donor/my-donations/"
        )

        messages.success(request, f"Donation {donation.tracking_code} submitted successfully. Our logistics operations will verify shortly.")
        return redirect('donor_my_donations')

    return render(request, 'donor/donate.html', {
        'categories': Resource.RESOURCE_CATEGORIES,
        'prefill_request': prefill_request,
    })

@login_required
def donor_my_donations(request):
    donations = Donation.objects.filter(donor=request.user).order_by('-created_at')
    return render(request, 'donor/my_donations.html', {
        'donations': donations,
    })


# ==================== USER FACILITY VIEWS ====================

@login_required
def user_hospitals(request):
    hospitals = Hospital.objects.all().order_by('-available_beds')
    
    district_filter = request.GET.get('district')
    if district_filter:
        hospitals = hospitals.filter(district__icontains=district_filter)

    return render(request, 'relief/hospitals.html', {
        'hospitals': hospitals,
        'district_filter': district_filter,
    })

@login_required
def user_shelters(request):
    shelters = Shelter.objects.filter(is_active=True).order_by('-total_capacity')

    district_filter = request.GET.get('district')
    if district_filter:
        shelters = shelters.filter(district__icontains=district_filter)

    return render(request, 'relief/shelters.html', {
        'shelters': shelters,
        'district_filter': district_filter,
    })


# ==================== ADMIN OPERATIONS VIEWS ====================

@login_required
def admin_donations(request):
    if not request.user.is_admin_user():
        messages.error(request, "Admin access required.")
        return redirect('dashboard_redirect')

    donations = Donation.objects.all().order_by('-created_at')
    status_filter = request.GET.get('status')
    if status_filter:
        donations = donations.filter(status=status_filter)

    return render(request, 'admin/donations.html', {
        'donations': donations,
        'status_filter': status_filter,
        'STATUS_CHOICES': Donation.STATUS_CHOICES,
    })

@login_required
def admin_update_donation_status(request, tracking_code):
    if not request.user.is_admin_user():
        messages.error(request, "Admin access required.")
        return redirect('dashboard_redirect')

    donation = get_object_or_404(Donation, tracking_code=tracking_code)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in [s[0] for s in Donation.STATUS_CHOICES]:
            donation.status = new_status
            now = timezone.now()
            if new_status == Donation.STATUS_VERIFIED:
                donation.verified_at = now
            elif new_status == Donation.STATUS_RECEIVED:
                donation.received_at = now
                # Automatically add to resource inventory
                res, _ = Resource.objects.get_or_create(
                    name=donation.item_name,
                    category=donation.category,
                    defaults={'unit': donation.unit, 'storage_location': 'Central Relief Depot'}
                )
                res.quantity_available += donation.quantity
                res.save()
            elif new_status == Donation.STATUS_ALLOCATED:
                donation.allocated_at = now
            elif new_status == Donation.STATUS_DELIVERED:
                donation.delivered_at = now

            donation.save()

            # Notify donor
            Notification.objects.create(
                recipient=donation.donor,
                title=f"Donation Status: {donation.tracking_code}",
                message=f"Your donation of {donation.item_name} has moved to '{new_status}'.",
                notification_type=Notification.TYPE_DONATION,
                link_url="/relief/donor/my-donations/"
            )

            messages.success(request, f"Donation {donation.tracking_code} status updated to {new_status}.")

    return redirect('admin_donations')

@login_required
def admin_resources(request):
    if not request.user.is_admin_user():
        messages.error(request, "Admin access required.")
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            name = request.POST.get('name', '').strip()
            category = request.POST.get('category', 'FOOD')
            quantity = int(request.POST.get('quantity', 0) or 0)
            unit = request.POST.get('unit', 'units').strip()
            storage_location = request.POST.get('storage_location', '').strip()
            district = request.POST.get('district', 'Chennai').strip()

            Resource.objects.create(
                name=name,
                category=category,
                quantity_available=quantity,
                unit=unit,
                storage_location=storage_location,
                district=district,
                latitude=13.0827,
                longitude=80.2707,
            )
            messages.success(request, f"Resource item '{name}' added to inventory.")
        elif action == 'restock':
            resource_id = request.POST.get('resource_id')
            add_qty = int(request.POST.get('add_quantity', 0) or 0)
            res = get_object_or_404(Resource, id=resource_id)
            res.quantity_available += add_qty
            res.save()
            messages.success(request, f"Restocked {res.name} by +{add_qty} {res.unit}.")

        return redirect('admin_resources')

    resources = Resource.objects.all().order_by('category', 'name')
    return render(request, 'admin/resources.html', {
        'resources': resources,
        'categories': Resource.RESOURCE_CATEGORIES,
    })

@login_required
def admin_facilities(request):
    if not request.user.is_admin_user():
        messages.error(request, "Admin access required.")
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        facility_type = request.POST.get('facility_type')
        if facility_type == 'hospital':
            name = request.POST.get('name', '').strip()
            hospital_type = request.POST.get('hospital_type', 'District General')
            phone = request.POST.get('phone', '').strip()
            address = request.POST.get('address', '').strip()
            district = request.POST.get('district', 'Chennai').strip()
            lat = float(request.POST.get('latitude', 13.0827) or 13.0827)
            lon = float(request.POST.get('longitude', 80.2707) or 80.2707)
            total_beds = int(request.POST.get('total_beds', 50) or 50)
            available_beds = int(request.POST.get('available_beds', 10) or 10)
            icu_beds = int(request.POST.get('icu_beds', 2) or 2)
            oxygen = int(request.POST.get('oxygen', 200) or 200)

            Hospital.objects.create(
                name=name,
                hospital_type=hospital_type,
                phone=phone,
                address=address,
                district=district,
                latitude=lat,
                longitude=lon,
                total_beds=total_beds,
                available_beds=available_beds,
                icu_beds_available=icu_beds,
                oxygen_available_liters=oxygen
            )
            messages.success(request, f"Hospital '{name}' registered.")

        elif facility_type == 'shelter':
            name = request.POST.get('name', '').strip()
            manager_name = request.POST.get('manager_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            address = request.POST.get('address', '').strip()
            district = request.POST.get('district', 'Chennai').strip()
            lat = float(request.POST.get('latitude', 13.0827) or 13.0827)
            lon = float(request.POST.get('longitude', 80.2707) or 80.2707)
            capacity = int(request.POST.get('total_capacity', 150) or 150)
            facilities_description = request.POST.get('facilities_description', '').strip()

            Shelter.objects.create(
                name=name,
                manager_name=manager_name,
                phone=phone,
                address=address,
                district=district,
                latitude=lat,
                longitude=lon,
                total_capacity=capacity,
                current_occupancy=0,
                facilities_description=facilities_description
            )
            messages.success(request, f"Shelter '{name}' registered.")

        return redirect('admin_facilities')

    hospitals = Hospital.objects.all().order_by('-available_beds')
    shelters = Shelter.objects.all().order_by('-total_capacity')

    return render(request, 'admin/facilities.html', {
        'hospitals': hospitals,
        'shelters': shelters,
    })

@login_required
def admin_responders(request):
    if not request.user.is_admin_user():
        messages.error(request, "Admin access required.")
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            name = request.POST.get('name', '').strip()
            responder_type = request.POST.get('responder_type', 'SDRF')
            team_name = request.POST.get('team_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            location = request.POST.get('location_name', 'Command Base').strip()
            lat = float(request.POST.get('latitude', 13.0827) or 13.0827)
            lon = float(request.POST.get('longitude', 80.2707) or 80.2707)

            Responder.objects.create(
                name=name,
                responder_type=responder_type,
                team_name=team_name,
                phone=phone,
                current_location_name=location,
                current_latitude=lat,
                current_longitude=lon,
                status='Available'
            )
            messages.success(request, f"Responder '{name}' registered on duty.")
        elif action == 'update_status':
            resp_id = request.POST.get('responder_id')
            new_status = request.POST.get('status')
            resp = get_object_or_404(Responder, id=resp_id)
            resp.status = new_status
            resp.save()
            messages.success(request, f"Responder '{resp.name}' status set to {new_status}.")

        return redirect('admin_responders')

    responders = Responder.objects.all().order_by('name')
    return render(request, 'admin/responders.html', {
        'responders': responders,
        'RESPONDER_TYPES': Responder.RESPONDER_TYPES,
        'STATUS_CHOICES': Responder.STATUS_CHOICES,
    })

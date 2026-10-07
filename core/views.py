from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User
from emergencies.models import EmergencyRequest
from relief.models import Hospital

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    # Auto-seed database if no users exist (Vercel serverless cold-start safety)
    if User.objects.count() == 0:
        try:
            from django.core.management import call_command
            call_command('seed_data', interactive=False)
        except Exception as exc:
            print(f"Auto seed error: {exc}")

    if request.method == 'POST':
        # Quick login demonstration shortcuts
        demo_user = request.POST.get('demo_user')
        if demo_user:
            user = User.objects.filter(username=demo_user).first()
            if not user:
                try:
                    from django.core.management import call_command
                    call_command('seed_data', interactive=False)
                    user = User.objects.filter(username=demo_user).first()
                except Exception as exc:
                    print(f"Demo user seed error: {exc}")

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

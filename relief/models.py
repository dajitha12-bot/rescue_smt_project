import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

class Hospital(models.Model):
    name = models.CharField(max_length=200)
    hospital_type = models.CharField(max_length=100, default='District Emergency Center')
    contact_person = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    address = models.TextField()
    district = models.CharField(max_length=100, default='Chennai')
    state = models.CharField(max_length=100, default='Tamil Nadu')
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    total_beds = models.IntegerField(default=100)
    available_beds = models.IntegerField(default=20)
    icu_beds_available = models.IntegerField(default=5)
    oxygen_available_liters = models.IntegerField(default=500)
    blood_units_available = models.IntegerField(default=30)
    ambulances_available = models.IntegerField(default=2)
    is_emergency_ready = models.BooleanField(default=True)
    
    associated_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='hospital_facilities'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.district}, {self.state})"


class Shelter(models.Model):
    name = models.CharField(max_length=200)
    manager_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    address = models.TextField()
    district = models.CharField(max_length=100, default='Chennai')
    state = models.CharField(max_length=100, default='Tamil Nadu')
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    total_capacity = models.IntegerField(default=200)
    current_occupancy = models.IntegerField(default=0)
    facilities_description = models.TextField(blank=True, help_text="e.g. Clean drinking water, food distribution, medical first aid counter, power backup")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    @property
    def available_capacity(self):
        return max(0, self.total_capacity - self.current_occupancy)

    def __str__(self):
        return f"{self.name} ({self.current_occupancy}/{self.total_capacity} capacity)"


class Responder(models.Model):
    RESPONDER_TYPES = [
        ('NDRF', 'NDRF (National Disaster Response Force)'),
        ('SDRF', 'SDRF (State Disaster Response Force)'),
        ('FIRE_RESCUE', 'Tamil Nadu Fire & Rescue Services'),
        ('POLICE', 'Police Emergency Unit'),
        ('MEDICAL_EMS', '108 Emergency Medical Services'),
        ('VOLUNTEER', 'Trained Civil Defense Volunteer Group'),
    ]

    STATUS_CHOICES = [
        ('Available', 'Available on Standby'),
        ('Deployed', 'Deployed to Incident'),
        ('Off Duty', 'Off Duty'),
    ]

    name = models.CharField(max_length=150)
    responder_type = models.CharField(max_length=30, choices=RESPONDER_TYPES, default='SDRF')
    team_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30)
    current_latitude = models.FloatField(null=True, blank=True)
    current_longitude = models.FloatField(null=True, blank=True)
    current_location_name = models.CharField(max_length=150, blank=True, default='Command Base')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Available', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.team_name} [{self.status}]"


class Resource(models.Model):
    RESOURCE_CATEGORIES = [
        ('FOOD', 'Food & Ration Kits'),
        ('WATER', 'Drinking Water & Purification'),
        ('MEDICAL', 'Medical Aid & First Aid Supplies'),
        ('SHELTER_SUPPLIES', 'Tents & Tarpaulins'),
        ('EQUIPMENT', 'Rescue Boats & Life Jackets'),
        ('CLOTHING', 'Blankets & Emergency Clothing'),
    ]

    name = models.CharField(max_length=150)
    category = models.CharField(max_length=30, choices=RESOURCE_CATEGORIES, db_index=True)
    quantity_available = models.IntegerField(default=0)
    unit = models.CharField(max_length=30, default='units')
    storage_location = models.CharField(max_length=200)
    district = models.CharField(max_length=100, default='Chennai')
    state = models.CharField(max_length=100, default='Tamil Nadu')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    last_restocked = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.quantity_available} {self.unit}) @ {self.storage_location}"


class Donation(models.Model):
    STATUS_SUBMITTED = 'Submitted'
    STATUS_VERIFIED = 'Verified'
    STATUS_RECEIVED = 'Received'
    STATUS_ALLOCATED = 'Allocated'
    STATUS_DELIVERED = 'Delivered'

    STATUS_CHOICES = [
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_VERIFIED, 'Verified'),
        (STATUS_RECEIVED, 'Received'),
        (STATUS_ALLOCATED, 'Allocated'),
        (STATUS_DELIVERED, 'Delivered'),
    ]

    tracking_code = models.CharField(max_length=30, unique=True, db_index=True)
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='donations', on_delete=models.CASCADE)
    category = models.CharField(max_length=30, choices=Resource.RESOURCE_CATEGORIES, db_index=True)
    item_name = models.CharField(max_length=150)
    quantity = models.IntegerField(default=1)
    unit = models.CharField(max_length=30, default='units')
    target_region = models.CharField(max_length=150, blank=True, default='General Relief / All Regions')
    pickup_location = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUBMITTED, db_index=True)
    
    # Optional link to specific emergency request if allocated
    allocated_to_request = models.ForeignKey(
        'emergencies.EmergencyRequest',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='allocated_donations'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    allocated_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            short_id = uuid.uuid4().hex[:6].upper()
            year = timezone.now().year
            self.tracking_code = f"DON-{year}-{short_id}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tracking_code}: {self.item_name} ({self.quantity} {self.unit}) - {self.status}"

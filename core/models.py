from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_ADMIN = 'ADMIN'
    ROLE_USER = 'USER'
    ROLE_DONOR = 'DONOR'
    
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin / Operations Coordinator'),
        (ROLE_USER, 'Affected Person / Hospital User'),
        (ROLE_DONOR, 'Relief Donor / Sponsor'),
    ]

    SUBTYPE_AFFECTED_PERSON = 'AFFECTED_PERSON'
    SUBTYPE_HOSPITAL = 'HOSPITAL'
    SUBTYPE_DONOR_INDIVIDUAL = 'DONOR_INDIVIDUAL'
    SUBTYPE_DONOR_ORG = 'DONOR_ORG'

    SUBTYPE_CHOICES = [
        (SUBTYPE_AFFECTED_PERSON, 'Affected Person / Citizen'),
        (SUBTYPE_HOSPITAL, 'Hospital / Medical Center User'),
        (SUBTYPE_DONOR_INDIVIDUAL, 'Individual Donor'),
        (SUBTYPE_DONOR_ORG, 'Relief Organization / NGO'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_USER, db_index=True)
    user_subtype = models.CharField(max_length=30, choices=SUBTYPE_CHOICES, default=SUBTYPE_AFFECTED_PERSON)
    phone = models.CharField(max_length=20, blank=True)
    organization_name = models.CharField(max_length=150, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True, default='Chennai')
    state = models.CharField(max_length=100, default='Tamil Nadu')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def is_admin_user(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser or self.is_staff

    def is_donor_user(self):
        return self.role == self.ROLE_DONOR

    def is_hospital_subtype(self):
        return self.user_subtype == self.SUBTYPE_HOSPITAL

    def get_role_display_badge(self):
        if self.is_admin_user():
            return "Operations Administrator"
        elif self.role == self.ROLE_DONOR:
            return "Relief Donor"
        elif self.is_hospital_subtype():
            return "Hospital Facility User"
        return "Affected Citizen / User"

    def __str__(self):
        display_name = self.get_full_name() or self.username
        if self.organization_name:
            return f"{display_name} ({self.organization_name})"
        return f"{display_name} [{self.get_role_display()}]"

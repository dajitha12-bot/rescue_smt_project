import math
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

class EmergencyRequest(models.Model):
    TYPE_EMERGENCY = 'EMERGENCY'
    TYPE_RESOURCE = 'RESOURCE'
    TYPE_SHELTER = 'SHELTER'
    TYPE_MEDICAL = 'MEDICAL'

    REQUEST_TYPES = [
        (TYPE_EMERGENCY, 'Life Safety & Evacuation'),
        (TYPE_RESOURCE, 'Food, Water & Relief Supplies'),
        (TYPE_SHELTER, 'Emergency Shelter Placement'),
        (TYPE_MEDICAL, 'Urgent Medical Aid & Hospitalization'),
    ]

    STATUS_PENDING = 'Pending'
    STATUS_VERIFIED = 'Verified'
    STATUS_ASSIGNED = 'Assigned'
    STATUS_RESPONDING = 'Responding'
    STATUS_RESOLVED = 'Resolved'

    STATUS_FLOW = [
        (STATUS_PENDING, 'Pending Verification'),
        (STATUS_VERIFIED, 'Verified by Ops'),
        (STATUS_ASSIGNED, 'Assigned to Responder'),
        (STATUS_RESPONDING, 'Responder Responding'),
        (STATUS_RESOLVED, 'Resolved & Closed'),
    ]

    SEVERITY_CHOICES = [
        (1, '1 - Low (Non-life threatening, minor assistance)'),
        (2, '2 - Medium (Moderate disruption, stable conditions)'),
        (3, '3 - High (Severe disruption, urgent supplies needed)'),
        (4, '4 - Critical (Immediate hazard, vulnerable individuals)'),
        (5, '5 - Catastrophic (Life-threatening emergency, trapped victims)'),
    ]

    PRIORITY_LEVEL_CHOICES = [
        ('Low', 'Low Priority'),
        ('Medium', 'Medium Priority'),
        ('High', 'High Priority'),
        ('Critical', 'Critical Priority'),
    ]

    tracking_code = models.CharField(max_length=30, unique=True, db_index=True)
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='emergency_requests', on_delete=models.CASCADE)
    
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES, default=TYPE_EMERGENCY, db_index=True)
    category = models.CharField(max_length=120)
    quantity_needed = models.IntegerField(default=1)
    unit = models.CharField(max_length=30, default='persons / units')
    severity = models.IntegerField(choices=SEVERITY_CHOICES, default=3, db_index=True)
    affected_people = models.IntegerField(default=1)
    description = models.TextField()

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    address = models.TextField()
    district = models.CharField(max_length=100, default='Chennai', blank=True)
    state = models.CharField(max_length=100, default='Tamil Nadu')

    status = models.CharField(max_length=20, choices=STATUS_FLOW, default=STATUS_PENDING, db_index=True)

    # Documented Priority Score: PS = 0.35S + 0.25P + 0.20W + 0.10R + 0.10D
    priority_score = models.FloatField(default=0.0, db_index=True)
    priority_classification = models.CharField(max_length=20, choices=PRIORITY_LEVEL_CHOICES, default='Medium', db_index=True)
    score_breakdown = models.JSONField(default=dict, blank=True)

    assigned_responder = models.ForeignKey(
        'relief.Responder',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_emergencies'
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    responding_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    response_time_minutes = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['-priority_score', '-created_at']

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            short_id = uuid.uuid4().hex[:6].upper()
            year = timezone.now().year
            self.tracking_code = f"REQ-{year}-{short_id}"
            
        # If transitioning to resolved, calculate response time
        if self.status == self.STATUS_RESOLVED and not self.resolved_at:
            self.resolved_at = timezone.now()
            
        if self.resolved_at and self.created_at:
            delta = self.resolved_at - self.created_at
            self.response_time_minutes = round(delta.total_seconds() / 60.0, 2)

        super().save(*args, **kwargs)

    def calculate_priority_score(self, nearest_help_distance_km=None, total_stock_available=None):
        """
        Documented Emergency Priority Score:
        PS = 0.35S + 0.25P + 0.20W + 0.10R + 0.10D
        Where:
        S = Severity (scaled 1-10: 1->2.0, 2->4.0, 3->6.0, 4->8.0, 5->10.0)
        P = Affected People (scaled 0-10: 1->1.0, 2-5->3.0, 6-20->5.0, 21-50->8.0, >50->10.0)
        W = Waiting Time (scaled 0-10 based on elapsed hours: min(10.0, hours_waiting / 2.4))
        R = Resource Shortage (scaled 0-10 based on unmet demand vs available stock)
        D = Distance from Available Help (scaled 0-10 based on isolation: min(10.0, dist_km / 10.0))
        """
        # S: Severity
        S_raw = self.severity
        S_val = min(10.0, S_raw * 2.0)

        # P: Affected People
        p_count = self.affected_people
        if p_count <= 1:
            P_val = 1.0
        elif p_count <= 5:
            P_val = 3.0
        elif p_count <= 20:
            P_val = 5.5
        elif p_count <= 50:
            P_val = 8.0
        else:
            P_val = 10.0

        # W: Waiting Time
        if self.created_at:
            elapsed_hours = (timezone.now() - self.created_at).total_seconds() / 3600.0
        else:
            elapsed_hours = 0.0
        W_val = min(10.0, elapsed_hours / 2.4)

        # R: Resource Shortage
        if total_stock_available is not None:
            if total_stock_available <= 0:
                R_val = 10.0
            elif total_stock_available < self.quantity_needed:
                shortage_ratio = 1.0 - (total_stock_available / max(1, self.quantity_needed))
                R_val = min(10.0, shortage_ratio * 10.0)
            else:
                R_val = 2.0
        else:
            # Scaled by quantity needed if stock not specified
            R_val = min(10.0, max(1.0, (self.quantity_needed / 20.0) * 5.0))

        # D: Distance from Available Help (km)
        if nearest_help_distance_km is not None:
            D_val = min(10.0, nearest_help_distance_km / 5.0)
        else:
            # Default moderate distance factor
            D_val = 3.0

        # Formula: PS = 0.35S + 0.25P + 0.20W + 0.10R + 0.10D
        ps = (0.35 * S_val) + (0.25 * P_val) + (0.20 * W_val) + (0.10 * R_val) + (0.10 * D_val)
        ps_rounded = round(ps, 2)

        # Classification
        if ps_rounded >= 7.5:
            classification = 'Critical'
        elif ps_rounded >= 5.5:
            classification = 'High'
        elif ps_rounded >= 3.5:
            classification = 'Medium'
        else:
            classification = 'Low'

        self.priority_score = ps_rounded
        self.priority_classification = classification
        self.score_breakdown = {
            'S': round(S_val, 2),
            'P': round(P_val, 2),
            'W': round(W_val, 2),
            'R': round(R_val, 2),
            'D': round(D_val, 2),
            'weighted_S': round(0.35 * S_val, 2),
            'weighted_P': round(0.25 * P_val, 2),
            'weighted_W': round(0.20 * W_val, 2),
            'weighted_R': round(0.10 * R_val, 2),
            'weighted_D': round(0.10 * D_val, 2),
            'total_PS': ps_rounded,
            'classification': classification,
        }
        return ps_rounded

    def __str__(self):
        return f"{self.tracking_code} [{self.priority_classification}] {self.category} - {self.status}"

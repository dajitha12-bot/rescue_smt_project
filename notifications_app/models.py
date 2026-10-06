from django.db import models
from django.conf import settings

class Notification(models.Model):
    TYPE_EMERGENCY = 'EMERGENCY'
    TYPE_STATUS_UPDATE = 'STATUS_UPDATE'
    TYPE_DONATION = 'DONATION'
    TYPE_GDACS = 'GDACS'
    TYPE_SYSTEM = 'SYSTEM'

    TYPE_CHOICES = [
        (TYPE_EMERGENCY, 'Emergency Alert'),
        (TYPE_STATUS_UPDATE, 'Request Status Update'),
        (TYPE_DONATION, 'Donation Pipeline'),
        (TYPE_GDACS, 'GDACS Regional Hazard'),
        (TYPE_SYSTEM, 'Operations Announcement'),
    ]

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notifications', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default=TYPE_SYSTEM)
    is_read = models.BooleanField(default=False, db_index=True)
    link_url = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"To {self.recipient.username}: {self.title} ({'Read' if self.is_read else 'Unread'})"

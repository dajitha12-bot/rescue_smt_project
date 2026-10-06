from django.db import models

class GDACSEvent(models.Model):
    ALERT_GREEN = 'Green'
    ALERT_ORANGE = 'Orange'
    ALERT_RED = 'Red'

    ALERT_LEVEL_CHOICES = [
        (ALERT_GREEN, 'Green - Minor Impact'),
        (ALERT_ORANGE, 'Orange - Moderate Impact'),
        (ALERT_RED, 'Red - Severe / Catastrophic Impact'),
    ]

    EVENT_TYPE_CHOICES = [
        ('EQ', 'Earthquake'),
        ('TC', 'Tropical Cyclone'),
        ('FL', 'Flood'),
        ('DR', 'Drought'),
        ('VO', 'Volcano'),
        ('WF', 'Wildfire'),
        ('TS', 'Tsunami'),
        ('OTHER', 'Other Disaster'),
    ]

    external_event_id = models.CharField(max_length=100, unique=True, db_index=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, db_index=True)
    event_name = models.CharField(max_length=255)
    country = models.CharField(max_length=100, blank=True)
    iso3 = models.CharField(max_length=10, blank=True)
    affected_area = models.TextField(blank=True)
    severity_level = models.CharField(max_length=150, blank=True)
    alert_level = models.CharField(max_length=20, choices=ALERT_LEVEL_CHOICES, default=ALERT_GREEN, db_index=True)
    alert_score = models.FloatField(default=1.0)
    latitude = models.FloatField()
    longitude = models.FloatField()
    event_date = models.DateTimeField(null=True, blank=True)
    source_updated_at = models.DateTimeField(null=True, blank=True)
    details_url = models.URLField(max_length=500, blank=True)
    
    # Geographic classification strictly evaluated by real coordinates and official metadata
    is_india = models.BooleanField(default=False, db_index=True)
    is_tamil_nadu = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-event_date', '-source_updated_at', '-created_at']
        verbose_name = 'GDACS Event'
        verbose_name_plural = 'GDACS Events'

    def __str__(self):
        return f"[{self.event_type}] {self.event_name} - {self.country} ({self.alert_level})"

    def save(self, *args, **kwargs):
        # Strict geographic classification based on actual coordinates and country name
        # India bounding box approx: Lat 6.0 to 37.5 N, Lon 68.0 to 97.5 E
        is_coord_india = (6.0 <= self.latitude <= 37.5) and (68.0 <= self.longitude <= 97.5)
        is_name_india = ('india' in self.country.lower()) or (self.iso3.upper() == 'IND') or ('india' in self.event_name.lower())
        self.is_india = is_coord_india or is_name_india

        # Tamil Nadu bounding box: Lat 8.08 to 13.55 N, Lon 76.24 to 80.35 E
        is_coord_tn = (8.08 <= self.latitude <= 13.55) and (76.24 <= self.longitude <= 80.35)
        is_text_tn = ('tamil nadu' in self.country.lower()) or ('tamil nadu' in self.affected_area.lower()) or ('tamil nadu' in self.event_name.lower())
        self.is_tamil_nadu = is_coord_tn or is_text_tn

        super().save(*args, **kwargs)


class GDACSSyncLog(models.Model):
    STATUS_SUCCESS = 'SUCCESS'
    STATUS_FAILED = 'FAILED'

    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED, 'Failed'),
    ]

    sync_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, db_index=True)
    events_synced = models.IntegerField(default=0)
    india_events_count = models.IntegerField(default=0)
    tamil_nadu_events_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-sync_time']
        verbose_name = 'GDACS Sync Log'
        verbose_name_plural = 'GDACS Sync Logs'

    def __str__(self):
        return f"Sync {self.sync_time.strftime('%Y-%m-%d %H:%M:%S')} - {self.status} ({self.events_synced} events)"

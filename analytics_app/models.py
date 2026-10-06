from django.db import models

class OperationsMetricSnapshot(models.Model):
    snapshot_time = models.DateTimeField(auto_now_add=True)
    total_active_emergencies = models.IntegerField(default=0)
    pending_emergencies = models.IntegerField(default=0)
    resolved_emergencies = models.IntegerField(default=0)
    avg_response_time_minutes = models.FloatField(null=True, blank=True)
    total_donations_value = models.IntegerField(default=0)
    shelter_utilization_pct = models.FloatField(default=0.0)
    hospital_bed_occupancy_pct = models.FloatField(default=0.0)

    class Meta:
        ordering = ['-snapshot_time']

    def __str__(self):
        return f"Snapshot @ {self.snapshot_time.strftime('%Y-%m-%d %H:%M')}"

from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    ACTION_CHOICES = (
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
    )

    SEVERITY_CHOICES = (
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
        ("CRITICAL", "Critical"),
    )

    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default="LOW",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    clinic = models.ForeignKey(
        "clinics.Clinic",
        on_delete=models.CASCADE
    )

    action = models.CharField(max_length=10, choices=ACTION_CHOICES)

    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=50)

    before_data = models.JSONField(null=True, blank=True)
    after_data = models.JSONField(null=True, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.model_name} - {self.action}"
    

class Meta:
    ordering = ["-timestamp"]
    indexes = [
        models.Index(fields=["model_name"]),
        models.Index(fields=["action"]),
        models.Index(fields=["timestamp"]),
        models.Index(fields=["clinic"]),
    ]    
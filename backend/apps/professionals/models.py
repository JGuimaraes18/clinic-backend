from django.db import models
from django.db.models import UniqueConstraint
from apps.core.models import BaseModel


class Professional(BaseModel):

    clinic = models.ForeignKey(
        "clinics.Clinic",
        on_delete=models.CASCADE,
        related_name="professionals"
    )

    full_name = models.CharField(max_length=255)

    phone = models.CharField(max_length=20, blank=True, null=True)

    email = models.EmailField(blank=True, null=True)

    registration_type = models.CharField(max_length=50)

    registration_number = models.CharField(max_length=50)

    specialty = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["clinic", "registration_type", "registration_number"],
                name="unique_registration_per_clinic"
            )
        ]

    def __str__(self):
        return f"{self.full_name} ({self.registration_type})"
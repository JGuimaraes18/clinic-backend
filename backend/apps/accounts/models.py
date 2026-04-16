from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    clinic = models.ForeignKey(
        "clinics.Clinic",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('professional', 'Professional'),
        ('staff', 'Staff'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
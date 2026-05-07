from django.db import models
from django.db.models import UniqueConstraint
from apps.core.models import BaseModel
from apps.accounts.models import Membership


class Professional(BaseModel):

    membership = models.OneToOneField(
        Membership,
        on_delete=models.CASCADE,
        related_name="professional_profile"
    )

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
                fields=["membership", "registration_type", "registration_number"],
                name="unique_registration_per_membership"
            )
        ]

    def __str__(self):
        return f"{self.membership.user.get_full_name()} ({self.registration_type})"
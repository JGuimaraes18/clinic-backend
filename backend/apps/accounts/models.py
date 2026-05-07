from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Usuário global do sistema.
    Não pertence diretamente a nenhuma clínica.
    """
    def __str__(self):
        return self.username


class Membership(models.Model):
    ROLE_CHOICES = (
        ("ADMIN", "Admin"),
        ("PROFESSIONAL", "Professional"),
        ("ATTENDANT", "Attendant"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="memberships"
    )

    clinic = models.ForeignKey(
        "clinics.Clinic",
        on_delete=models.CASCADE,
        related_name="memberships"
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "clinic"],
                name="unique_user_clinic"
            )
        ]
        indexes = [
            models.Index(fields=["clinic"]),
            models.Index(fields=["user"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.clinic.name} ({self.get_role_display()})"
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("O usuário deve possuir um email")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    force_password_change = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    def __str__(self):
        return self.email


class UserSettings(models.Model):
    THEME_CHOICES = (
        ("light", "Light"),
        ("dark", "Dark"),
        ("system", "System"),
    )
    DENSITY_CHOICES = (
        ("comfortable", "Comfortable"),
        ("compact", "Compact"),
    )
    FONT_SIZE_CHOICES = (
        ("small", "Small"),
        ("medium", "Medium"),
        ("large", "Large"),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="settings")
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default="system")
    primary_color = models.CharField(max_length=20, blank=True, null=True, default="#0651ED")
    density = models.CharField(max_length=20, choices=DENSITY_CHOICES, default="comfortable")
    font_size = models.CharField(max_length=20, choices=FONT_SIZE_CHOICES, default="medium")
    extra_preferences = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Settings: {self.user.email}"


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
        return f"{self.user.email} - {self.clinic.name} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        # Validar regra: administrador pertence a apenas uma clínica ativa
        if self.role == "ADMIN" and self.is_active:
            existing = Membership.objects.filter(user=self.user, is_active=True).exclude(clinic=self.clinic)
            if existing.exists():
                raise ValidationError("Um administrador de clínica não pode estar associado a outra clínica.")
        
        # Validar se o usuário já é ADMIN em alguma clínica ativa
        existing_admin = Membership.objects.filter(user=self.user, role="ADMIN", is_active=True)
        if self.pk:
            existing_admin = existing_admin.exclude(pk=self.pk)
        if existing_admin.exists() and self.clinic != existing_admin.first().clinic:
            raise ValidationError("Este usuário já é administrador de outra clínica.")
            
        super().save(*args, **kwargs)


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_reset_tokens")
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)
    
    def is_valid(self):
        # 24 hours expiration
        expiration_time = self.created_at + timezone.timedelta(hours=24)
        return not self.used and timezone.now() <= expiration_time
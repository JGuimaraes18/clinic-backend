import hashlib
import hmac

from django.db import models
from apps.core.models import BaseModel
from apps.core.fields import EncryptedTextField
from django.conf import settings

class Patient(BaseModel):
    clinic = models.ForeignKey("clinics.Clinic", on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    cpf = EncryptedTextField(null=True, blank=True)
    cpf_hash = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    document = EncryptedTextField(null=True, blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["clinic", "cpf_hash"],
                name="unique_cpf_per_clinic"
            )
        ]

    def save(self, *args, **kwargs):
        if self.cpf:
            self.cpf_hash = self.generate_cpf_hash(self.cpf)
        super().save(*args, **kwargs)

    def generate_cpf_hash(self, cpf_value):
        return hmac.new(
            settings.SECRET_KEY.encode(),
            cpf_value.encode(),
            hashlib.sha256
        ).hexdigest()

    def __str__(self):
        return self.full_name
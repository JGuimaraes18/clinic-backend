from django.db import models
from apps.core.models import BaseModel
from apps.core.fields import EncryptedTextField

class Patient(BaseModel):
    clinic = models.ForeignKey("clinics.Clinic", on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    cpf = EncryptedTextField(null=True, blank=True)
    document = EncryptedTextField(null=True, blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.full_name
from django.conf import settings
from django.db import models
from apps.core.models import BaseModel


class Atendimento(BaseModel):

    STATUS_CHOICES = [
        ("AGENDADO", "Agendado"),
        ("EM_ATENDIMENTO", "Em Atendimento"),
        ("REALIZADO", "Realizado"),
        ("CANCELADO", "Cancelado"),
    ]

    clinic = models.ForeignKey(
        "clinics.Clinic",
        on_delete=models.CASCADE,
        related_name="atendimentos",
    )

    paciente = models.ForeignKey(
        "patients.Patient",
        on_delete=models.PROTECT,
        related_name="atendimentos"
    )

    profissional = models.ForeignKey(
        "professionals.Professional",
        on_delete=models.PROTECT,
        related_name="atendimentos",
        null=True,
        blank=True
    )

    data_hora = models.DateTimeField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="AGENDADO"
    )

    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.paciente.nome} - {self.data_hora}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
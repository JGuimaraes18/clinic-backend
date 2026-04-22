from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import BaseModel


class Atendimento(BaseModel):

    STATUS_CHOICES = [
        ("AGENDADO", "Agendado"),
        ("REALIZADO", "Realizado"),
        ("CANCELADO", "Cancelado"),
    ]

    clinic = models.ForeignKey(
        "clinics.Clinic",
        on_delete=models.CASCADE,
        related_name="appointments",
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
        if self.pk:
            original = Atendimento.objects.only("status").get(pk=self.pk)

            if (
                original.status != "REALIZADO"
                and self.status == "REALIZADO"
            ):
                try:
                    prontuario = self.prontuario
                except Atendimento.prontuario.RelatedObjectDoesNotExist:
                    raise ValidationError(
                        "Não é possível finalizar atendimento sem prontuário."
                    )

                if not prontuario.conteudo or not prontuario.conteudo.strip():
                    raise ValidationError(
                        "Prontuário está vazio. Preencha antes de finalizar."
                    )

        super().save(*args, **kwargs)
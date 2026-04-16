from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError


class Atendimento(models.Model):

    STATUS_CHOICES = [
        ("AGENDADO", "Agendado"),
        ("REALIZADO", "Realizado"),
        ("CANCELADO", "Cancelado"),
    ]

    paciente = models.ForeignKey(
        "patients.Patient",
        on_delete=models.PROTECT,
        related_name="atendimentos"
    )

    dentista = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="atendimentos_realizados"
    )

    data_hora = models.DateTimeField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="AGENDADO"
    )

    observacoes = models.TextField(blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)

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
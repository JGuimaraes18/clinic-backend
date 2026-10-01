from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import hashlib


class Prontuario(models.Model):

    STATUS_CHOICES = [
        ("RASCUNHO", "Rascunho"),
        ("FECHADO", "Fechado"),
    ]

    hash_integridade = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        editable=False
    )

    atendimento = models.OneToOneField(
        "appointments.Atendimento",
        on_delete=models.PROTECT,
        related_name="prontuario"
    )

    conteudo = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="RASCUNHO"
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    finalizado_em = models.DateTimeField(
        null=True,
        blank=True
    )

    finalizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="prontuarios_finalizados"
    )

    def fechar(self, user):
        if self.status == "FECHADO":
            raise ValidationError("Prontuário já está fechado.")

        if not self.conteudo or not self.conteudo.strip():
            raise ValidationError("Não é possível fechar prontuário vazio.")

        # Gera hash SHA256 do conteúdo
        hash_obj = hashlib.sha256(self.conteudo.encode("utf-8"))
        self.hash_integridade = hash_obj.hexdigest()

        self.status = "FECHADO"
        self.finalizado_em = timezone.now()
        self.finalizado_por = user

        super().save()

    def save(self, *args, **kwargs):
        if self.pk:
            original = Prontuario.objects.only(
                "status", "hash_integridade"
            ).get(pk=self.pk)

            if original.status == "FECHADO":
                raise ValidationError(
                    "Prontuário fechado não pode ser alterado."
                )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Prontuário #{self.id}"
    

class AdendoProntuario(models.Model):

    prontuario = models.ForeignKey(
        Prontuario,
        on_delete=models.PROTECT,
        related_name="adendos"
    )

    conteudo = models.TextField()

    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Adendo #{self.id} - Prontuário {self.prontuario.id}"    
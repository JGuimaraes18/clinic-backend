from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Atendimento
from apps.medical_records.models import Prontuario


@receiver(post_save, sender=Atendimento)
def criar_prontuario_automatico(sender, instance, created, **kwargs):
    
    if instance.status == "REALIZADO":
        
        if not hasattr(instance, "prontuario"):
            Prontuario.objects.create(
                atendimento=instance,
                conteudo=""
            )
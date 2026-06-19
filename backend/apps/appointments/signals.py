from django.db.models.signals import post_save
from django.dispatch import receiver

from core.middleware import get_current_user, get_current_ip
from apps.audit.services import log_audit_event
from .models import Atendimento


@receiver(post_save, sender=Atendimento)
def audit_appointment_save(sender, instance, created, **kwargs):
    actor = get_current_user()
    ip = get_current_ip()

    if not actor or not actor.is_authenticated:
        return

    action = "CREATE" if created else "UPDATE"

    log_audit_event(
        user=actor,
        clinic=instance.clinic,
        action=action,
        model_name="Atendimento",
        object_id=str(instance.pk),
        after_data={
            "paciente": instance.paciente.full_name,
            "profissional": (
                instance.profissional.user.get_full_name()
                if instance.profissional
                else None
            ),
            "data_hora": str(instance.data_hora),
            "status": instance.status,
        },
        ip_address=ip,
    )

from django.db.models.signals import post_save
from django.dispatch import receiver

from core.middleware import get_current_user, get_current_ip
from apps.audit.services import log_audit_event
from .models import Patient


@receiver(post_save, sender=Patient)
def audit_patient_save(sender, instance, created, **kwargs):
    actor = get_current_user()
    ip = get_current_ip()

    if not actor or not actor.is_authenticated:
        return

    action = "CREATE" if created else "UPDATE"

    log_audit_event(
        user=actor,
        clinic=instance.clinic,
        action=action,
        model_name="Patient",
        object_id=str(instance.pk),
        after_data={
            "full_name": instance.full_name,
            "email": instance.email,
            "phone": instance.phone,
            "is_deleted": instance.is_deleted,
        },
        ip_address=ip,
    )

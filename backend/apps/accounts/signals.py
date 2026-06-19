from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from core.middleware import get_current_user, get_current_ip
from apps.audit.services import log_audit_event
from .models import Membership

User = get_user_model()


@receiver(post_save, sender=User)
def audit_user_save(sender, instance, created, **kwargs):
    actor = get_current_user()
    ip = get_current_ip()

    if not actor or not actor.is_authenticated:
        return

    action = "CREATE" if created else "UPDATE"

    log_audit_event(
        user=actor,
        clinic=None,  # Usuário é global, sem clínica
        action=action,
        model_name="User",
        object_id=str(instance.pk),
        after_data={
            "email": instance.email,
            "first_name": instance.first_name,
            "last_name": instance.last_name,
            "is_active": instance.is_active,
        },
        ip_address=ip,
    )


@receiver(post_save, sender=Membership)
def audit_membership_save(sender, instance, created, **kwargs):
    actor = get_current_user()
    ip = get_current_ip()

    if not actor or not actor.is_authenticated:
        return

    action = "CREATE" if created else "UPDATE"

    log_audit_event(
        user=actor,
        clinic=instance.clinic,
        action=action,
        model_name="Membership",
        object_id=str(instance.pk),
        after_data={
            "user_email": instance.user.email,
            "clinic": instance.clinic.name,
            "role": instance.role,
            "is_active": instance.is_active,
        },
        ip_address=ip,
    )


@receiver(post_delete, sender=Membership)
def audit_membership_delete(sender, instance, **kwargs):
    actor = get_current_user()
    ip = get_current_ip()

    if not actor or not actor.is_authenticated:
        return

    log_audit_event(
        user=actor,
        clinic=instance.clinic,
        action="DELETE",
        model_name="Membership",
        object_id=str(instance.pk),
        before_data={
            "user_email": instance.user.email,
            "clinic": instance.clinic.name,
            "role": instance.role,
        },
        ip_address=ip,
    )

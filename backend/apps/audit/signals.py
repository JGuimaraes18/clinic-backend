from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from django.db import models
import datetime
import decimal
import uuid

from .models import AuditLog
from .redaction import sanitize_snapshot
from core.middleware import get_current_ip, get_current_user


ALLOWED_APPS = [
    "patients",
    "appointments",
    "medical_records",
    "clinics",
    "accounts",
]

# Apps que NÃO devem ser auditadas
EXCLUDED_APPS = [
    "admin",
    "contenttypes",
    "sessions",
    "auth",
    "audit", 
]


from django.db.models.fields.files import FieldFile

def serialize_value(value):
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()

    if isinstance(value, decimal.Decimal):
        return float(value)

    if isinstance(value, uuid.UUID):
        return str(value)
        
    if isinstance(value, FieldFile):
        return value.name if value else None

    return value


def model_to_dict_safe(instance):
    data = {}

    for field in instance._meta.fields:
        value = getattr(instance, field.name)

        # 🔐 Se for ForeignKey → salva apenas o ID
        if isinstance(field, models.ForeignKey):
            data[field.name] = value.pk if value else None
            continue

        # 🔐 Se for OneToOne → salva ID
        if isinstance(field, models.OneToOneField):
            data[field.name] = value.pk if value else None
            continue

        data[field.name] = serialize_value(value)

    return data

def get_severity(model_name, action):
    if model_name in ["Prontuario"]:
        return "CRITICAL"

    if model_name in ["Patient", "Atendimento"]:
        return "HIGH"

    if action == "DELETE":
        return "HIGH"

    return "LOW"


def should_audit(sender, instance):
    if sender._meta.app_label not in ALLOWED_APPS:
        return

    # Não auditar o próprio AuditLog
    if isinstance(instance, AuditLog):
        return False

    # Ignorar apps internas
    if sender._meta.app_label in EXCLUDED_APPS:
        return False

    return True


def resolve_clinic(instance):
    """
    Deriva a clinica do evento auditado.

    Patient/Atendimento possuem `clinic` proprio; Prontuario e
    AdendoProntuario nao, entao a clinica e derivada do Atendimento.
    """
    clinic = getattr(instance, "clinic", None)
    if clinic is not None:
        return clinic

    atendimento = getattr(instance, "atendimento", None)
    if atendimento is None:
        atendimento = getattr(getattr(instance, "prontuario", None), "atendimento", None)

    if atendimento is None:
        return None

    return getattr(atendimento, "clinic", None)


# 🔎 Captura estado anterior antes de salvar
@receiver(pre_save)
def capture_old_data(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_instance = sender.objects.get(pk=instance.pk)
        instance._old_data = model_to_dict_safe(old_instance)
    except sender.DoesNotExist:
        instance._old_data = None


# 💾 CREATE / UPDATE
@receiver(post_save)
def log_create_update(sender, instance, created, **kwargs):
    if not should_audit(sender, instance):
        return
    
    severity=get_severity(sender.__name__, "CREATE" if created else "UPDATE")

    user = get_current_user()
    clinic = resolve_clinic(instance)
    # Camada 1: payload saneado ANTES de chegar ao banco.
    after_data = sanitize_snapshot(sender.__name__, model_to_dict_safe(instance))
    before_data = sanitize_snapshot(sender.__name__, getattr(instance, "_old_data", None))

    ip_address = get_current_ip()

    # Se for UPDATE, salvar apenas campos alterados
    if not created and before_data:
        changed_fields = {}

        for field, old_value in before_data.items():
            new_value = after_data.get(field) if after_data else None

            if old_value != new_value:
                changed_fields[field] = {
                    "before": old_value,
                    "after": new_value,
                }

        if not changed_fields:
            return

        before_data = changed_fields
        after_data = None  

    AuditLog.objects.create(
        user=user if user and user.is_authenticated else None,
        clinic=clinic,
        action="CREATE" if created else "UPDATE",
        model_name=sender.__name__,
        object_id=str(instance.pk),
        before_data=None if created else before_data,
        after_data=after_data if created else None,
        severity=severity,
        ip_address=ip_address,
    )


# 🗑 DELETE
@receiver(pre_delete)
def log_delete(sender, instance, **kwargs):
    if not should_audit(sender, instance):
        return

    severity=get_severity(sender.__name__, "DELETE")

    user = get_current_user()
    clinic = resolve_clinic(instance)

    # Camada 1: payload saneado ANTES de chegar ao banco.
    before_data = sanitize_snapshot(sender.__name__, model_to_dict_safe(instance))

    AuditLog.objects.create(
        user=user if user and user.is_authenticated else None,
        clinic=clinic,
        action="DELETE",
        model_name=sender.__name__,
        object_id=str(instance.pk),
        before_data=before_data,
        after_data=None,
        severity=severity,
        ip_address=get_current_ip(),
    )
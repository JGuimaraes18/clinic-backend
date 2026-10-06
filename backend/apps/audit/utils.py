from .models import AuditLog
from .redaction import sanitize_snapshot


def log_audit_event(
    *,
    user,
    clinic,
    action,
    model_name,
    object_id,
    before_data=None,
    after_data=None,
    ip_address=None,
):
    AuditLog.objects.create(
        user=user,
        clinic=clinic,
        action=action,
        model_name=model_name,
        object_id=str(object_id),
        before_data=sanitize_snapshot(model_name, before_data),
        after_data=sanitize_snapshot(model_name, after_data),
        ip_address=ip_address,
    )
from rest_framework import viewsets
from apps.audit.utils import log_audit_event


class ClinicSafeModelViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return super().get_queryset().filter(
            clinic=self.request.user.clinic
        )

    def perform_create(self, serializer):
        instance = serializer.save(clinic=self.request.user.clinic)

        log_audit_event(
            user=self.request.user,
            clinic=self.request.user.clinic,
            action="CREATE",
            model_name=instance.__class__.__name__,
            object_id=instance.pk,
            after_data=serializer.data,
            ip_address=self.request.META.get("REMOTE_ADDR"),
        )

    def perform_update(self, serializer):
        instance = self.get_object()
        before_data = self.get_serializer(instance).data

        instance = serializer.save()

        log_audit_event(
            user=self.request.user,
            clinic=self.request.user.clinic,
            action="UPDATE",
            model_name=instance.__class__.__name__,
            object_id=instance.pk,
            before_data=before_data,
            after_data=serializer.data,
            ip_address=self.request.META.get("REMOTE_ADDR"),
        )

    def perform_destroy(self, instance):
        before_data = self.get_serializer(instance).data

        log_audit_event(
            user=self.request.user,
            clinic=self.request.user.clinic,
            action="DELETE",
            model_name=instance.__class__.__name__,
            object_id=instance.pk,
            before_data=before_data,
            ip_address=self.request.META.get("REMOTE_ADDR"),
        )

        instance.delete()


from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from apps.clinics.permissions import IsSuperUser
from .models import AuditLog
from .serializers import AuditLogSerializer

class AuditLogViewSet(ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    # Superuser only, declarado como politica (antes so existia implicito
    # na exception de get_queryset). Mesmo resultado, agora explicito.
    permission_classes = [IsAuthenticated, IsSuperUser]

    def get_queryset(self):
        if not self.request.user.is_superuser:
            raise PermissionDenied("Apenas SuperAdmins podem visualizar os logs de auditoria.")
        return AuditLog.objects.all().select_related("user", "clinic")
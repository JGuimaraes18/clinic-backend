from rest_framework import viewsets
from apps.audit.services import log_audit_event


class ClinicSafeModelViewSet(viewsets.ModelViewSet):
    """
    ViewSet base para garantir isolamento por clínica (multi-tenant),
    suporte a soft delete e auditoria automática.
    """

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        model = queryset.model

        if user.is_superuser:
            if hasattr(model, "is_deleted"):
                return queryset.filter(is_deleted=False)
            return queryset

        if hasattr(model, "clinic"):
            filters = {"clinic": user.clinic}

            if hasattr(model, "is_deleted"):
                filters["is_deleted"] = False

            return queryset.filter(**filters)

        if hasattr(model, "atendimento"):
            filters = {"atendimento__clinic": user.clinic}

            if hasattr(model, "is_deleted"):
                filters["is_deleted"] = False

            return queryset.filter(**filters)

        return queryset.none()

    def perform_create(self, serializer):
        model = serializer.Meta.model

        if hasattr(model, "clinic"):
            serializer.save(clinic=self.request.user.clinic)
        else:
            serializer.save()

    def perform_destroy(self, instance):
        before_data = self.get_serializer(instance).data

        if hasattr(instance, "is_deleted"):
            instance.is_deleted = True
            instance.save()
        else:
            instance.delete()

        log_audit_event(
            user=self.request.user,
            clinic=getattr(self.request.user, "clinic", None),
            action="DELETE",
            model_name=instance.__class__.__name__,
            object_id=str(instance.pk),
            before_data=before_data,
            ip_address=self.get_client_ip(),
        )

    def get_client_ip(self):
        x_forwarded_for = self.request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return self.request.META.get("REMOTE_ADDR")
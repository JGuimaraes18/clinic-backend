from rest_framework import viewsets
from apps.audit.services import log_audit_event


class ClinicSafeModelViewSet(viewsets.ModelViewSet):
    """
    ViewSet base para garantir isolamento por clínica (multi-tenant),
    suporte a soft delete e auditoria automática.
    """

    # 🔎 Sempre filtra por clínica e remove registros deletados
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        # Futuro suporte para superadmin global
        if getattr(user, "role", None) == "superadmin":
            if hasattr(queryset.model, "is_deleted"):
                return queryset.filter(is_deleted=False)
            return queryset

        # Regra padrão: usuário só enxerga dados da própria clínica
        filters = {"clinic": user.clinic}

        if hasattr(queryset.model, "is_deleted"):
            filters["is_deleted"] = False

        return queryset.filter(**filters)

    # 🏥 Garante que o clinic nunca venha do frontend
    def perform_create(self, serializer):
        serializer.save(clinic=self.request.user.clinic)

    # 🗑 Soft delete + auditoria
    def perform_destroy(self, instance):
        before_data = self.get_serializer(instance).data

        if hasattr(instance, "is_deleted"):
            instance.is_deleted = True
            instance.save()
        else:
            instance.delete()

        log_audit_event(
            user=self.request.user,
            clinic=self.request.user.clinic,
            action="DELETE",
            model_name=instance.__class__.__name__,
            object_id=str(instance.pk),
            before_data=before_data,
            ip_address=self.get_client_ip(),
        )

    # 🌍 Captura IP corretamente mesmo com proxy (nginx, cloudflare etc)
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return self.request.META.get("REMOTE_ADDR")
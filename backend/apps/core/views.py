from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from apps.accounts.models import Membership
from apps.audit.services import log_audit_event


class ClinicSafeModelViewSet(viewsets.ModelViewSet):
    """
    ViewSet base que filtra automaticamente por clínica ativa.
    Usa clinic_id do token JWT para isolar os dados.
    """

    def get_user_clinic_id(self):
        """Retorna o clinic_id do token JWT do usuário autenticado."""
        user = self.request.user

        clinic_id = self.request.auth.get("clinic_id") if self.request.auth else None

        if user.is_superuser and not clinic_id:
            return None

        if not clinic_id:
            raise PermissionDenied("Usuário não possui clínica ativa no token.")

        return clinic_id

    def get_user_clinic(self):
        """Retorna o objeto Clinic (para compatibilidade / auditoria)."""
        from apps.clinics.models import Clinic

        clinic_id = self.get_user_clinic_id()

        if clinic_id is None:
            return None

        try:
            return Clinic.objects.get(id=clinic_id)
        except Clinic.DoesNotExist:
            raise PermissionDenied("Clínica não encontrada.")

    def get_queryset(self):
        queryset = super().get_queryset()
        model = queryset.model
        user = self.request.user

        # Superuser vê tudo
        if user.is_superuser:
            if hasattr(model, "is_deleted"):
                return queryset.filter(is_deleted=False)
            return queryset

        clinic_id = self.get_user_clinic_id()

        # Modelo possui campo clinic direto
        if hasattr(model, "clinic"):
            filters = {"clinic_id": clinic_id}

            if hasattr(model, "is_deleted"):
                filters["is_deleted"] = False

            return queryset.filter(**filters)

        # Modelo possui relacionamento via atendimento
        if hasattr(model, "atendimento"):
            filters = {"atendimento__clinic_id": clinic_id}

            if hasattr(model, "is_deleted"):
                filters["is_deleted"] = False

            return queryset.filter(**filters)

        # Se o modelo NÃO tem clinic nem atendimento,
        # retorna normalmente (ex: tabelas globais)
        if hasattr(model, "is_deleted"):
            return queryset.filter(is_deleted=False)

        return queryset

    def perform_create(self, serializer):
        model = serializer.Meta.model
        clinic = self.get_user_clinic()

        if hasattr(model, "clinic"):
            if not clinic:
                raise PermissionDenied("Superusuário deve ter uma clínica no token para criar este registro (faça login na clínica).")
            serializer.save(clinic=clinic)
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
            clinic=self.get_user_clinic() if not self.request.user.is_superuser else None,
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
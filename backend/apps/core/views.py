from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from apps.accounts.models import Membership
from apps.audit.services import log_audit_event


class ClinicSafeModelViewSet(viewsets.ModelViewSet):

    def get_user_clinic(self):
        user = self.request.user

        if user.is_superuser:
            return None

        membership = Membership.objects.filter(
            user=user,
            is_active=True
        ).first()

        if not membership:
            raise PermissionDenied("Usuário não possui clínica ativa.")

        return membership.clinic

    def get_queryset(self):
        queryset = super().get_queryset()
        model = queryset.model

        user = self.request.user

        if user.is_superuser:
            if hasattr(model, "is_deleted"):
                return queryset.filter(is_deleted=False)
            return queryset

        clinic = self.get_user_clinic()

        if hasattr(model, "clinic"):
            filters = {"clinic": clinic}

            if hasattr(model, "is_deleted"):
                filters["is_deleted"] = False

            return queryset.filter(**filters)

        if hasattr(model, "atendimento"):
            filters = {"atendimento__clinic": clinic}

            if hasattr(model, "is_deleted"):
                filters["is_deleted"] = False

            return queryset.filter(**filters)

        return queryset.none()


    def perform_create(self, serializer):
        model = serializer.Meta.model

        if self.request.user.is_superuser:
            serializer.save()
            return

        clinic = self.get_user_clinic()

        if hasattr(model, "clinic"):
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
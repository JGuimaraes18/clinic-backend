from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from apps.accounts.models import Membership
from .models import Clinic
from .serializers import ClinicSerializer


class ClinicViewSet(ModelViewSet):
    serializer_class = ClinicSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return Clinic.objects.all()

        membership = Membership.objects.filter(
            user=user,
            role="ADMIN",
            is_active=True
        ).first()

        if membership:
            return Clinic.objects.filter(id=membership.clinic.id)

        return Clinic.objects.none()

    def perform_create(self, serializer):
        if not self.request.user.is_superuser:
            raise PermissionDenied("Você não tem permissão para criar clínicas.")
        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user

        if user.is_superuser:
            serializer.save()
            return

        membership = Membership.objects.filter(
            user=user,
            role="ADMIN",
            is_active=True
        ).first()

        if membership and serializer.instance.id == membership.clinic.id:
            serializer.save()
            return

        raise PermissionDenied("Você não pode editar essa clínica.")

    def perform_destroy(self, instance):
        if not self.request.user.is_superuser:
            raise PermissionDenied("Você não pode excluir clínicas.")

        instance.delete()
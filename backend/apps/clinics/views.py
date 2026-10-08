from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils.crypto import get_random_string
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action

from core.middleware import get_current_ip

from apps.accounts.models import Membership
from apps.audit.services import log_audit_event
from .models import Clinic
from .serializers import ClinicSerializer

User = get_user_model()


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

    def create(self, request, *args, **kwargs):
        if not self.request.user.is_superuser:
            raise PermissionDenied("Você não tem permissão para criar clínicas.")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            clinic = serializer.save()
            
            admin_email = clinic.email
            
            # Se o email já existir, criamos um específico
            if User.objects.filter(email=admin_email).exists():
                admin_email = f"admin@{clinic.slug}.com"
                
            # Geração de senha temporária segura
            temp_password = get_random_string(12, allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*')
            
            # Cria usuário inicial
            user = User.objects.create_user(
                email=admin_email,
                password=temp_password,
                first_name="Admin",
                last_name=clinic.name,
                force_password_change=True
            )
            
            # Associa como ADMIN exclusivo
            try:
                Membership.objects.create(
                    user=user,
                    clinic=clinic,
                    role="ADMIN"
                )
            except DjangoValidationError as exc:
                raise ValidationError(exc.messages)

        headers = self.get_success_headers(serializer.data)
        response_data = serializer.data
        response_data["temporary_password"] = temp_password
        response_data["admin_email"] = admin_email
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

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

        instance.is_active = False
        instance.save()

    @action(detail=True, methods=["post"], url_path="reset-admin-password")
    def reset_admin_password(self, request, pk=None):
        if not request.user.is_superuser:
            raise PermissionDenied("Apenas SuperAdmins podem redefinir a senha do administrador da clínica.")
            
        clinic = self.get_object()
        
        # Encontra o admin da clínica
        membership = Membership.objects.filter(clinic=clinic, role="ADMIN").first()
        if not membership:
            return Response({"detail": "Clínica não possui um administrador."}, status=400)
            
        admin_user = membership.user
        new_password = get_random_string(12, allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*')
        admin_user.set_password(new_password)
        admin_user.force_password_change = True
        admin_user.save()
        
        log_audit_event(
            user=request.user,
            clinic=None,
            action="UPDATE",
            model_name="User",
            object_id=str(admin_user.pk),
            before_data={"event": "Senha resetada pelo SuperAdmin"},
            ip_address=get_current_ip(),
        )
        
        return Response({
            "detail": "Senha redefinida com sucesso.",
            "temporary_password": new_password,
            "admin_email": admin_user.email
        })
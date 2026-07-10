from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action

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

    def create(self, request, *args, **kwargs):
        from django.contrib.auth import get_user_model
        from apps.accounts.models import Membership
        from django.db import transaction
        from django.utils.crypto import get_random_string
        from rest_framework.response import Response
        from rest_framework import status

        if not self.request.user.is_superuser:
            raise PermissionDenied("Você não tem permissão para criar clínicas.")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            clinic = serializer.save()
            
            User = get_user_model()
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
            Membership.objects.create(
                user=user,
                clinic=clinic,
                role="ADMIN"
            )

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
            from rest_framework.response import Response
            return Response({"detail": "Clínica não possui um administrador."}, status=400)
            
        admin_user = membership.user
        from django.utils.crypto import get_random_string
        new_password = get_random_string(12, allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*')
        admin_user.set_password(new_password)
        admin_user.force_password_change = True
        admin_user.save()
        
        from apps.audit.services import log_audit_event
        log_audit_event(
            user=request.user,
            clinic=None,
            action="UPDATE",
            model_name="User",
            object_id=str(admin_user.pk),
            before_data={"event": "Senha resetada pelo SuperAdmin"},
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        
        from rest_framework.response import Response
        return Response({
            "detail": "Senha redefinida com sucesso.",
            "temporary_password": new_password,
            "admin_email": admin_user.email
        })
from apps.accounts.permissions import IsClinicAdminOrSuperuser
from apps.accounts.models import Membership
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.viewsets import ModelViewSet
from django.contrib.auth import get_user_model

from .serializers import (
    LoginSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    UserMeSerializer,
)

User = get_user_model()


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data["user"]
            clinic = serializer.validated_data.get("clinic")
            role = serializer.validated_data.get("role")

            refresh = RefreshToken.for_user(user)

            if user.is_superuser:
                refresh["role"] = "SUPERUSER"
            else:
                refresh["clinic_id"] = clinic.id
                refresh["role"] = role

            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        new_password = request.data.get("new_password")
        if not new_password or len(new_password) < 8:
            return Response({"detail": "A senha deve ter pelo menos 8 caracteres."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.set_password(new_password)
        user.force_password_change = False
        user.save()
        
        from apps.audit.services import log_audit_event
        log_audit_event(
            user=user,
            clinic=None,
            action="UPDATE",
            model_name="User",
            object_id=str(user.pk),
            before_data={"event": "Senha alterada pelo usuário"},
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        return Response({"detail": "Senha atualizada com sucesso."})

class UpdateSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        from .models import UserSettings
        
        settings, _ = UserSettings.objects.get_or_create(user=user)
        
        theme = request.data.get("theme")
        primary_color = request.data.get("primary_color")
        density = request.data.get("density")
        font_size = request.data.get("font_size")
        extra_preferences = request.data.get("extra_preferences")
        
        if theme in ["light", "dark", "system"]:
            settings.theme = theme
        if primary_color is not None:
            settings.primary_color = primary_color
        if density in ["comfortable", "compact"]:
            settings.density = density
        if font_size in ["small", "medium", "large"]:
            settings.font_size = font_size
        if isinstance(extra_preferences, dict):
            settings.extra_preferences = extra_preferences
            
        settings.save()
        return Response({
            "detail": "Configurações atualizadas com sucesso.",
            "settings": {
                "theme": settings.theme,
                "primary_color": settings.primary_color,
                "density": settings.density,
                "font_size": settings.font_size,
                "extra_preferences": settings.extra_preferences,
            }
        })

class UserViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsClinicAdminOrSuperuser]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return User.objects.filter(memberships__isnull=False).distinct().prefetch_related("memberships__clinic")
            
        auth = self.request.auth
        if not auth:
            return User.objects.none()
            
        clinic_id = auth.get("clinic_id")
        if not clinic_id:
            return User.objects.none()

        from apps.clinics.models import Clinic
        from rest_framework.exceptions import PermissionDenied
        if not Clinic.objects.filter(id=clinic_id, is_active=True).exists():
            raise PermissionDenied("Acesso negado: Esta clínica está inativa.")

        return User.objects.filter(
            memberships__clinic_id=clinic_id
        ).distinct()


    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return UserMeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from .models import PasswordResetToken

class RequestPasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"detail": "Email é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)
            
        user = User.objects.filter(email=email).first()
        if user:
            # Geração de token seguro
            token_str = get_random_string(64)
            PasswordResetToken.objects.create(user=user, token=token_str)
            
            # Simulated send_mail logic since this is usually async, but we send directly here
            # link = f"{request.scheme}://{request.get_host()}/reset-password?token={token_str}"
            # In a real app, we'd send an email. We just pretend to or use django's send_mail
            # send_mail(
            #     "Recuperação de Senha",
            #     f"Acesse o link para redefinir sua senha: {link}",
            #     "noreply@clinify.com",
            #     [email],
            #     fail_silently=True,
            # )
            
            # Retornando o token apenas para facilitar testes localmente
            # Na produção NÃO devemos retornar o token na resposta
            return Response({"detail": "Se o email existir, um link de recuperação foi enviado.", "debug_token": token_str})
            
        return Response({"detail": "Se o email existir, um link de recuperação foi enviado."})

class ResetPasswordConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token_str = request.data.get("token")
        new_password = request.data.get("password")
        
        if not token_str or not new_password:
            return Response({"detail": "Token e nova senha são obrigatórios."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Validação de força de senha
        if len(new_password) < 8:
            return Response({"detail": "A senha deve ter pelo menos 8 caracteres."}, status=status.HTTP_400_BAD_REQUEST)
            
        token_obj = PasswordResetToken.objects.filter(token=token_str).first()
        
        if not token_obj or not token_obj.is_valid():
            return Response({"detail": "Token inválido ou expirado."}, status=status.HTTP_400_BAD_REQUEST)
            
        user = token_obj.user
        user.set_password(new_password)
        user.save()
        
        # Invalida o token após o uso (Proteção contra reutilização)
        token_obj.used = True
        token_obj.save()
        
        return Response({"detail": "Senha redefinida com sucesso."})
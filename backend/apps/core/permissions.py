from rest_framework.permissions import BasePermission


class BaseClinicRolePermission(BasePermission):
    """
    Permissão base que verifica o role do usuário na clínica ativa
    usando o token JWT (clinic_id + role injetados no login).
    """

    allowed_roles = []

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        # Superuser sempre tem acesso
        if user.is_superuser:
            return True

        # Role vem direto do token JWT
        user_role = request.auth.get("role") if request.auth else None

        return user_role in self.allowed_roles


class IsAdmin(BaseClinicRolePermission):
    allowed_roles = ["ADMIN"]


class IsProfessional(BaseClinicRolePermission):
    allowed_roles = ["PROFESSIONAL"]


class IsAttendant(BaseClinicRolePermission):
    allowed_roles = ["ATTENDANT"]


class IsAdminOrProfessional(BaseClinicRolePermission):
    allowed_roles = ["ADMIN", "PROFESSIONAL"]


class IsAdminOrAttendant(BaseClinicRolePermission):
    allowed_roles = ["ADMIN", "ATTENDANT"]


class IsAnyClinicRole(BaseClinicRolePermission):
    allowed_roles = ["ADMIN", "PROFESSIONAL", "ATTENDANT"]
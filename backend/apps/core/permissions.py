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

        # Superuser da plataforma NÃO deve ter acesso aos endpoints operacionais da clínica
        # a menos que o perfil dele permita de alguma outra forma, mas isso é bloqueado
        # pois role vem do token e Superuser não deveria ter role operacional se não está numa clínica.


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
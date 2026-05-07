from rest_framework.permissions import BasePermission


class BaseRolePermission(BasePermission):

    allowed_roles = []

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        # Superuser sempre tem acesso
        if user.is_superuser:
            return True

        user_role = getattr(user, "role", None)

        return user_role in self.allowed_roles


class IsAdmin(BaseRolePermission):
    allowed_roles = ["admin"]


class IsProfessional(BaseRolePermission):
    allowed_roles = ["professional"]


class IsStaff(BaseRolePermission):
    allowed_roles = ["staff"]


class IsAdminOrProfessional(BaseRolePermission):
    allowed_roles = ["admin", "professional"]
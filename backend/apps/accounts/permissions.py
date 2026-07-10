from rest_framework.permissions import BasePermission

class IsAuthenticatedAndHasClinic(BasePermission):
    """
    Garante que o usuário esteja autenticado
    e que exista clinic_id no token.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        clinic_id = request.auth.get("clinic_id") if request.auth else None
        return clinic_id is not None


class IsClinicAdminOrSuperuser(BasePermission):
    """
    Permite acesso ao ADMIN da clínica ou ao SuperAdmin da plataforma.
    """
    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        role = request.auth.get("role") if request.auth else None
        return role == "ADMIN" or user.is_superuser


class IsClinicUserWithRestrictions(BasePermission):
    """
    Admin → acesso total na clínica
    Attendant → não pode deletar
    Professional → apenas leitura
    """
    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        role = request.auth.get("role") if request.auth else None

        # ADMIN → tudo
        if role == "ADMIN":
            return True

        # ATTENDANT
        if role == "ATTENDANT":
            if view.action == "destroy":
                return False
            return True

        # PROFESSIONAL
        if role == "PROFESSIONAL":
            if view.action in ["list", "retrieve", "start_attendance", "finalizar"]:
                return True
            return False

        return False
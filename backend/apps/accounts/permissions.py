from rest_framework.permissions import BasePermission


class IsAuthenticatedAndHasClinic(BasePermission):
    """
    Garante que o usuário esteja autenticado
    e que exista clinic_id no token.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # superuser pode tudo mesmo sem clinic ativa
        if request.user.is_superuser:
            return True

        clinic_id = request.auth.get("clinic_id")
        return clinic_id is not None


class IsClinicAdminOrSuperuser(BasePermission):
    """
    Permite acesso apenas para ADMIN da clínica ativa
    ou superuser do sistema.
    """

    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        clinic_id = request.auth.get("clinic_id")

        if not clinic_id:
            return False

        membership = user.memberships.filter(
            clinic_id=clinic_id,
            is_active=True
        ).first()

        if not membership:
            return False

        return membership.role == "ADMIN"


class IsClinicUserWithRestrictions(BasePermission):
    """
    Superuser → acesso total
    Admin → acesso total na clínica
    Attendant → não pode deletar
    Professional → apenas leitura
    """

    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        clinic_id = request.auth.get("clinic_id")
        if not clinic_id:
            return False

        membership = user.memberships.filter(
            clinic_id=clinic_id,
            is_active=True
        ).first()

        if not membership:
            return False

        role = membership.role

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
            if view.action in ["list", "retrieve"]:
                return True
            return False

        return False
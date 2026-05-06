from rest_framework.permissions import BasePermission

class IsAdminOrSuperuser(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_superuser or user.role == "admin"
    
class IsClinicUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated
    


class IsClinicUserWithRestrictions(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        # superuser pode tudo
        if user.is_superuser:
            return True

        # admin pode tudo
        if user.role == "admin":
            return True

        # staff
        if user.role == "staff":
            if view.action in ["list", "retrieve", "create", "update", "partial_update"]:
                return True
            if view.action == "destroy":
                return False

        return False    
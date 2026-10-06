from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from apps.clinics.permissions import IsSuperUser
from .models import AuditLog
from .serializers import AuditLogSerializer

class AuditLogViewSet(ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    # Superuser only, declarado como politica (antes so existia implicito
    # na exception de get_queryset). Mesmo resultado, agora explicito.
    permission_classes = [IsAuthenticated, IsSuperUser]

    def get_queryset(self):
        if not self.request.user.is_superuser:
            raise PermissionDenied("Apenas SuperAdmins podem visualizar os logs de auditoria.")
        return AuditLog.objects.all().select_related("user", "clinic")

from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from apps.clinics.permissions import IsSuperUser
from .models import AuditLog
from .serializers import AuditLogSerializer

class AuditLogViewSet(ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    # Superuser only, declarado como politica explicita. O IsSuperUser
    # bloqueia 403 antes mesmo de chegar ao queryset.
    permission_classes = [IsAuthenticated, IsSuperUser]

    def get_queryset(self):
        return AuditLog.objects.all().select_related("user", "clinic")

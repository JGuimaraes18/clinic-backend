from apps.core.views import ClinicSafeModelViewSet
from .models import Professional
from .serializers import ProfessionalSerializer
from apps.core.permissions import IsAdminOrProfessional


class ProfessionalViewSet(ClinicSafeModelViewSet):
    queryset = Professional.objects.all()
    serializer_class = ProfessionalSerializer
    permission_classes = [IsAdminOrProfessional]
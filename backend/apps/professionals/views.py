from apps.core.views import ClinicSafeModelViewSet
from apps.accounts.permissions import IsClinicUserWithRestrictions
from .models import Professional
from .serializers import ProfessionalSerializer


class ProfessionalViewSet(ClinicSafeModelViewSet):
    queryset = Professional.objects.select_related(
        "user"
    )
    serializer_class = ProfessionalSerializer
    permission_classes = [IsClinicUserWithRestrictions]
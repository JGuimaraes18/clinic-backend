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

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        role = self.request.auth.get("role") if self.request.auth else None

        if role == "PROFESSIONAL":
            return queryset.filter(user=user)

        return queryset
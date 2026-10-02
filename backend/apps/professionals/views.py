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
        clinic_id = self.get_user_clinic_id()
        user = self.request.user
        role = self.request.auth.get("role") if self.request.auth else None

        queryset = super().get_queryset().filter(
            clinics__membership__clinic_id=clinic_id,
            clinics__membership__is_active=True,
            clinics__is_active=True,
        ).distinct()

        if role == "PROFESSIONAL":
            return queryset.filter(user=user)

        return queryset
from apps.core.views import ClinicSafeModelViewSet
from apps.accounts.permissions import IsClinicUserWithRestrictions
from .models import Patient
from .serializers import PatientSerializer


class PatientViewSet(ClinicSafeModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsClinicUserWithRestrictions]

    def get_queryset(self):
        queryset = super().get_queryset()
        membership = self.request.user.memberships.filter(
            is_active=True
        ).first()

        if not membership:
            return Patient.objects.none()

        return queryset.filter(clinic=membership.clinic)
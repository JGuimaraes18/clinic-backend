from apps.core.views import ClinicSafeModelViewSet
from apps.accounts.permissions import IsClinicUserWithRestrictions
from .models import Patient
from .serializers import PatientSerializer


class PatientViewSet(ClinicSafeModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsClinicUserWithRestrictions]
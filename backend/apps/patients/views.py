from django.shortcuts import render

# Create your views here.
from apps.core.views import ClinicSafeModelViewSet
from .models import Patient
from .serializers import PatientSerializer
from apps.core.permissions import IsAdminOrProfessional


class PatientViewSet(ClinicSafeModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAdminOrProfessional]
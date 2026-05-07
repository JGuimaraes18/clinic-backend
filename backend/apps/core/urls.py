from rest_framework.routers import DefaultRouter
from django.urls import path, include

from apps.patients.views import PatientViewSet
from apps.appointments.views import AtendimentoViewSet
from apps.medical_records.views import ProntuarioViewSet
from apps.professionals.views import ProfessionalViewSet
from apps.clinics.views import ClinicViewSet

router = DefaultRouter()

router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'appointments', AtendimentoViewSet, basename='appointment')
router.register(r'medical-records', ProntuarioViewSet, basename='medical-record')
router.register(r'professionals', ProfessionalViewSet, basename='professional')
router.register(r'clinics', ClinicViewSet, basename='clinic')

urlpatterns = [
    path('', include(router.urls)),
]
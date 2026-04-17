from rest_framework.routers import DefaultRouter
from django.urls import path, include

from apps.patients.views import PatientViewSet
from apps.appointments.views import AtendimentoViewSet
from apps.medical_records.views import ProntuarioViewSet
from apps.clinics.views import ClinicViewSet

router = DefaultRouter()

router.register(r'patients', PatientViewSet, basename='patients')
router.register(r'appointments', AtendimentoViewSet, basename='appointments')
router.register(r'medical-records', ProntuarioViewSet, basename='medical-records')
router.register(r"clinics", ClinicViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
from rest_framework.viewsets import ModelViewSet
from .models import Clinic
from .serializers import ClinicSerializer
from rest_framework.permissions import IsAdminUser


class ClinicViewSet(ModelViewSet):
    queryset = Clinic.objects.all()
    serializer_class = ClinicSerializer
    permission_classes = [IsAdminUser]
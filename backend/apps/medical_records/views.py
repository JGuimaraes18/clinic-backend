from apps.core.views import ClinicSafeModelViewSet
from .models import Prontuario
from .serializers import ProntuarioSerializer
from apps.core.permissions import IsAdminOrProfessional


class ProntuarioViewSet(ClinicSafeModelViewSet):
    queryset = Prontuario.objects.select_related(
        "paciente",
        "atendimento",
        "profissional",
    )
    serializer_class = ProntuarioSerializer
    permission_classes = [IsAdminOrProfessional]
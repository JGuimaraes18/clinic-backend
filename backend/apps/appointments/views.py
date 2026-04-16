from apps.core.views import ClinicSafeModelViewSet
from .models import Atendimento
from .serializers import AtendimentoSerializer
from apps.core.permissions import IsAdminOrProfessional


class AtendimentoViewSet(ClinicSafeModelViewSet):
    queryset = Atendimento.objects.select_related(
        "paciente",
        "dentista",
    )
    serializer_class = AtendimentoSerializer
    permission_classes = [IsAdminOrProfessional]
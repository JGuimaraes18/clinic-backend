from apps.core.views import ClinicSafeModelViewSet
from .models import Prontuario
from .serializers import ProntuarioSerializer
from apps.core.permissions import IsAdminOrProfessional


class ProntuarioViewSet(ClinicSafeModelViewSet):
    serializer_class = ProntuarioSerializer
    permission_classes = [IsAdminOrProfessional]

    def get_queryset(self):
        user = self.request.user

        return (
            Prontuario.objects
            .filter(atendimento__clinic=user.clinic)
            .select_related(
                "atendimento",
                "atendimento__paciente",
                "atendimento__dentista",
                "atendimento__clinic",
                "finalizado_por",
            )
        )

    def perform_create(self, serializer):
        serializer.save(
            finalizado_por=self.request.user
        )
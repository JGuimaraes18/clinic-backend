from rest_framework.decorators import action
from rest_framework.response import Response
from apps.core.views import ClinicSafeModelViewSet
from apps.core.permissions import IsAdminOrProfessional
from apps.medical_records.models import Prontuario

from .models import Atendimento
from .serializers import AtendimentoSerializer


class AtendimentoViewSet(ClinicSafeModelViewSet):

    queryset = Atendimento.objects.select_related(
        "clinic",
        "paciente",
        "profissional",
    )

    serializer_class = AtendimentoSerializer
    permission_classes = [IsAdminOrProfessional]

    @action(detail=True, methods=["post"])
    def iniciar_atendimento(self, request, pk=None):
        atendimento = self.get_object()

        if atendimento.status != "AGENDADO":
            return Response(
                {"detail": "Atendimento já iniciado ou finalizado."},
                status=400
            )

        # 1. muda status primeiro
        atendimento.status = "EM_ATENDIMENTO"
        atendimento.save()

        # 2. cria prontuário (se não existir)
        prontuario, _ = Prontuario.objects.get_or_create(
            atendimento=atendimento,
            defaults={"conteudo": ""}
        )

        return Response({
            "prontuario_id": prontuario.id,
            "atendimento_id": atendimento.id
        })

    @action(detail=True, methods=["post"])
    def finalizar(self, request, pk=None):
        atendimento = self.get_object()

        if atendimento.status != "EM_ATENDIMENTO":
            return Response(
                {"detail": "Atendimento não está em andamento."},
                status=400
            )

        atendimento.status = "REALIZADO"
        atendimento.save()

        return Response({"detail": "Atendimento finalizado."})
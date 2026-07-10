from apps.accounts.permissions import IsClinicUserWithRestrictions, IsAuthenticatedAndHasClinic
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.core.views import ClinicSafeModelViewSet
from apps.medical_records.models import Prontuario
from django.db import transaction
from .models import Atendimento
from .serializers import AtendimentoSerializer


class AtendimentoViewSet(ClinicSafeModelViewSet):

    queryset = Atendimento.objects.select_related(
        "clinic",
        "paciente",
        "profissional",
    )

    serializer_class = AtendimentoSerializer

    def get_permissions(self):
        # Override to allow PROFESSIONAL to update/partial_update
        if self.action in ["update", "partial_update"]:
            user = self.request.user
            role = self.request.auth.get("role") if self.request.auth else None
            if role == "PROFESSIONAL":
                return [IsAuthenticatedAndHasClinic()]
        return [IsClinicUserWithRestrictions()]


    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        role = self.request.auth.get("role") if self.request.auth else None

        if role == "PROFESSIONAL":
            return queryset.filter(profissional__user=user)

        return queryset

    @action(detail=True, methods=["post"])
    def start_attendance(self, request, pk=None):
        with transaction.atomic():
            atendimento = self.get_object()

            if atendimento.status != "AGENDADO":
                return Response(
                    {"detail": "Atendimento já iniciado ou finalizado."},
                    status=400
                )

            atendimento.status = "EM_ATENDIMENTO"
            atendimento.save()

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
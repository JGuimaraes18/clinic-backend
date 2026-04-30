from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ValidationError
from apps.core.views import ClinicSafeModelViewSet
from apps.core.permissions import IsAdminOrProfessional
from .models import Prontuario, AdendoProntuario
from .serializers import ( ProntuarioSerializer, AdendoProntuarioSerializer )


class ProntuarioViewSet(ClinicSafeModelViewSet):
    serializer_class = ProntuarioSerializer
    permission_classes = [IsAdminOrProfessional]

    def get_queryset(self):
        user = self.request.user

        qs = Prontuario.objects.filter(
            atendimento__clinic=user.clinic
        ).select_related(
            "atendimento",
            "atendimento__paciente",
            "atendimento__profissional",
            "finalizado_por",
        )

        params = self.request.query_params

        if params.get("paciente"):
            qs = qs.filter(atendimento__paciente_id=params["paciente"])

        if params.get("profissional"):
            qs = qs.filter(atendimento__profissional_id=params["profissional"])

        return qs

    def perform_create(self, serializer):
        appointment = serializer.validated_data["atendimento"]
        user = self.request.user

        if not (
            user.is_superuser or
            appointment.profissional.user == user
        ):
            raise ValidationError(
                "Apenas o médico responsável pode iniciar atendimento."
            )

        serializer.save()

    @action(detail=True, methods=["get"])
    def historico(self, request, pk=None):
        prontuario = self.get_object()

        paciente = prontuario.atendimento.paciente
        profissional = prontuario.atendimento.profissional

        historico = (
            Prontuario.objects
            .filter(
                atendimento__paciente=paciente,
                atendimento__profissional=profissional,
                status="FECHADO"
            )
            .exclude(pk=prontuario.pk)
            .select_related("atendimento")
            .order_by("-finalizado_em")
        )

        data = [
            {
                "id": p.id,
                "data": p.finalizado_em,
                "resumo": p.conteudo[:150],
            }
            for p in historico
        ]

        return Response(data)

    @action(detail=True, methods=["post"])
    def fechar(self, request, pk=None):
        prontuario = self.get_object()

        try:
            prontuario.fechar(request.user)

            atendimento = prontuario.atendimento
            atendimento.status = "REALIZADO"
            atendimento.save(update_fields=["status"])

            return Response(
                {"detail": "Prontuário fechado com sucesso."}
            )

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    
class AdendoProntuarioViewSet(ClinicSafeModelViewSet):
    serializer_class = AdendoProntuarioSerializer
    permission_classes = [IsAdminOrProfessional]

    def get_queryset(self):
        user = self.request.user

        return (
            AdendoProntuario.objects
            .filter(prontuario__atendimento__clinic=user.clinic)
            .select_related("prontuario", "criado_por")
        )
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
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

        # Superuser vê tudo
        if user.is_superuser:
            qs = Prontuario.objects.all()
        else:
            clinic_id = self.get_user_clinic_id()

            qs = Prontuario.objects.filter(
                atendimento__clinic_id=clinic_id
            )

        qs = qs.select_related(
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
                atendimento__clinic_id=prontuario.atendimento.clinic_id,
                atendimento__paciente=paciente,
                atendimento__profissional=profissional,
                status="FECHADO"
            )
            .exclude(pk=prontuario.pk)
            .select_related("atendimento")
            .order_by("-finalizado_em")
        )

        # mesma regra aplicada em ProntuarioSerializer.to_representation:
        # apenas o profissional responsavel enxerga o conteudo clinico
        pode_ver_conteudo = (
            profissional is not None
            and profissional.user_id == request.user.id
        )

        data = [
            {
                "id": p.id,
                "data": p.finalizado_em,
                "resumo": (
                    p.conteudo[:150] if pode_ver_conteudo
                    else "Acesso restrito (Informação Sensível)"
                ),
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
        
    @action(detail=False, methods=["get"], url_path="by-appointment/(?P<appointment_id>[^/.]+)")
    def by_appointment(self, request, appointment_id=None):
        try:
            # get_queryset() aplica o filtro por clinica do token; sem ele,
            # qualquer atendimento de outra clinica seria lido aqui
            prontuario = self.get_queryset().get(atendimento_id=appointment_id)
        except Prontuario.DoesNotExist:
            return Response(
                {"detail": "Prontuário não encontrado."},
                status=404
            )

        return Response(self.get_serializer(prontuario).data)
        

class AdendoProntuarioViewSet(ClinicSafeModelViewSet):
    serializer_class = AdendoProntuarioSerializer
    permission_classes = [IsAdminOrProfessional]

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            qs = AdendoProntuario.objects.all()
        else:
            clinic_id = self.get_user_clinic_id()

            qs = AdendoProntuario.objects.filter(
                prontuario__atendimento__clinic_id=clinic_id
            )

        return qs.select_related("prontuario", "criado_por")
from rest_framework import serializers
from django.utils import timezone
from django.db import IntegrityError
from apps.accounts.models import Membership
from apps.professionals.models import ProfessionalClinic
from .models import Atendimento


class AtendimentoSerializer(serializers.ModelSerializer):

    paciente_nome = serializers.CharField(
        source="paciente.full_name",
        read_only=True
    )

    profissional_nome = serializers.CharField(
        source="profissional.user.get_full_name",
        read_only=True
    )

    class Meta:
        model = Atendimento
        fields = "__all__"
        read_only_fields = (
            "clinic",
            "created_at",
            "updated_at",
            "is_deleted",
        )

    # ----------------------------------------------------
    # UTIL
    # ----------------------------------------------------
    def get_user_clinic(self):
        request = self.context["request"]

        membership = Membership.objects.filter(
            user=request.user,
            is_active=True
        ).first()

        if not membership:
            raise serializers.ValidationError(
                "Usuário sem clínica ativa."
            )

        return membership.clinic

    # ----------------------------------------------------
    # FIELD VALIDATION
    # ----------------------------------------------------
    def validate_data_hora(self, value):
        if value < timezone.now():
            raise serializers.ValidationError(
                "Não é permitido agendar para datas passadas."
            )
        return value

    # ----------------------------------------------------
    # OBJECT VALIDATION
    # ----------------------------------------------------
    def validate(self, attrs):
        clinic = self.get_user_clinic()

        paciente = attrs.get("paciente")
        profissional = attrs.get("profissional")
        data_hora = attrs.get("data_hora")

        # ✅ Validação paciente (caso Patient tenha FK direta para clinic)
        if paciente and hasattr(paciente, "clinic"):
            if paciente.clinic != clinic:
                raise serializers.ValidationError(
                    {"paciente": "Paciente não pertence a esta clínica."}
                )

        # ✅ Validação profissional via ProfessionalClinic
        if profissional:
            is_linked = ProfessionalClinic.objects.filter(
                professional=profissional,
                membership__clinic=clinic,
                is_active=True
            ).exists()

            if not is_linked:
                raise serializers.ValidationError(
                    {"profissional": "Profissional não pertence a esta clínica."}
                )

        # ✅ Validação conflito de horário
        if profissional and data_hora:
            queryset = Atendimento.objects.filter(
                clinic=clinic,
                profissional=profissional,
                data_hora=data_hora,
            ).exclude(status="CANCELADO")

            if self.instance:
                queryset = queryset.exclude(id=self.instance.id)

            if queryset.exists():
                raise serializers.ValidationError(
                    "Já existe um agendamento para esse profissional nesse horário."
                )

        return attrs

    # ----------------------------------------------------
    # CREATE
    # ----------------------------------------------------
    def create(self, validated_data):
        clinic = self.get_user_clinic()
        validated_data["clinic"] = clinic

        try:
            return super().create(validated_data)
        except IntegrityError:
            raise serializers.ValidationError(
                "Já existe um agendamento para esse profissional nesse horário."
            )

    # ----------------------------------------------------
    # UPDATE
    # ----------------------------------------------------
    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except IntegrityError:
            raise serializers.ValidationError(
                "Já existe um agendamento para esse profissional nesse horário."
            )
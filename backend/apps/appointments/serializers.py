from rest_framework import serializers
from django.utils import timezone
from django.db import IntegrityError
from .models import Atendimento


class AtendimentoSerializer(serializers.ModelSerializer):

    paciente_nome = serializers.CharField(
        source="paciente.full_name",
        read_only=True
    )

    profissional_nome = serializers.CharField(
        source="profissional.full_name",
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

    def validate_data_hora(self, value):
        if value < timezone.now():
            raise serializers.ValidationError(
                "Não é permitido agendar para datas passadas."
            )
        return value
    
    def validate(self, attrs):
        clinic = self.context["request"].user.clinic
        profissional = attrs.get("profissional")
        data_hora = attrs.get("data_hora")

        # Em caso de edição, ignorar o próprio registro
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
    
    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError:
            raise serializers.ValidationError(
                "Já existe um agendamento para esse profissional nesse horário."
            )

    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except IntegrityError:
            raise serializers.ValidationError(
                "Já existe um agendamento para esse profissional nesse horário."
            )
    
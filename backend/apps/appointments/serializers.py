from rest_framework import serializers
from django.utils import timezone
from .models import Atendimento


class AtendimentoSerializer(serializers.ModelSerializer):
    paciente_nome = serializers.CharField(source="paciente.full_name", read_only=True)
    profissional_nome = serializers.CharField(source="profissional.full_name", read_only=True)

    def validate_data_hora(self, value):
        if value < timezone.now():
            raise serializers.ValidationError(
                "Não é permitido agendar para datas passadas."
            )
        return value

    class Meta:
        model = Atendimento
        fields = "__all__"
        read_only_fields = ("clinic", "created_at", "is_deleted", "updated_at")
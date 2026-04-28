from rest_framework import serializers
from .models import Atendimento


class AtendimentoSerializer(serializers.ModelSerializer):
    paciente_nome = serializers.CharField(source="paciente.full_name", read_only=True)
    profissional_nome = serializers.CharField(source="profissional.full_name", read_only=True)

    class Meta:
        model = Atendimento
        fields = "__all__"
        read_only_fields = ("clinic", "created_at", "is_deleted", "updated_at")
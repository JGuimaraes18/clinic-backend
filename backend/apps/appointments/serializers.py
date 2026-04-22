from rest_framework import serializers
from .models import Atendimento


class AtendimentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Atendimento
        fields = "__all__"
        read_only_fields = ("clinic", "created_at", "is_deleted", "updated_at")
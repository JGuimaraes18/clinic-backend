from rest_framework import serializers
from .models import Prontuario


class ProntuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prontuario
        fields = "__all__"
        read_only_fields = ("clinic", "criado_em")
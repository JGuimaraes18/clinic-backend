from rest_framework import serializers
from .models import Prontuario, AdendoProntuario


class ProntuarioSerializer(serializers.ModelSerializer):

    class Meta:
        model = Prontuario
        fields = "__all__"
        read_only_fields = (
            "hash_integridade",
            "criado_em",
            "finalizado_em",
            "finalizado_por",
        )

    def validate(self, attrs):
        """
        Impede criação de mais de um prontuário para o mesmo atendimento.
        (OneToOne já protege, mas aqui fica erro amigável)
        """
        atendimento = attrs.get("atendimento")

        if self.instance is None:
            if Prontuario.objects.filter(atendimento=atendimento).exists():
                raise serializers.ValidationError(
                    "Já existe prontuário para este atendimento."
                )

        return attrs

    def create(self, validated_data):
        """
        Cria como RASCUNHO.
        Não altera status do atendimento aqui.
        """
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Impede alteração se estiver FECHADO.
        """
        if instance.status == "FECHADO":
            raise serializers.ValidationError(
                "Prontuário fechado não pode ser alterado."
            )

        return super().update(instance, validated_data)


class AdendoProntuarioSerializer(serializers.ModelSerializer):

    class Meta:
        model = AdendoProntuario
        fields = "__all__"
        read_only_fields = ("criado_em", "criado_por")

    def create(self, validated_data):
        validated_data["criado_por"] = self.context["request"].user
        return super().create(validated_data)
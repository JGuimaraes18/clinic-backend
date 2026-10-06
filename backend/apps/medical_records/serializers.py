from rest_framework import serializers
from .models import Prontuario, AdendoProntuario


def can_view_conteudo(user, atendimento):
    """
    Regra unica de acesso ao conteudo clinico (B2c).

    Somente o profissional responsavel pelo atendimento enxerga o conteudo.
    Atendimento.profissional e opcional (null=True): sem profissional
    definido, ninguem enxerga o conteudo.
    """
    profissional = getattr(atendimento, "profissional", None)
    user_id = getattr(user, "id", None)

    if profissional is None or user_id is None:
        return False

    return profissional.user_id == user_id


RESTRITO = "Acesso restrito (Informação Sensível)"


class ProntuarioSerializer(serializers.ModelSerializer):

    class Meta:
        model = Prontuario
        # SHA-256 sem sal do conteudo: nao revela o conteudo, mas permite
        # forca bruta offline e anula a mascara aplicada em to_representation
        exclude = ("hash_integridade",)
        read_only_fields = (
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

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")

        if request and request.user and not can_view_conteudo(request.user, instance.atendimento):
            data["conteudo"] = RESTRITO

        return data


class AdendoProntuarioSerializer(serializers.ModelSerializer):

    class Meta:
        model = AdendoProntuario
        fields = "__all__"
        read_only_fields = ("criado_em", "criado_por")

    def create(self, validated_data):
        validated_data["criado_por"] = self.context["request"].user
        return super().create(validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")

        if request and request.user and not can_view_conteudo(request.user, instance.prontuario.atendimento):
            data["conteudo"] = RESTRITO

        return data

import re
from rest_framework import serializers
from .models import Patient
from apps.core.utils import resolve_user_clinic


def normalize_cpf(value: str) -> str:
    return re.sub(r"\D", "", value or "")


class PatientSerializer(serializers.ModelSerializer):
    """
    Contrato publico do paciente (B6 - protecao de CPF/RG).

    INPUT: `cpf` e `document` continuam aceitos (necessarios para criar e
    editar o cadastro).

    OUTPUT: nenhum dos tres campos sensiveis e devolvido:
      * `cpf`        -> write_only
      * `document`   -> write_only
      * `cpf_hash`   -> fora de `fields` (detalhe interno de unicidade
                        por clinica; o model continua calculando e
                        persistindo normalmente)
    """

    class Meta:
        model = Patient
        fields = [
            "id",
            "full_name",
            "cpf",
            "document",
            "phone",
            "email",
            "birth_date",
            "clinic",
            "is_deleted",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "clinic",
            "is_deleted",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "cpf": {"write_only": True, "required": False, "allow_null": True},
            "document": {"write_only": True, "required": False, "allow_null": True},
        }

    def get_user_clinic(self):
        return resolve_user_clinic(self.context)

    def validate(self, attrs):
        clinic = self.get_user_clinic()
        cpf = attrs.get("cpf")

        if cpf and clinic:
            cpf_normalizado = normalize_cpf(cpf)

            if len(cpf_normalizado) != 11:
                raise serializers.ValidationError(
                    {"cpf": "CPF must contain 11 digits."}
                )

            cpf_hash = Patient().generate_cpf_hash(cpf_normalizado)

            queryset = Patient.all_objects.filter(
                clinic=clinic,
                cpf_hash=cpf_hash,
                is_deleted=False
            )

            if self.instance:
                queryset = queryset.exclude(id=self.instance.id)

            if queryset.exists():
                raise serializers.ValidationError(
                    {"cpf": "CPF already registered in this clinic."}
                )

        return attrs

    def create(self, validated_data):
        clinic = self.get_user_clinic()
        if clinic:
            validated_data["clinic"] = clinic
        return super().create(validated_data)
import re

from rest_framework import serializers
from .models import Patient

def normalize_cpf(value: str) -> str:
    return re.sub(r"\D", "", value or "")


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = "__all__"
        read_only_fields = ["clinic", "is_deleted", "created_at", "updated_at", "cpf_hash"]

    def validate(self, attrs):
        request = self.context.get("request")
        clinic = request.user.clinic
        cpf = attrs.get("cpf")

        if cpf:
            cpf_normalizado = normalize_cpf(cpf)

            if len(cpf_normalizado) != 11:
                raise serializers.ValidationError(
                    {"cpf": "CPF must contain 11 digits."}
                )

            cpf_hash = Patient().generate_cpf_hash(cpf_normalizado)

            exists = Patient.all_objects.filter(
                clinic=clinic,
                cpf_hash=cpf_hash,
                is_deleted=False
            ).exists()

            if exists:
                raise serializers.ValidationError(
                    {"cpf": "CPF already registered in this clinic."}
                )

        return attrs

    def create(self, validated_data):
        validated_data["clinic"] = self.context["request"].user.clinic
        return super().create(validated_data)
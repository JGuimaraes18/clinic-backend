import re
from rest_framework import serializers
from .models import Patient
from apps.accounts.models import Membership


def normalize_cpf(value: str) -> str:
    return re.sub(r"\D", "", value or "")


class PatientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Patient
        fields = "__all__"
        read_only_fields = [
            "clinic",
            "is_deleted",
            "created_at",
            "updated_at",
            "cpf_hash"
        ]

    def get_user_clinic(self):
        request = self.context["request"]

        membership = Membership.objects.filter(
            user=request.user,
            is_active=True
        ).first()

        if not membership:
            raise serializers.ValidationError("Usuário não vinculado a nenhuma clínica.")

        return membership.clinic

    def validate(self, attrs):
        clinic = self.get_user_clinic()
        cpf = attrs.get("cpf")

        if cpf:
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
        validated_data["clinic"] = clinic
        return super().create(validated_data)
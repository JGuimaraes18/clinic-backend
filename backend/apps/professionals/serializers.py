from rest_framework import serializers
from apps.clinics.models import Clinic
from apps.accounts.models import Membership
from .models import Professional, ProfessionalClinic


class ProfessionalSerializer(serializers.ModelSerializer):

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Professional
        fields = "__all__"
        read_only_fields = (
            "created_at",
            "updated_at",
            "is_deleted",
        )

    def get_full_name(self, obj):
        return obj.user.get_full_name()

    def validate(self, attrs):
        target_user = attrs.get("user")

        if target_user is not None:
            request = self.context["request"]
            clinic_id = request.auth.get("clinic_id") if request.auth else None

            if not clinic_id:
                raise serializers.ValidationError("Usuário sem clínica ativa.")

            if not Membership.objects.filter(
                user=target_user,
                clinic_id=clinic_id,
                is_active=True,
            ).exists():
                raise serializers.ValidationError(
                    {"user": "Usuário não pertence a esta clínica."}
                )

        return attrs

    def get_user_clinic(self):
        request = self.context["request"]
        clinic_id = request.auth.get("clinic_id") if request.auth else None

        if request.user.is_superuser and not clinic_id:
            return None

        if not clinic_id:
            raise serializers.ValidationError(
                "Usuário sem clínica ativa."
            )

        try:
            return Clinic.objects.get(id=clinic_id)
        except Clinic.DoesNotExist:
            raise serializers.ValidationError("Clínica não encontrada.")

    def create(self, validated_data):
        professional = super().create(validated_data)

        request = self.context["request"]
        clinic_id = request.auth.get("clinic_id") if request.auth else None

        if clinic_id:
            from apps.accounts.models import Membership
            # Procura a membership do usuário recém-transformado em profissional,
            # não a do usuário logado (que poderia ser admin/superuser)
            membership = Membership.objects.filter(
                user=professional.user,
                clinic_id=clinic_id,
                is_active=True
            ).first()

            if membership:
                ProfessionalClinic.objects.create(
                    professional=professional,
                    membership=membership,
                    specialty=professional.specialty or "",
                    is_active=True
                )

        return professional
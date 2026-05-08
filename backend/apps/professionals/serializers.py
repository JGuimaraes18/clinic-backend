from rest_framework import serializers
from apps.accounts.models import Membership
from .models import Professional, ProfessionalClinic


class ProfessionalSerializer(serializers.ModelSerializer):

    full_name = serializers.CharField(
        source="user.get_full_name",
        read_only=True
    )

    class Meta:
        model = Professional
        fields = "__all__"
        read_only_fields = (
            "created_at",
            "updated_at",
            "is_deleted",
        )

    def get_user_membership(self):
        request = self.context["request"]

        membership = Membership.objects.filter(
            user=request.user,
            is_active=True
        ).first()

        if not membership:
            raise serializers.ValidationError(
                "Usuário não possui clínica ativa."
            )

        return membership

    def create(self, validated_data):
        membership = self.get_user_membership()

        professional = super().create(validated_data)

        # 🔥 cria automaticamente o vínculo
        ProfessionalClinic.objects.create(
            professional=professional,
            membership=membership,
            specialty=professional.specialty or "",
            is_active=True
        )

        return professional
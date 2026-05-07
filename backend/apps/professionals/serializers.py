from rest_framework import serializers
from .models import Professional
from apps.accounts.models import Membership


class ProfessionalSerializer(serializers.ModelSerializer):

    user_id = serializers.IntegerField(write_only=True)

    full_name = serializers.CharField(
        source="membership.user.get_full_name",
        read_only=True
    )

    email = serializers.EmailField(
        source="membership.user.email",
        read_only=True
    )

    class Meta:
        model = Professional
        fields = "__all__"
        read_only_fields = [
            "is_deleted",
            "created_at",
            "updated_at"
        ]

    def validate(self, attrs):
        request = self.context["request"]
        user_id = self.initial_data.get("user_id")

        try:
            membership = Membership.objects.get(
                user_id=user_id,
                clinic=request.user.clinic,
                role="PROFESSIONAL",
                is_active=True
            )
        except Membership.DoesNotExist:
            raise serializers.ValidationError(
                "User is not a professional in this clinic."
            )

        attrs["membership"] = membership
        return attrs

    def create(self, validated_data):
        return Professional.objects.create(**validated_data)
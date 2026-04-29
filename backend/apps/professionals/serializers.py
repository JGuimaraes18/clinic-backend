from rest_framework import serializers
from .models import Professional


class ProfessionalSerializer(serializers.ModelSerializer):

    class Meta:
        model = Professional
        fields = "__all__"
        read_only_fields = [
            "clinic",
            "is_deleted",
            "created_at",
            "updated_at"
        ]

    def validate(self, attrs):
        request = self.context.get("request")
        clinic = request.user.clinic

        reg_type = attrs.get("registration_type")
        reg_number = attrs.get("registration_number")

        queryset = Professional.all_objects.filter(
            clinic=clinic,
            registration_type=reg_type,
            registration_number=reg_number,
            is_deleted=False
        )

        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.exists():
            raise serializers.ValidationError(
                "This registration already exists in this clinic."
            )

        return attrs

    def create(self, validated_data):
        validated_data["clinic"] = self.context["request"].user.clinic
        return super().create(validated_data)
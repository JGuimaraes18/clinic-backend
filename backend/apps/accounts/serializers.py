from django.contrib.auth import get_user_model
from rest_framework import serializers
from apps.clinics.models import Clinic

User = get_user_model()


class ClinicMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinic
        fields = ["id", "name"]


class UserMeSerializer(serializers.ModelSerializer):
    clinic = ClinicMiniSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "clinic",
            "is_superuser",
        ]
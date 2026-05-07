from rest_framework import serializers
from .models import Clinic


class ClinicSerializer(serializers.ModelSerializer):

    class Meta:
        model = Clinic
        fields = "__all__"
        read_only_fields = ["slug", "created_at"]
from rest_framework import serializers
from .models import Clinic
from apps.accounts.models import Membership


class ClinicSerializer(serializers.ModelSerializer):
    admin_email = serializers.SerializerMethodField()
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = Clinic
        fields = "__all__"
        read_only_fields = ["slug", "created_at"]

    def get_admin_email(self, obj):
        admin_membership = Membership.objects.filter(
            clinic=obj, role="ADMIN"
        ).select_related("user").first()
        return admin_membership.user.email if admin_membership else None

    def get_user_count(self, obj):
        return Membership.objects.filter(clinic=obj, is_active=True).count()
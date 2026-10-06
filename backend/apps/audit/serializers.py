from rest_framework import serializers
from .models import AuditLog
from .redaction import sanitize_snapshot
from django.contrib.auth import get_user_model

User = get_user_model()

class UserMiniSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "full_name"]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

class AuditLogSerializer(serializers.ModelSerializer):
    user_detail = UserMiniSerializer(source="user", read_only=True)
    clinic_name = serializers.CharField(source="clinic.name", read_only=True)
    # Camada 2: os payloads passam pela mesma politica de sanitizacao
    # usada na escrita, para que historico ja gravado tambem seja seguro.
    before_data = serializers.SerializerMethodField()
    after_data = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        # Allowlist explicita. Mesmo conjunto de chaves do antigo
        # `fields = "__all__"` + campos declarados acima: nenhum contrato
        # do frontend foi alterado.
        fields = (
            "id",
            "severity",
            "user",
            "clinic",
            "action",
            "model_name",
            "object_id",
            "before_data",
            "after_data",
            "ip_address",
            "timestamp",
            "user_detail",
            "clinic_name",
        )

    def get_before_data(self, obj):
        return sanitize_snapshot(obj.model_name, obj.before_data)

    def get_after_data(self, obj):
        return sanitize_snapshot(obj.model_name, obj.after_data)

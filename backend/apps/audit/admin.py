import json

from django.contrib import admin
from .models import AuditLog
from .redaction import sanitize_snapshot


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):

    list_display = (
        "timestamp",
        "severity",
        "model_name",
        "action",
        "user",
        "clinic",
        "ip_address",
    )

    list_filter = (
        "action",
        "model_name",
        "clinic",
        "timestamp",
    )

    search_fields = (
        "model_name",
        "object_id",
        "user__username",
    )

    readonly_fields = (
        "user",
        "clinic",
        "action",
        "model_name",
        "object_id",
        "before_data_safe",
        "after_data_safe",
        "ip_address",
        "timestamp",
    )

    ordering = ("-timestamp",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="before_data")
    def before_data_safe(self, obj):
        return self._render_payload(obj, obj.before_data)

    @admin.display(description="after_data")
    def after_data_safe(self, obj):
        return self._render_payload(obj, obj.after_data)

    @staticmethod
    def _render_payload(obj, raw):
        # Camada 2: mesmo politica da API, para o historico nao vazar
        # conteudo clinico/credenciais pela interface administrativa.
        payload = sanitize_snapshot(getattr(obj, "model_name", None), raw)
        if payload is None:
            return "-"
        return json.dumps(payload, ensure_ascii=False, indent=2, default=str)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # O SuperAdmin NÃO deve ver os logs operacionais das clínicas
        # Logs de clínicas possuem o campo `clinic` preenchido.
        # Logs da plataforma (ex: Criação de Clínicas, Criação de Usuários globais) tem `clinic=None`.
        return qs.filter(clinic__isnull=True)

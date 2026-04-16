from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):

    list_display = (
        "timestamp",
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
        "before_data",
        "after_data",
        "ip_address",
        "timestamp",
    )

    ordering = ("-timestamp",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
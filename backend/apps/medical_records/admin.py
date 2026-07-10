from django.contrib import admin
from .models import Prontuario, AdendoProntuario


@admin.register(Prontuario)
class ProntuarioAdmin(admin.ModelAdmin):
    readonly_fields = (
        "status",
        "finalizado_em",
        "finalizado_por",
    )

    def get_queryset(self, request):
        return super().get_queryset(request).none()

    def has_module_permission(self, request):
        return False
        
    def has_view_permission(self, request, obj=None):
        return False
        
    def has_add_permission(self, request):
        return False
        
    def has_change_permission(self, request, obj=None):
        return False
        
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AdendoProntuario)
class AdendoAdmin(admin.ModelAdmin):
    
    def get_queryset(self, request):
        return super().get_queryset(request).none()

    def has_module_permission(self, request):
        return False
        
    def has_view_permission(self, request, obj=None):
        return False
        
    def has_add_permission(self, request):
        return False
        
    def has_change_permission(self, request, obj=None):
        return False
        
    def has_delete_permission(self, request, obj=None):
        return False
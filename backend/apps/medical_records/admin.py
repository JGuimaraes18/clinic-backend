from django.contrib import admin
from .models import Prontuario, AdendoProntuario


@admin.register(Prontuario)
class ProntuarioAdmin(admin.ModelAdmin):
    readonly_fields = (
        "status",
        "finalizado_em",
        "finalizado_por",
    )


@admin.register(AdendoProntuario)
class AdendoAdmin(admin.ModelAdmin):
    pass
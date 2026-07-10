from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import Membership

User = get_user_model()


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    fields = ("clinic", "role", "is_active")


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "first_name", "last_name", "is_active", "is_staff", "date_joined")
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # SuperAdmin só pode ver outros SuperAdmins ou Staffs da plataforma.
        # NUNCA deve ver os usuários operacionais das clínicas.
        return qs.filter(is_superuser=True)

    def has_module_permission(self, request):
        return request.user.is_superuser

    # Campos para criação de usuário
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "password1", "password2"),
        }),
    )

    # Campos para edição de usuário
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Informações Pessoais", {"fields": ("first_name", "last_name")}),
        ("Permissões", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Datas", {"fields": ("last_login", "date_joined")}),
    )

    readonly_fields = ("date_joined", "last_login")

    inlines = [MembershipInline]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "clinic", "role", "is_active", "created_at")
    list_filter = ("role", "is_active")
    search_fields = ("user__email", "clinic__name")

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
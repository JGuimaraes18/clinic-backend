from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoginView, MeView, UserViewSet, RequestPasswordResetView, ResetPasswordConfirmView, ChangePasswordView, UpdateSettingsView

router = DefaultRouter()
router.register("users", UserViewSet, basename="users")

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path("me/settings/", UpdateSettingsView.as_view(), name="update_settings"),
    path("login/", LoginView.as_view()),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
    path("password-reset/request/", RequestPasswordResetView.as_view(), name="password_reset_request"),
    path("password-reset/confirm/", ResetPasswordConfirmView.as_view(), name="password_reset_confirm"),
    path("", include(router.urls)), 
]
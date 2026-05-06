from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoginView, MeView, UserViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="users")

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path("login/", LoginView.as_view()),
    path("", include(router.urls)), 
]
from apps.accounts.permissions import IsClinicAdminOrSuperuser
from apps.accounts.models import Membership
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.viewsets import ModelViewSet
from django.contrib.auth import get_user_model

from .serializers import (
    LoginSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    UserMeSerializer,
)

User = get_user_model()


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data["user"]
            clinic = serializer.validated_data.get("clinic")
            role = serializer.validated_data.get("role")

            refresh = RefreshToken.for_user(user)

            if user.is_superuser:
                refresh["role"] = "SUPERUSER"
                if clinic:
                    refresh["clinic_id"] = clinic.id
            else:
                refresh["clinic_id"] = clinic.id
                refresh["role"] = role

            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsClinicAdminOrSuperuser]

    def get_queryset(self):
        user = self.request.user

        # Superuser vê todos
        if user.is_superuser:
            return User.objects.all()

        clinic_id = self.request.auth.get("clinic_id")

        return User.objects.filter(
            memberships__clinic_id=clinic_id
        ).distinct()

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return UserMeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context
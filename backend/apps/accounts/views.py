from apps.accounts.permissions import IsAdminOrSuperuser
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.viewsets import ModelViewSet
from django.contrib.auth import get_user_model
from .serializers import LoginSerializer, UserCreateSerializer, UserUpdateSerializer
from .serializers import UserMeSerializer

User = get_user_model()

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data)

class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data["user"]
            refresh = RefreshToken.for_user(user)

            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    
    
class UserViewSet(ModelViewSet):
    serializer_class = UserMeSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperuser]

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return User.objects.all()

        return User.objects.filter(clinic=user.clinic)

    def perform_create(self, serializer):
        if self.request.user.is_superuser:
            serializer.save()
        else:
            serializer.save(clinic=self.request.user.clinic)

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserMeSerializer
    
    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return UserMeSerializer
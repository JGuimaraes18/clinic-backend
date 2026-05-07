from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework import serializers
from apps.clinics.models import Clinic

User = get_user_model()


class ClinicMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinic
        fields = ["id", "name"]


class UserMeSerializer(serializers.ModelSerializer):
    clinic = ClinicMiniSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "clinic",
            "is_superuser",
        ]


class LoginSerializer(serializers.Serializer):
    clinic_slug = serializers.CharField()
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        clinic_slug = data.get("clinic_slug")
        username = data.get("username")
        password = data.get("password")

        try:
            clinic = Clinic.objects.get(slug=clinic_slug)
        except Clinic.DoesNotExist:
            raise serializers.ValidationError("Clínica não encontrada.")

        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError("Usuário ou senha inválidos.")

        if not user.is_superuser and user.clinic != clinic:
            raise serializers.ValidationError(
                "Usuário não pertence a essa clínica."
            )

        data["user"] = user
        return data
    
class UserCreateSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "role",
            "clinic",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        clinic = validated_data.pop("clinic", None)

        user = User(**validated_data)
        user.set_password(password)

        request = self.context["request"]

        if request.user.is_superuser:
            # superuser pode escolher clinic
            user.clinic = clinic
        else:
            # admin só pode criar dentro da própria clínica
            user.clinic = request.user.clinic

        user.save()
        return user

class UserUpdateSerializer(serializers.ModelSerializer):

    clinic = serializers.PrimaryKeyRelatedField(
        queryset=Clinic.objects.all(),
        required=False,
        allow_null=True
    )

    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "clinic",
            "password",
        ]

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        clinic = validated_data.pop("clinic", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        request = self.context["request"]

        if request.user.is_superuser:
            instance.clinic = clinic

        if password:
            instance.set_password(password)

        instance.save()
        return instance    
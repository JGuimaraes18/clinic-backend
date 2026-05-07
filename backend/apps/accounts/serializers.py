from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework import serializers
from apps.clinics.models import Clinic
from apps.accounts.models import Membership

User = get_user_model()


class ClinicMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinic
        fields = ["id", "name", "slug"]


class UserMeSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    memberships = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_memberships(self, obj):
        memberships = obj.memberships.filter(is_active=True)

        return [
            {
                "clinic": {
                    "id": m.clinic.id,
                    "name": m.clinic.name,
                    "slug": m.clinic.slug,
                },
                "role": m.role,
            }
            for m in memberships
        ]

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "is_superuser",
            "memberships",
        ]


class LoginSerializer(serializers.Serializer):
    clinic_slug = serializers.CharField(required=False)
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")
        clinic_slug = data.get("clinic_slug")

        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError("Usuário ou senha inválidos.")

        if user.is_superuser:
            data["user"] = user
            return data

        if not clinic_slug:
            raise serializers.ValidationError("Clínica é obrigatória.")

        try:
            clinic = Clinic.objects.get(slug=clinic_slug)
        except Clinic.DoesNotExist:
            raise serializers.ValidationError("Clínica não encontrada.")

        membership = Membership.objects.filter(
            user=user,
            clinic=clinic,
            is_active=True
        ).first()

        if not membership:
            raise serializers.ValidationError(
                "Usuário não pertence a essa clínica."
            )

        data["user"] = user
        data["clinic"] = clinic
        data["role"] = membership.role

        return data


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    clinic_id = serializers.IntegerField(write_only=True, required=False)
    role = serializers.ChoiceField(
        choices=Membership.ROLE_CHOICES,
        write_only=True,
        required=False
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "clinic_id",
            "role",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        clinic_id = validated_data.pop("clinic_id", None)
        role = validated_data.pop("role", None)

        request = self.context["request"]

        # cria usuário
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        if request.user.is_superuser:
            if clinic_id and role:
                Membership.objects.create(
                    user=user,
                    clinic_id=clinic_id,
                    role=role,
                )

        else:
            # Admin só pode criar dentro da clínica ativa
            active_clinic_id = request.auth.get("clinic_id")

            Membership.objects.create(
                user=user,
                clinic_id=active_clinic_id,
                role=role,
            )

        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "password",
        ]

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from apps.clinics.models import Clinic
from apps.accounts.models import Membership

User = get_user_model()


class ClinicMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinic
        fields = ["id", "name", "slug"]


class MembershipSerializer(serializers.Serializer):
    clinic = ClinicMiniSerializer()
    role = serializers.CharField()


class UserMeSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    memberships = serializers.SerializerMethodField()
    settings = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_memberships(self, obj):
        memberships = obj.memberships.filter(is_active=True).select_related("clinic")

        return [
            {
                "clinic": {
                    "id": m.clinic.id,
                    "name": m.clinic.name,
                    "slug": m.clinic.slug,
                    "is_active": m.clinic.is_active,
                },
                "role": m.role,
            }
            for m in memberships
        ]
        
    def get_settings(self, obj):
        if hasattr(obj, "settings"):
            return {
                "theme": obj.settings.theme,
                "primary_color": obj.settings.primary_color,
                "density": obj.settings.density,
                "font_size": obj.settings.font_size,
                "extra_preferences": obj.settings.extra_preferences,
            }
        return {"theme": "system", "primary_color": "#0651ED", "density": "comfortable", "font_size": "medium", "extra_preferences": {}}

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "is_superuser",
            "force_password_change",
            "memberships",
            "settings",
        ]


class LoginSerializer(serializers.Serializer):
    clinic_slug = serializers.CharField(required=False)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")
        clinic_slug = data.get("clinic_slug")

        user = authenticate(email=email, password=password)

        if not user:
            raise serializers.ValidationError("Usuário ou senha inválidos.")
            
        if not user.is_active:
            raise serializers.ValidationError("Usuário inativo.")

        if user.is_superuser:
            data["user"] = user
            data["role"] = "SUPERUSER"
            # Superadmin loga apenas na plataforma, NUNCA em uma clínica específica.
            data["clinic"] = None 
            return data

        if not clinic_slug:
            raise serializers.ValidationError("Clínica é obrigatória.")

        try:
            clinic = Clinic.objects.get(slug=clinic_slug)
        except Clinic.DoesNotExist:
            raise serializers.ValidationError("Clínica não encontrada.")
            
        if not clinic.is_active:
            raise serializers.ValidationError("Esta clínica está desativada. Entre em contato com o suporte.")

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
            "email",
            "first_name",
            "last_name",
            "password",
            "clinic_id",
            "role",
        ]

    def validate(self, attrs):
        role = attrs.get("role")
        email = attrs.get("email")
        if role == "ADMIN":
            user = User.objects.filter(email=email).first()
            if user:
                existing = Membership.objects.filter(user=user, is_active=True)
                if existing.exists():
                    raise serializers.ValidationError(
                        {"role": "Um administrador de clínica não pode estar associado a outra clínica."}
                    )
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        clinic_id = validated_data.pop("clinic_id", None)
        role = validated_data.pop("role", None)

        request = self.context["request"]

        with transaction.atomic():
            user = User.objects.create_user(
                password=password,
                **validated_data
            )

            if request.user.is_superuser:
                if not clinic_id:
                    raise serializers.ValidationError("A clínica (clinic_id) é obrigatória para o SuperAdmin cadastrar um usuário.")
            else:
                clinic_id = request.auth.get("clinic_id") if request.auth else None
                if not clinic_id:
                    raise serializers.ValidationError("Não foi possível identificar a clínica ativa.")

            from apps.clinics.models import Clinic
            try:
                clinic = Clinic.objects.get(id=clinic_id)
                if not clinic.is_active:
                    raise serializers.ValidationError("Esta clínica está desativada.")
            except Clinic.DoesNotExist:
                raise serializers.ValidationError("Clínica não encontrada.")

            try:
                Membership.objects.create(
                    user=user,
                    clinic_id=clinic_id,
                    role=role or "ATTENDANT",
                )
            except DjangoValidationError as exc:
                raise serializers.ValidationError(exc.messages)

        # Sem atomic acima, um erro de negocio depois de create_user()
        # deixaria um usuario orfao (sem membership) persistido no banco.
        return user



class UserUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    role = serializers.ChoiceField(
        choices=Membership.ROLE_CHOICES,
        required=False,
        write_only=True
    )
    clinic_id = serializers.IntegerField(
        required=False,
        write_only=True
    )

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "password",
            "role",
            "clinic_id",
        ]

    def validate(self, attrs):
        role = attrs.get("role")
        clinic_id = attrs.get("clinic_id")
        if role == "ADMIN" and self.instance:
            existing = Membership.objects.filter(user=self.instance, is_active=True)
            if not clinic_id:
                active_membership = self.instance.memberships.filter(is_active=True).first()
                clinic_id = active_membership.clinic_id if active_membership else None
            
            other_memberships = existing.exclude(clinic_id=clinic_id)
            if other_memberships.exists():
                raise serializers.ValidationError(
                    {"role": "Um administrador de clínica não pode estar associado a outra clínica."}
                )
        return attrs

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        role = validated_data.pop("role", None)
        clinic_id = validated_data.pop("clinic_id", None)

        request = self.context["request"]

        try:
            with transaction.atomic():
                for attr, value in validated_data.items():
                    setattr(instance, attr, value)

                if password:
                    instance.set_password(password)

                instance.save()

                # Update or create membership
                if request.user.is_superuser:
                    membership = instance.memberships.first()
                    if membership:
                        if clinic_id:
                            membership.clinic_id = clinic_id
                        if role:
                            membership.role = role
                        membership.save()
                    else:
                        if clinic_id:
                            Membership.objects.create(
                                user=instance,
                                clinic_id=clinic_id,
                                role=role or "ADMIN"
                            )
                else:
                    membership = instance.memberships.filter(is_active=True).first()
                    if role and membership:
                        membership.role = role
                    if membership:
                        membership.save()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)

        return instance
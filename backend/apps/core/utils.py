from rest_framework import serializers

from apps.clinics.models import Clinic


def resolve_user_clinic(context):
    """
    Resolve a clínica ativa a partir do token JWT no contexto do serializer.

    Unica implementacao da regra (antes duplicada em patients, appointments
    e professionals). Retorna None somente para superuser autenticado sem
    clinic_id no token; caso contrario levanta ValidationError.
    """
    request = context["request"]
    clinic_id = request.auth.get("clinic_id") if request.auth else None

    if request.user.is_superuser and not clinic_id:
        return None

    if not clinic_id:
        raise serializers.ValidationError("Usuário sem clínica ativa.")

    try:
        return Clinic.objects.get(id=clinic_id)
    except Clinic.DoesNotExist:
        raise serializers.ValidationError("Clínica não encontrada.")

"""
Testes do Lote 5A - regra unica de resolucao de clínica a partir do JWT.

apps.core.utils.resolve_user_clinic() e a extracao do que antes estava
duplicado em PatientSerializer, AppointmentSerializer e
ProfessionalSerializer. Estes testes fixam a regra para que a
remocao das copias seja uma mudanca segura.

Executar somente em banco de teste isolado:

    python manage.py test apps.core.tests
"""

from types import SimpleNamespace

from django.test import TestCase

from apps.accounts.models import Membership
from apps.clinics.models import Clinic
from apps.core.utils import resolve_user_clinic
from rest_framework import serializers


def _context(user, clinic_id=None):
    request = SimpleNamespace(user=user, auth={"clinic_id": clinic_id})
    return {"request": request}


class ResolveUserClinicTestCase(TestCase):
    def setUp(self):
        self.clinic = Clinic.objects.create(
            name="Clinica Core",
            document="77665544000133",
            phone="11999990007",
            email="core@clinica.test",
        )
        self.admin_user = SimpleNamespace(
            id=1, is_superuser=False, email="admin@clinica.test"
        )

    def test_retorna_clinic_valida_do_token(self):
        result = resolve_user_clinic(_context(self.admin_user, self.clinic.id))
        self.assertEqual(result, self.clinic)

    def test_levanta_erro_quando_token_sem_clinic_id(self):
        with self.assertRaises(serializers.ValidationError):
            resolve_user_clinic(_context(self.admin_user, None))

    def test_levanta_erro_quando_clinic_do_token_nao_existe(self):
        with self.assertRaises(serializers.ValidationError):
            resolve_user_clinic(_context(self.admin_user, 999999))

    def test_superuser_sem_clinic_no_token_retorna_none(self):
        # Comportamento preservado da implementacao original: um superuser
        # da plataforma pode serializar sem clínica de contexto.
        superuser = SimpleNamespace(
            id=2, is_superuser=True, email="super@plataforma.test"
        )
        self.assertIsNone(resolve_user_clinic(_context(superuser, None)))

    def test_superuser_com_clinic_no_token_retorna_clinic(self):
        superuser = SimpleNamespace(
            id=2, is_superuser=True, email="super@plataforma.test"
        )
        result = resolve_user_clinic(_context(superuser, self.clinic.id))
        self.assertEqual(result, self.clinic)


class ResolveUserClinicNosSerializersTestCase(TestCase):
    """Os tres serializers delegam a mesma funcao (regressao do DRY)."""

    def setUp(self):
        from apps.appointments.serializers import AtendimentoSerializer
        from apps.patients.serializers import PatientSerializer
        from apps.professionals.serializers import ProfessionalSerializer

        self.clinic = Clinic.objects.create(
            name="Clinica DRY",
            document="11223344000166",
            phone="11999990008",
            email="dry@clinica.test",
        )
        self.user = SimpleNamespace(id=3, is_superuser=False, email="u@t.test")
        self.serializer_classes = (
            PatientSerializer,
            AtendimentoSerializer,
            ProfessionalSerializer,
        )

    def test_todos_delegam_para_resolve_user_clinic(self):
        context = _context(self.user, self.clinic.id)
        for serializer_class in self.serializer_classes:
            with self.subTest(serializer=serializer_class.__name__):
                serializer = serializer_class(context=context)
                self.assertEqual(serializer.get_user_clinic(), self.clinic)

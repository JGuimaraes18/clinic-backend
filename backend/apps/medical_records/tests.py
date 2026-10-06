"""
Testes do Lote 5A - regra unica de acesso ao conteudo clinico.

Cobrem as correcoes aplicadas em apps/medical_records:

  * can_view_conteudo() com atendimento sem profissional (profissional
    opcional) deixa de levantar AttributeError -> 500;
  * a mascara de conteudo continua valendo para todos os casos que
    valiam antes (mesma regra, agora em um unico lugar);
  * POST /api/medical-records/ devolve 400 (nao 500) quando quem cria
    nao e o profissional responsavel.

Executar somente em banco de teste isolado:

    python manage.py test apps.medical_records.tests
"""

from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Membership
from apps.appointments.models import Atendimento
from apps.clinics.models import Clinic
from apps.medical_records.models import AdendoProntuario, Prontuario
from apps.medical_records.serializers import (
    RESTRITO,
    AdendoProntuarioSerializer,
    ProntuarioSerializer,
    can_view_conteudo,
)
from apps.patients.models import Patient
from apps.professionals.models import Professional

User = get_user_model()

CONTEUDO_MARCA = "CONTEUDO_CLINICO_L5A_9f31"
SENHA = "SenhaForte!123"


def _request(user, clinic_id=None):
    """Request de fachada com o minimo que os serializers leem."""
    auth = {"clinic_id": clinic_id, "role": "PROFESSIONAL"} if clinic_id else None
    return SimpleNamespace(user=user, auth=auth)


class CanViewConteudoTestCase(TestCase):
    """Unica fonte da regra 'quem enxerga o conteudo clinico'."""

    def setUp(self):
        self.clinic = Clinic.objects.create(
            name="Clinica Mascara",
            document="11222333000181",
            phone="11999990001",
            email="mascara@clinica.test",
        )
        self.owner_user = User.objects.create_user(
            email="dono@clinica.test",
            password=SENHA,
            first_name="Dona",
            last_name="Do Prontuario",
        )
        self.owner = Professional.objects.create(
            user=self.owner_user,
            registration_type="CRM",
            registration_number="11111",
        )
        self.other_user = User.objects.create_user(
            email="outra@clinica.test",
            password=SENHA,
            first_name="Outra",
            last_name="Pessoa",
        )
        self.paciente = Patient.objects.create(
            clinic=self.clinic,
            full_name="Paciente Mascara",
            cpf="12345678900",
            phone="11999990002",
        )
        self.atendimento = Atendimento.objects.create(
            clinic=self.clinic,
            paciente=self.paciente,
            profissional=self.owner,
            data_hora=timezone.now(),
        )
        self.atendimento_sem_profissional = Atendimento.objects.create(
            clinic=self.clinic,
            paciente=self.paciente,
            profissional=None,
            data_hora=timezone.now() + timezone.timedelta(hours=1),
        )

    def test_profissional_null_retorna_false_sem_levantar_erro(self):
        # Regressao: antes this linha era `atendimento.profissional.user`
        # e quebrava com AttributeError quando profissional e opcional.
        self.assertFalse(
            can_view_conteudo(self.owner_user, self.atendimento_sem_profissional)
        )

    def test_responsavel_enxerga_conteudo(self):
        self.assertTrue(can_view_conteudo(self.owner_user, self.atendimento))

    def test_terceiro_nao_enxerga_conteudo(self):
        self.assertFalse(can_view_conteudo(self.other_user, self.atendimento))

    def test_sem_usuario_nao_enxerga_conteudo(self):
        self.assertFalse(can_view_conteudo(None, self.atendimento))

    def test_usuario_sem_id_nao_enxerga_conteudo(self):
        anonimo = SimpleNamespace(id=None)
        self.assertFalse(can_view_conteudo(anonimo, self.atendimento))

    def test_atendimento_sem_profissional_sem_usuario_nao_quebra(self):
        self.assertFalse(can_view_conteudo(None, self.atendimento_sem_profissional))


class MascaramentoSerializerTestCase(TestCase):
    """ProntuarioSerializer/AdendoProntuarioSerializer usam a mesma regra."""

    def setUp(self):
        self.clinic = Clinic.objects.create(
            name="Clinica Serial",
            document="99887766000155",
            phone="11999990003",
            email="serial@clinica.test",
        )
        self.owner_user = User.objects.create_user(
            email="medico@clinica.test",
            password=SENHA,
            first_name="Medico",
            last_name="Responsavel",
        )
        self.owner = Professional.objects.create(
            user=self.owner_user,
            registration_type="CRM",
            registration_number="22222",
        )
        self.admin_user = User.objects.create_user(
            email="admin@clinica.test",
            password=SENHA,
            first_name="Admin",
            last_name="Da Clinica",
        )
        Membership.objects.create(
            user=self.admin_user, clinic=self.clinic, role="ADMIN"
        )
        self.paciente = Patient.objects.create(
            clinic=self.clinic,
            full_name="Paciente Serial",
            cpf="12345678901",
            phone="11999990004",
        )
        self.atendimento = Atendimento.objects.create(
            clinic=self.clinic,
            paciente=self.paciente,
            profissional=self.owner,
            data_hora=timezone.now(),
        )
        self.prontuario = Prontuario.objects.create(
            atendimento=self.atendimento,
            conteudo=CONTEUDO_MARCA,
        )

    def _data(self, serializer_class, obj, user):
        serializer = serializer_class(
            obj, context={"request": _request(user, self.clinic.id)}
        )
        return serializer.to_representation(obj)

    def test_responsavel_recebe_conteudo_real(self):
        data = self._data(ProntuarioSerializer, self.prontuario, self.owner_user)
        self.assertEqual(data["conteudo"], CONTEUDO_MARCA)

    def test_admin_da_clinica_recebe_mascara(self):
        # Mesma regra de antes: admin NAO ve o conteudo clinico.
        data = self._data(ProntuarioSerializer, self.prontuario, self.admin_user)
        self.assertEqual(data["conteudo"], RESTRITO)
        self.assertNotIn(CONTEUDO_MARCA, data["conteudo"])

    def test_prontuario_sem_profissional_e_mascarado_em_quebra(self):
        atendimento = Atendimento.objects.create(
            clinic=self.clinic,
            paciente=self.paciente,
            profissional=None,
            data_hora=timezone.now() + timezone.timedelta(hours=2),
        )
        prontuario = Prontuario.objects.create(
            atendimento=atendimento, conteudo=CONTEUDO_MARCA
        )

        data = self._data(ProntuarioSerializer, prontuario, self.owner_user)
        self.assertEqual(data["conteudo"], RESTRITO)

    def test_adendo_sem_profissional_e_mascarado_sem_quebrar(self):
        atendimento = Atendimento.objects.create(
            clinic=self.clinic,
            paciente=self.paciente,
            profissional=None,
            data_hora=timezone.now() + timezone.timedelta(hours=3),
        )
        prontuario = Prontuario.objects.create(
            atendimento=atendimento, conteudo=CONTEUDO_MARCA
        )
        adendo = AdendoProntuario.objects.create(
            prontuario=prontuario,
            conteudo=CONTEUDO_MARCA,
            criado_por=self.admin_user,
        )

        data = self._data(AdendoProntuarioSerializer, adendo, self.owner_user)
        self.assertEqual(data["conteudo"], RESTRITO)

    def test_adendo_do_responsavel_recebe_conteudo_real(self):
        adendo = AdendoProntuario.objects.create(
            prontuario=self.prontuario,
            conteudo=CONTEUDO_MARCA,
            criado_por=self.admin_user,
        )

        data = self._data(AdendoProntuarioSerializer, adendo, self.owner_user)
        self.assertEqual(data["conteudo"], CONTEUDO_MARCA)


class CriacaoProntuarioViaAPITestCase(TestCase):
    """POST /api/medical-records/ devolve 400 (nao 500) para nao responsavel."""

    def setUp(self):
        self.clinic = Clinic.objects.create(
            name="Clinica Api",
            document="44556677000199",
            phone="11999990005",
            email="api@clinica.test",
        )
        self.owner_user = User.objects.create_user(
            email="medico.api@clinica.test",
            password=SENHA,
            first_name="Medico",
            last_name="Api",
        )
        Membership.objects.create(
            user=self.owner_user, clinic=self.clinic, role="PROFESSIONAL"
        )
        self.owner = Professional.objects.create(
            user=self.owner_user,
            registration_type="CRM",
            registration_number="33333",
        )

        self.other_user = User.objects.create_user(
            email="outra.api@clinica.test",
            password=SENHA,
            first_name="Outro",
            last_name="Profissional",
        )
        Membership.objects.create(
            user=self.other_user, clinic=self.clinic, role="PROFESSIONAL"
        )
        self.other = Professional.objects.create(
            user=self.other_user,
            registration_type="CRM",
            registration_number="44444",
        )

        self.paciente = Patient.objects.create(
            clinic=self.clinic,
            full_name="Paciente Api",
            cpf="12345678902",
            phone="11999990006",
        )
        self.atendimento = Atendimento.objects.create(
            clinic=self.clinic,
            paciente=self.paciente,
            profissional=self.owner,
            data_hora=timezone.now(),
        )
        self.atendimento_sem_profissional = Atendimento.objects.create(
            clinic=self.clinic,
            paciente=self.paciente,
            profissional=None,
            data_hora=timezone.now() + timezone.timedelta(hours=4),
        )

        self.owner_client = self._login("medico.api@clinica.test")
        self.other_client = self._login("outra.api@clinica.test")

    def _login(self, email):
        client = APIClient()
        response = client.post(
            "/api/auth/login/",
            {
                "email": email,
                "password": SENHA,
                "clinic_slug": self.clinic.slug,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.json()['access']}"
        )
        return client

    def _payload(self, atendimento):
        return {"atendimento": atendimento.id, "conteudo": CONTEUDO_MARCA}

    def test_responsavel_cria_prontuario(self):
        response = self.owner_client.post(
            "/api/medical-records/",
            self._payload(self.atendimento),
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)

    def test_nao_responsavel_recebe_400_e_nao_500(self):
        response = self.other_client.post(
            "/api/medical-records/",
            self._payload(self.atendimento),
            format="json",
        )
        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("responsável", response.content.decode("utf-8"))

    def test_atendimento_sem_profissional_recebe_400_e_nao_500(self):
        # Regressao: `appointment.profissional.user` explodia com
        # AttributeError e o DRF devolvia 500.
        response = self.other_client.post(
            "/api/medical-records/",
            self._payload(self.atendimento_sem_profissional),
            format="json",
        )
        self.assertEqual(response.status_code, 400, response.content)
        self.assertNotEqual(response.status_code, 500)

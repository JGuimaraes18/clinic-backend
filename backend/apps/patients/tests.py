"""
Testes do Lote 5A - PatientSerializer apos extracao de get_user_clinic.

Regressao de tenant: a atribuicao de clinic continua vindo do token JWT
mesmo depois de a regra ter sido movida de apps.patients para
apps.core.utils.resolve_user_clinic.

Executar somente em banco de teste isolado:

    python manage.py test apps.patients.tests
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Membership
from apps.clinics.models import Clinic
from apps.patients.models import Patient

User = get_user_model()

SENHA = "SenhaForte!123"


class PatientClinicFromTokenTestCase(TestCase):
    def setUp(self):
        self.clinic_a = Clinic.objects.create(
            name="Clinica A",
            document="11222333000182",
            phone="11999990010",
            email="a@clinica.test",
        )
        self.clinic_b = Clinic.objects.create(
            name="Clinica B",
            document="11222333000183",
            phone="11999990011",
            email="b@clinica.test",
        )

        self.admin_a = User.objects.create_user(
            email="admin.a@clinica.test",
            password=SENHA,
            first_name="Admin",
            last_name="A",
        )
        Membership.objects.create(
            user=self.admin_a, clinic=self.clinic_a, role="ADMIN"
        )

        self.admin_b = User.objects.create_user(
            email="admin.b@clinica.test",
            password=SENHA,
            first_name="Admin",
            last_name="B",
        )
        Membership.objects.create(
            user=self.admin_b, clinic=self.clinic_b, role="ADMIN"
        )

        self.pro_a = User.objects.create_user(
            email="pro.a@clinica.test",
            password=SENHA,
            first_name="Pro",
            last_name="A",
        )
        Membership.objects.create(
            user=self.pro_a, clinic=self.clinic_a, role="PROFESSIONAL"
        )

    def _login(self, email, clinic_slug):
        client = APIClient()
        response = client.post(
            "/api/auth/login/",
            {"email": email, "password": SENHA, "clinic_slug": clinic_slug},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.json()['access']}"
        )
        return client

    def _payload(self, cpf="11122233344"):
        return {
            "full_name": "Paciente L5A",
            "cpf": cpf,
            "phone": "11999990012",
        }

    def test_criacao_atribui_clinic_do_token(self):
        client = self._login("admin.a@clinica.test", self.clinic_a.slug)

        response = client.post("/api/patients/", self._payload(), format="json")

        self.assertEqual(response.status_code, 201, response.content)
        patient = Patient.objects.get(id=response.json()["id"])
        self.assertEqual(patient.clinic_id, self.clinic_a.id)

    def test_cpf_duplicado_na_mesma_clinic_continua_bloqueado(self):
        client_a = self._login("admin.a@clinica.test", self.clinic_a.slug)
        first = client_a.post("/api/patients/", self._payload(), format="json")
        self.assertEqual(first.status_code, 201, first.content)

        second = client_a.post("/api/patients/", self._payload(), format="json")
        self.assertEqual(second.status_code, 400, second.content)
        self.assertIn("CPF already registered", second.content.decode("utf-8"))

    def test_cpf_repetido_em_outra_clinic_e_permitido(self):
        client_a = self._login("admin.a@clinica.test", self.clinic_a.slug)
        client_b = self._login("admin.b@clinica.test", self.clinic_b.slug)

        first = client_a.post("/api/patients/", self._payload(), format="json")
        second = client_b.post("/api/patients/", self._payload(), format="json")

        self.assertEqual(first.status_code, 201, first.content)
        self.assertEqual(second.status_code, 201, second.content)
        self.assertEqual(
            Patient.objects.filter(cpf_hash=Patient().generate_cpf_hash("11122233344")).count(),
            2,
        )

    def test_listagem_nao_exibe_pacientes_de_outra_clinic(self):
        client_a = self._login("admin.a@clinica.test", self.clinic_a.slug)
        client_b = self._login("admin.b@clinica.test", self.clinic_b.slug)
        client_a.post("/api/patients/", self._payload(), format="json")

        response = client_b.get("/api/patients/")

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json(), [])

    def test_profissional_nao_cria_paciente(self):
        client = self._login("pro.a@clinica.test", self.clinic_a.slug)

        response = client.post("/api/patients/", self._payload(), format="json")

        self.assertEqual(response.status_code, 403, response.content)

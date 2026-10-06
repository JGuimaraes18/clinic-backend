"""
Testes de PatientSerializer.

1) Lote 5A - regressao de tenant: a atribuicao de clinic continua vindo do
   token JWT mesmo depois de a regra ter sido movida de apps.patients para
   apps.core.utils.resolve_user_clinic.

2) B6 - protecao de CPF/RG: `cpf`, `document` e `cpf_hash` deixaram de ser
   devolvidos pela API, continuando aceitos no input e persistidos no banco.

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

# Campos que NUNCA podem aparecer em nenhuma resposta de /api/patients/.
CAMPOS_PROIBIDOS = {"cpf", "document", "cpf_hash"}

# Marcadores de valor: se aparecerem no corpo bruto, ha vazamento mesmo
# que a chave tenha sido renomeada.
CPF_MARCA = "98765432100"
CPF_NOVO_MARCA = "12345678900"
CPF_EDITADO_MARCA = "55566677788"
RG_MARCA = "MG-987654"


def _encontrar_proibidos(node, path=""):
    """Varre a estrutura JSON e devolve o caminho de cada campo proibido."""
    achados = []
    if isinstance(node, dict):
        for key, value in node.items():
            atual = f"{path}.{key}" if path else str(key)
            if str(key).strip().lower() in CAMPOS_PROIBIDOS:
                achados.append(atual)
            achados.extend(_encontrar_proibidos(value, atual))
    elif isinstance(node, (list, tuple)):
        for index, item in enumerate(node):
            achados.extend(_encontrar_proibidos(item, f"{path}[{index}]"))
    return achados


class PatientSensitiveDataContractTestCase(TestCase):
    """Contrato B6: CPF/document/cpf_hash nao sao expostos pela API."""

    def setUp(self):
        self.clinic = Clinic.objects.create(
            name="Clinica B6",
            document="99887766000144",
            phone="11999990020",
            email="b6@clinica.test",
        )
        self.admin = User.objects.create_user(
            email="admin.b6@clinica.test",
            password=SENHA,
            first_name="Admin",
            last_name="B6",
        )
        Membership.objects.create(
            user=self.admin, clinic=self.clinic, role="ADMIN"
        )
        self.client_a = self._login("admin.b6@clinica.test")

        self.paciente = Patient.objects.create(
            clinic=self.clinic,
            full_name="Paciente B6",
            cpf=CPF_MARCA,
            document=RG_MARCA,
            phone="11999990021",
        )

    def _login(self, email):
        client = APIClient()
        response = client.post(
            "/api/auth/login/",
            {"email": email, "password": SENHA, "clinic_slug": self.clinic.slug},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.json()['access']}"
        )
        return client

    def _assert_sem_vazamento(self, response):
        """Nenhum campo proibido e nenhum valor proibido em nenhuma resposta."""
        body = response.content.decode("utf-8")
        self.assertEqual(_encontrar_proibidos(response.json()), [])
        for marcador in (CPF_MARCA, CPF_NOVO_MARCA, CPF_EDITADO_MARCA, RG_MARCA):
            self.assertNotIn(marcador, body)
        self.assertNotIn("cpf_hash", body)

    def _payload(self, cpf=CPF_NOVO_MARCA, **extra):
        payload = {
            "full_name": "Paciente Criado pelo B6",
            "cpf": cpf,
            "document": RG_MARCA,
            "phone": "11999990022",
            "birth_date": "1990-04-12",
        }
        payload.update(extra)
        return payload

    # ------------------------------------------------------------------ GET

    def test_get_list_nao_expoe_cpf_document_cpf_hash(self):
        response = self.client_a.get("/api/patients/")

        self.assertEqual(response.status_code, 200, response.content)
        self._assert_sem_vazamento(response)

        item = response.json()[0]
        self.assertEqual(item["full_name"], "Paciente B6")
        self.assertIn("phone", item)
        self.assertIn("birth_date", item)
        self.assertIn("clinic", item)
        self.assertNotIn("cpf", item)
        self.assertNotIn("document", item)
        self.assertNotIn("cpf_hash", item)

    def test_get_detail_nao_expoe_cpf_document_cpf_hash(self):
        response = self.client_a.get(f"/api/patients/{self.paciente.id}/")

        self.assertEqual(response.status_code, 200, response.content)
        self._assert_sem_vazamento(response)

    # ----------------------------------------------------------------- POST

    def test_post_aceita_cpf_e_document_mas_nao_devolve(self):
        response = self.client_a.post(
            "/api/patients/", self._payload(), format="json"
        )

        self.assertEqual(response.status_code, 201, response.content)
        self._assert_sem_vazamento(response)
        self.assertIn("id", response.json())
        self.assertEqual(response.json()["full_name"], "Paciente Criado pelo B6")

    def test_post_persiste_cpf_document_e_cpf_hash_internamente(self):
        response = self.client_a.post(
            "/api/patients/", self._payload(), format="json"
        )
        self.assertEqual(response.status_code, 201, response.content)

        paciente = Patient.objects.get(id=response.json()["id"])
        # criptografado em repouso, descriptografado na leitura do model
        self.assertEqual(paciente.cpf, CPF_NOVO_MARCA)
        self.assertEqual(paciente.document, RG_MARCA)
        # hash continua sendo calculado e persistido pelo model.save()
        self.assertEqual(
            paciente.cpf_hash,
            Patient().generate_cpf_hash(CPF_NOVO_MARCA),
        )

    def test_unicidade_de_cpf_continua_funcionando_apos_post(self):
        first = self.client_a.post(
            "/api/patients/", self._payload(), format="json"
        )
        self.assertEqual(first.status_code, 201, first.content)

        second = self.client_a.post(
            "/api/patients/", self._payload(), format="json"
        )
        self.assertEqual(second.status_code, 400, second.content)
        self.assertIn(
            "CPF already registered", second.content.decode("utf-8")
        )

    # --------------------------------------------------------------- PUT/PATCH

    def test_put_atualiza_cpf_document_sem_devolver_em_claro(self):
        novo = self._payload(cpf=CPF_EDITADO_MARCA, full_name="Paciente Editado")

        response = self.client_a.put(
            f"/api/patients/{self.paciente.id}/", novo, format="json"
        )

        self.assertEqual(response.status_code, 200, response.content)
        self._assert_sem_vazamento(response)
        self.assertEqual(response.json()["full_name"], "Paciente Editado")

        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.cpf, CPF_EDITADO_MARCA)
        self.assertEqual(self.paciente.document, RG_MARCA)
        self.assertEqual(
            self.paciente.cpf_hash,
            Patient().generate_cpf_hash(CPF_EDITADO_MARCA),
        )

    def test_put_sem_cpf_preserva_o_cpf_cadastrado(self):
        """Contrato input/output: ausencia de `cpf` nao apaga o valor."""
        payload = {
            "full_name": "Paciente Renomeado",
            "phone": "11999990023",
            "birth_date": "1990-04-12",
        }

        response = self.client_a.put(
            f"/api/patients/{self.paciente.id}/", payload, format="json"
        )

        self.assertEqual(response.status_code, 200, response.content)
        self._assert_sem_vazamento(response)

        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.full_name, "Paciente Renomeado")
        self.assertEqual(self.paciente.cpf, CPF_MARCA)
        self.assertEqual(
            self.paciente.cpf_hash,
            Patient().generate_cpf_hash(CPF_MARCA),
        )

    def test_patch_parcial_preserva_cpf_e_atualiza_telefone(self):
        response = self.client_a.patch(
            f"/api/patients/{self.paciente.id}/",
            {"phone": "11999990024"},
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.content)
        self._assert_sem_vazamento(response)

        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.phone, "11999990024")
        self.assertEqual(self.paciente.cpf, CPF_MARCA)

    # --------------------------------------------------------------- cpf_hash

    def test_cpf_hash_e_interno_e_nunca_sai_pela_api(self):
        self.assertTrue(self.paciente.cpf_hash)

        lista = self.client_a.get("/api/patients/")
        detalhe = self.client_a.get(f"/api/patients/{self.paciente.id}/")
        criado = self.client_a.post(
            "/api/patients/", self._payload(), format="json"
        )

        for response in (lista, detalhe, criado):
            self.assertNotIn("cpf_hash", response.content.decode("utf-8"))
            self.assertNotIn(self.paciente.cpf_hash, response.content.decode("utf-8"))

        # e continua util internamente para unicidade por clinica
        self.assertEqual(
            Patient.all_objects.filter(
                clinic=self.clinic, cpf_hash=self.paciente.cpf_hash
            ).count(),
            1,
        )

    def test_campos_sensiveis_nao_aparecem_em_nenhuma_rota_de_paciente(self):
        for method, url, payload in (
            ("get", "/api/patients/", None),
            ("get", f"/api/patients/{self.paciente.id}/", None),
            ("post", "/api/patients/", self._payload()),
            (
                "put",
                f"/api/patients/{self.paciente.id}/",
                self._payload(cpf=CPF_EDITADO_MARCA),
            ),
            (
                "patch",
                f"/api/patients/{self.paciente.id}/",
                {"phone": "11999990025"},
            ),
        ):
            with self.subTest(method=method, url=url):
                call = getattr(self.client_a, method)
                response = (
                    call(url, payload, format="json")
                    if payload is not None
                    else call(url)
                )
                self.assertIn(response.status_code, (200, 201))
                self.assertEqual(_encontrar_proibidos(response.json()), [])
                self.assertNotIn("cpf_hash", response.content.decode("utf-8"))


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

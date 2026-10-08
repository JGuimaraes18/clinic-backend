"""
Testes do Lote 7 - consistencia da API e regras de negocio.

Executar somente em banco de teste isolado:

    python manage.py test apps.accounts

Nenhum teste escreve no banco de desenvolvimento: o TestCase do Django
cria um banco `test_*`, roda tudo dentro de transacao e destroi o banco
ao final da execucao.
"""

from unittest import mock

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Membership
from apps.audit.models import AuditLog
from apps.clinics.models import Clinic
from core.middleware import _user as _current_actor, set_current_ip

User = get_user_model()

SENHA = "SenhaTesteL7!123"


def _clear_actor():
    _current_actor.value = None
    set_current_ip(None)


class BaseAccountsTestCase(TestCase):
    def setUp(self):
        super().setUp()
        _clear_actor()

        self.superuser = User.objects.create_superuser(
            email="super@plataforma.test",
            password=SENHA,
            first_name="Super",
            last_name="Admin",
        )
        self.clinic_a = Clinic.objects.create(
            name="Clinica A",
            document="11111111000111",
            phone="11999990001",
            email="a@clinica.test",
        )
        self.clinic_b = Clinic.objects.create(
            name="Clinica B",
            document="22222222000122",
            phone="11999990002",
            email="b@clinica.test",
        )

    def _create_user(
        self,
        email,
        clinic,
        role="ATTENDANT",
        is_active=True,
        force_password_change=False,
    ):
        user = User.objects.create_user(
            email=email,
            password=SENHA,
            first_name=email.split("@")[0],
            force_password_change=force_password_change,
        )
        Membership.objects.create(
            user=user,
            clinic=clinic,
            role=role,
            is_active=is_active,
        )
        return user

    def _login(self, email, password=SENHA, clinic_slug=None):
        client = APIClient()
        payload = {"email": email, "password": password}
        if clinic_slug:
            payload["clinic_slug"] = clinic_slug
        response = client.post("/api/auth/login/", payload, format="json")
        self.assertEqual(response.status_code, 200, response.content)
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.json()['access']}"
        )
        return client


class RotasPublicasExemptTestCase(BaseAccountsTestCase):
    """Rotas publicas (AllowAny) nao podem ser bloqueadas pelo
    ForcePasswordChangeMiddleware, mesmo com JWT valido de um usuario que
    ainda precisa trocar a senha."""

    ROTAS_PUBLICAS = [
        "/api/auth/login/",
        "/api/auth/password-reset/request/",
        "/api/auth/password-reset/confirm/",
        "/api/auth/token/refresh/",
    ]

    def setUp(self):
        super().setUp()
        self._create_user(
            "pendente@a.test",
            self.clinic_a,
            force_password_change=True,
        )
        self.client_pendente = self._login(
            "pendente@a.test", clinic_slug=self.clinic_a.slug
        )

    def test_rotas_publicas_nao_retornam_403_password_required(self):
        for url in self.ROTAS_PUBLICAS:
            with self.subTest(url=url):
                response = self.client_pendente.post(url, {}, format="json")
                self.assertNotEqual(
                    response.status_code,
                    403,
                    f"{url} deve ser exempt (AllowAny), nao bloqueada com 403.",
                )

    def test_rota_autenticada_continua_bloqueada(self):
        response = self.client_pendente.get("/api/patients/")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json().get("code"), "password_change_required"
        )


class IsolamentoMembrosAtivosTestCase(BaseAccountsTestCase):
    """A listagem de usuarios de uma clínica deve isolar apenas membros
    ATIVOS da propria clínica; o superuser continua vendo a plataforma."""

    def setUp(self):
        super().setUp()
        self.admin_a = self._create_user(
            "admina@a.test", self.clinic_a, role="ADMIN"
        )
        self._create_user("ativo@a.test", self.clinic_a, role="ATTENDANT")
        self._create_user(
            "inativo@a.test",
            self.clinic_a,
            role="ATTENDANT",
            is_active=False,
        )
        self._create_user("ativob@b.test", self.clinic_b, role="ATTENDANT")

        self.client_admin = self._login(
            "admina@a.test", clinic_slug=self.clinic_a.slug
        )
        self.client_super = self._login("super@plataforma.test")

    def test_admin_clinica_lista_apenas_membros_ativos_da_propria_clinica(self):
        response = self.client_admin.get("/api/auth/users/")
        self.assertEqual(response.status_code, 200)
        emails = {item["email"] for item in response.json()}
        self.assertEqual(emails, {"admina@a.test", "ativo@a.test"})

    def test_superuser_enxerga_todos_os_membros_da_plataforma(self):
        response = self.client_super.get("/api/auth/users/")
        self.assertEqual(response.status_code, 200)
        emails = {item["email"] for item in response.json()}
        for esperado in (
            "admina@a.test",
            "ativo@a.test",
            "inativo@a.test",
            "ativob@b.test",
        ):
            self.assertIn(esperado, emails)


class RegraDeNegocioRetorna400TestCase(BaseAccountsTestCase):
    """Erros de regra de negocio de Membership devem responder 400 (e nao
    500) e nao podem deixar dados orfaos nem eventos de auditoria soltos."""

    def setUp(self):
        super().setUp()
        self._create_user("admin@a.test", self.clinic_a, role="ADMIN")
        self.client_admin = self._login(
            "admin@a.test", clinic_slug=self.clinic_a.slug
        )
        self.client_super = self._login("super@plataforma.test")

    def test_falha_ao_criar_membership_retorna_400_e_reverte_usuario_e_audit(self):
        erro = "regra de negocio violada no cadastro"
        antes = AuditLog.objects.filter(model_name="User", action="CREATE").count()

        with mock.patch.object(
            Membership.objects,
            "create",
            side_effect=DjangoValidationError(erro),
        ):
            response = self.client_super.post(
                "/api/auth/users/",
                {
                    "email": "novo@a.test",
                    "password": "OutraSenha!123",
                    "first_name": "Novo",
                    "last_name": "Usuario",
                    "clinic_id": self.clinic_a.id,
                    "role": "ADMIN",
                },
                format="json",
            )

        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn(erro, response.content.decode("utf-8"))
        # atomic(): o usuario recem-criado foi desfeito - nenhum orfao.
        self.assertFalse(User.objects.filter(email="novo@a.test").exists())
        # atomic(): o evento de auditoria do User tambem foi desfeito.
        depois = AuditLog.objects.filter(model_name="User", action="CREATE").count()
        self.assertEqual(depois, antes)

    def test_clinica_inexistente_retorna_400_e_nao_persiste_usuario(self):
        response = self.client_super.post(
            "/api/auth/users/",
{
                    "email": "orfao@a.test",
                    "password": "OutraSenha!123",
                    "first_name": "Orfao",
                    "last_name": "SemClinic",
                    "clinic_id": 999999,
                },
            format="json",
        )

        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("Clínica não encontrada", response.content.decode("utf-8"))
        self.assertFalse(User.objects.filter(email="orfao@a.test").exists())

    def test_falha_ao_atualizar_membership_retorna_400_e_reverte_alteracoes(self):
        alvo = self._create_user("alvo@a.test", self.clinic_a, role="ATTENDANT")

        with mock.patch.object(
            Membership,
            "save",
            side_effect=DjangoValidationError("regra de negocio violada no update"),
        ):
            response = self.client_admin.patch(
                f"/api/auth/users/{alvo.id}/",
                {"first_name": "Renomeado"},
                format="json",
            )

        self.assertEqual(response.status_code, 400, response.content)
        alvo.refresh_from_db()
        self.assertEqual(alvo.first_name, "alvo")
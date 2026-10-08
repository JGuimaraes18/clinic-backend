"""
Testes do Lote 7 - consistencia da API no fluxo de criacao de clínicas.

Executar somente em banco de teste isolado:

    python manage.py test apps.clinics

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
from apps.clinics.models import Clinic

User = get_user_model()

SENHA = "SenhaTesteL7!123"


class CriacaoClinicaRegraDeNegocioTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.superuser = User.objects.create_superuser(
            email="super@plataforma.test",
            password=SENHA,
            first_name="Super",
            last_name="Admin",
        )
        client = APIClient()
        response = client.post(
            "/api/auth/login/",
            {"email": "super@plataforma.test", "password": SENHA},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.json()['access']}"
        )
        self.client_super = client

    def test_falha_ao_associar_admin_retorna_400_e_reverte_tudo(self):
        # Falha na regra de negocio ao associar o ADMIN da nova clínica:
        # a resposta deve ser 400 (nao 500) e a clínica + usuario inicial
        # nao podem sobrar no banco (transaction.atomic do clinic create).
        erro = "regra de negocio violada na clínica"

        with mock.patch.object(
            Membership.objects,
            "create",
            side_effect=DjangoValidationError(erro),
        ):
            response = self.client_super.post(
                "/api/clinics/",
                {
                    "name": "Clinica Nova",
                    "document": "33333333000133",
                    "phone": "11999990003",
                    "email": "nova@clinica.test",
                },
                format="json",
            )

        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn(erro, response.content.decode("utf-8"))
        self.assertFalse(Clinic.objects.filter(name="Clinica Nova").exists())
        self.assertFalse(
            User.objects.filter(email="nova@clinica.test").exists()
        )
"""
Testes de seguranca e regressao do B7 - Seguranca e Privacidade do AuditLog.

Executar somente em banco de teste isolado:

    python manage.py test apps.audit

Nenhum teste abaixo escreve no banco de desenvolvimento: o TestCase do
Django cria um banco `test_*`, roda tudo dentro de transacao e destroi o
banco ao final da execucao.
"""

from pathlib import Path
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from rest_framework.test import APIClient

import apps.audit as audit_package
from apps.accounts.models import Membership, PasswordResetToken
from apps.audit.models import AuditLog
from apps.audit.services import log_audit_event
from apps.clinics.models import Clinic
from apps.medical_records.models import Prontuario
from apps.patients.models import Patient
from core.middleware import _user as _current_actor, set_current_ip

User = get_user_model()

ACTOR_IP = "198.51.100.7"

# Marcadores que NUNCA podem aparecer em payload de AuditLog.
CONTEUDO_CLINICO_MARCA = "MARCADOR_CONTEUDO_CLINICO_SENSIVEL_9f31"
CPF_MARCA = "98765432100"
SENHA_MARCA = "MinhaSenhaSuperSegura!123"

# Lista INDEPENDENTE da implementacao: nao importa de apps.audit.redaction,
# para o teste nao repetir a regra que deveria estar verificando.
CHAVES_PROIBIDAS = {
    "password",
    "password_hash",
    "new_password",
    "old_password",
    "senha",
    "senha_hash",
    "token",
    "access_token",
    "refresh_token",
    "reset_token",
    "password_reset_token",
    "authorization",
    "secret",
    "client_secret",
    "api_key",
    "private_key",
    "credentials",
    "cpf",
    "cpf_hash",
    "rg",
    "document",
    "conteudo",
    "observacoes",
    "hash_integridade",
    "diagnostico",
    "anotacoes",
}


def _encontrar_chaves_proibidas(node, path=""):
    """Varre uma estrutura JSON e devolve o caminho de cada chave proibida."""
    achadas = []
    if isinstance(node, dict):
        for key, value in node.items():
            current = f"{path}.{key}" if path else str(key)
            if str(key).strip().lower() in CHAVES_PROIBIDAS:
                achadas.append(current)
            achadas.extend(_encontrar_chaves_proibidas(value, current))
    elif isinstance(node, (list, tuple)):
        for index, item in enumerate(node):
            achadas.extend(
                _encontrar_chaves_proibidas(item, f"{path}[{index}]")
            )
    return achadas


def _acting_as(user, ip=ACTOR_IP):
    """Simula o contexto que o CurrentUserMiddleware monta em producao."""
    _current_actor.value = user
    set_current_ip(ip)


def _clear_actor():
    _current_actor.value = None
    set_current_ip(None)


def _payload_blob():
    rows = AuditLog.objects.all().order_by("id")
    return "\n".join(
        f"{row.model_name}|{row.action}|{row.before_data}|{row.after_data}"
        for row in rows
    )


class BaseAuditTestCase(TestCase):
    def setUp(self):
        super().setUp()
        _clear_actor()

        self.superuser = User.objects.create_superuser(
            email="super@plataforma.test",
            password=SENHA_MARCA,
            first_name="Super",
            last_name="Admin",
        )
        self.clinic = Clinic.objects.create(
            name="Clinica Alpha",
            document="11222333000181",
            phone="11999990000",
            email="alpha@clinica.test",
        )

    def tearDown(self):
        _clear_actor()
        super().tearDown()


# ---------------------------------------------------------------------------
# FASE 2 - ORIGEM (Camada 1): nada de dado sensiveis sendo GRAVADO
# ---------------------------------------------------------------------------
class AuditOrigemTestCase(BaseAuditTestCase):

    def test_01_operacao_normal_gera_auditlog(self):
        before = AuditLog.objects.count()

        _acting_as(self.superuser)
        clinic_b = Clinic.objects.create(
            name="Clinica Beta",
            document="99888777000122",
            phone="11888880000",
            email="beta@clinica.test",
        )

        log = AuditLog.objects.get(
            model_name="Clinic", action="CREATE", object_id=str(clinic_b.pk)
        )

        self.assertEqual(AuditLog.objects.count(), before + 1)
        self.assertEqual(log.user, self.superuser)
        self.assertEqual(log.ip_address, ACTOR_IP)
        self.assertEqual(log.severity, "LOW")
        self.assertIsNotNone(log.timestamp)

    def test_02_e_03_password_e_password_hash_nao_sao_gravados(self):
        _acting_as(self.superuser)
        User.objects.create_user(
            email="nova.pessoa@clinica.test",
            password=SENHA_MARCA,
            first_name="Nova",
            last_name="Pessoa",
        )

        blob = _payload_blob()

        # Nenhum valor de credencial sobrevive em texto.
        self.assertNotIn("pbkdf2_sha256$", blob)
        self.assertNotIn(SENHA_MARCA, blob)

        # E nenhuma chave de credencial sobrevive na estrutura.
        proibidas = []
        for log in AuditLog.objects.all():
            for payload in (log.before_data, log.after_data):
                proibidas.extend(
                    _encontrar_chaves_proibidas(payload, f"log[{log.pk}]")
                )
        self.assertEqual(proibidas, [])

        user_logs = AuditLog.objects.filter(model_name="User")
        self.assertTrue(user_logs.exists())
        # O log de criacao continua util: demais campos operacionais la.
        criacao = user_logs.latest("id")
        self.assertEqual(criacao.after_data["email"], "nova.pessoa@clinica.test")
        self.assertEqual(criacao.after_data["first_name"], "Nova")

    def test_04_reset_token_nao_e_gravado(self):
        _acting_as(self.superuser)
        alvo = User.objects.create_user(
            email="esqueci@clinica.test", password=SENHA_MARCA
        )
        token = "abc123" * 10  # 60 chars, dentro do max_length=64

        PasswordResetToken.objects.create(user=alvo, token=token)

        log = AuditLog.objects.get(
            model_name="PasswordResetToken", action="CREATE"
        )

        # Model restrito: o log permanece, o payload nao.
        self.assertIsNone(log.before_data)
        self.assertIsNone(log.after_data)
        self.assertEqual(log.object_id, str(
            PasswordResetToken.objects.get(token=token).pk
        ))
        self.assertNotIn(token, _payload_blob())

    def test_05_e_06_access_e_refresh_token_nao_sao_gravados(self):
        # Nenhum caminho de producao grava esses campos hoje; o teste prova
        # que o mecanismo real de criacao (log_audit_event) os bloqueia.
        log_audit_event(
            user=self.superuser,
            clinic=self.clinic,
            action="UPDATE",
            model_name="User",
            object_id="1",
            after_data={
                "email": "alvo@clinica.test",
                "access_token": "eyJhbGciOiJIUzI1NiJ9.access",
                "refresh_token": "eyJhbGciOiJIUzI1NiJ9.refresh",
            },
        )

        payload = AuditLog.objects.filter(action="UPDATE").latest("id").after_data
        self.assertEqual(payload["email"], "alvo@clinica.test")
        self.assertNotIn("access_token", payload)
        self.assertNotIn("refresh_token", payload)

    def test_07_authorization_header_nao_e_gravado(self):
        log_audit_event(
            user=self.superuser,
            clinic=self.clinic,
            action="UPDATE",
            model_name="User",
            object_id="2",
            after_data={
                "note": "operacional",
                "authorization": "Bearer cabecalho-secreto",
                "x_header": "Bearer valor-em-campo-nao-listado",
            },
        )

        payload = AuditLog.objects.filter(action="UPDATE").latest("id").after_data

        # Chave sensivel removida; valor "Bearer ..." tambem e bloqueado
        # mesmo quando aparece sob um nome de campo nao previsto.
        self.assertEqual(payload["note"], "operacional")
        self.assertNotIn("authorization", payload)
        self.assertNotIn("cabecalho-secreto", str(payload))
        self.assertNotIn("valor-em-campo-nao-listado", str(payload))

    def test_08_conteudo_clinico_nao_e_gravado(self):
        atendimento = self._criar_atendimento()
        _acting_as(self.superuser)

        prontuario = Prontuario.objects.create(
            atendimento=atendimento,
            conteudo=f"{CONTEUDO_CLINICO_MARCA} exame do paciente",
        )

        log = AuditLog.objects.get(
            model_name="Prontuario", action="CREATE", object_id=str(prontuario.pk)
        )

        self.assertIsNone(log.after_data)
        self.assertIsNone(log.before_data)
        self.assertNotIn(CONTEUDO_CLINICO_MARCA, _payload_blob())
        # Metadados de rastreabilidade permanecem na propria linha.
        self.assertEqual(log.action, "CREATE")
        self.assertEqual(log.model_name, "Prontuario")
        self.assertEqual(log.user, self.superuser)
        self.assertEqual(log.severity, "CRITICAL")

    def test_08b_delete_de_prontuario_tambem_nao_grava_conteudo(self):
        atendimento = self._criar_atendimento()
        prontuario = Prontuario.objects.create(
            atendimento=atendimento,
            conteudo=f"{CONTEUDO_CLINICO_MARCA} em delete",
        )

        _acting_as(self.superuser)
        prontuario.delete()

        log = AuditLog.objects.filter(
            model_name="Prontuario", action="DELETE"
        ).latest("id")

        self.assertIsNone(log.before_data)
        self.assertNotIn(CONTEUDO_CLINICO_MARCA, _payload_blob())

    def test_09_cpf_e_rg_nao_sao_gravados(self):
        _acting_as(self.superuser)
        paciente = Patient.objects.create(
            clinic=self.clinic,
            full_name="Paciente Sigiloso",
            cpf=CPF_MARCA,
            document="MG-1234567",
            phone="11911112222",
        )

        log = AuditLog.objects.get(
            model_name="Patient", action="CREATE", object_id=str(paciente.pk)
        )

        blob = _payload_blob()
        self.assertIsNone(log.after_data)
        self.assertNotIn(CPF_MARCA, blob)
        self.assertNotIn("MG-1234567", blob)
        self.assertNotIn(paciente.cpf_hash, blob)
        self.assertNotIn("cpf_hash", blob)

    def test_10_dados_operacionais_utis_continuam_presentes(self):
        _acting_as(self.superuser)
        clinic_b = Clinic.objects.create(
            name="Clinica Gama",
            document="55666777000133",
            phone="11777770000",
            email="gama@clinica.test",
        )

        log = AuditLog.objects.get(
            model_name="Clinic", action="CREATE", object_id=str(clinic_b.pk)
        )

        # Resposta a "quem fez o quê, quando e sobre qual entidade?"
        self.assertEqual(log.action, "CREATE")
        self.assertEqual(log.model_name, "Clinic")
        self.assertEqual(log.object_id, str(clinic_b.pk))
        self.assertEqual(log.user, self.superuser)
        self.assertEqual(log.ip_address, ACTOR_IP)
        self.assertEqual(log.severity, "LOW")
        self.assertIsNotNone(log.timestamp)

        # Payload operacional util continua disponivel.
        self.assertEqual(log.after_data["name"], "Clinica Gama")
        self.assertEqual(log.after_data["slug"], clinic_b.slug)

    def test_10b_atualizacao_somente_com_campos_alterados_e_saneados(self):
        _acting_as(self.superuser)
        clinic = Clinic.objects.get(pk=self.clinic.pk)

        clinic.phone = "11900001111"
        clinic.save()

        log = AuditLog.objects.filter(
            model_name="Clinic", action="UPDATE"
        ).latest("id")

        self.assertEqual(set(log.before_data.keys()), {"phone"})
        self.assertIn("before", log.before_data["phone"])
        self.assertIn("after", log.before_data["phone"])

    # --- helpers ---------------------------------------------------------

    def _criar_atendimento(self):
        _acting_as(self.superuser)
        paciente = Patient.objects.create(
            clinic=self.clinic,
            full_name="Paciente Atendimento",
            phone="11933334444",
        )
        from django.utils import timezone as tz
        from apps.appointments.models import Atendimento

        return Atendimento.objects.create(
            clinic=self.clinic,
            paciente=paciente,
            data_hora=tz.now(),
        )


# ---------------------------------------------------------------------------
# FASE 3/4/5 - API (Camada 2): nada de dado sensiveis historico SENDO EXPOSTO
# ---------------------------------------------------------------------------
class AuditApiSegurancaTestCase(BaseAuditTestCase):

    def setUp(self):
        super().setUp()

        # Reproduz o estado historico problemático (17 hashes de senha e
        # logs com conteudo clinico) DENTRO do banco de teste.
        self.log_senha = AuditLog.objects.create(
            user=self.superuser,
            clinic=None,
            action="UPDATE",
            model_name="User",
            object_id="1",
            after_data={
                "email": "usuario@clinica.test",
                "first_name": "Ana",
                "password": "pbkdf2_sha256$3600000$abc123$XYZ789hash",
            },
            ip_address=ACTOR_IP,
        )
        self.log_prontuario = AuditLog.objects.create(
            user=self.superuser,
            clinic=self.clinic,
            action="CREATE",
            model_name="Prontuario",
            object_id="7",
            after_data={
                "conteudo": CONTEUDO_CLINICO_MARCA,
                "status": "RASCUNHO",
                "hash_integridade": "e3b0c44298fc1c149afbf4c8996fb924",
            },
            ip_address=ACTOR_IP,
        )
        self.log_paciente = AuditLog.objects.create(
            user=self.superuser,
            clinic=self.clinic,
            action="UPDATE",
            model_name="Patient",
            object_id="3",
            after_data={
                "full_name": "Paciente Historico",
                "cpf": CPF_MARCA,
                "cpf_hash": "aa" * 32,
                "document": "MG-7654321",
            },
            ip_address=ACTOR_IP,
        )
        self.log_operacional = AuditLog.objects.create(
            user=self.superuser,
            clinic=self.clinic,
            action="CREATE",
            model_name="Clinic",
            object_id="9",
            after_data={"name": "Clinica Historica", "phone": "11555556666"},
            ip_address=ACTOR_IP,
        )

        self.super_client = self._login("super@plataforma.test", SENHA_MARCA)

    # --- auth -------------------------------------------------------------

    def _login(self, email, password):
        client = APIClient()
        response = client.post(
            "/api/auth/login/",
            {"email": email, "password": password},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.json()['access']}"
        )
        return client

    def _login_clinic(self, email, password, clinic_slug):
        client = APIClient()
        response = client.post(
            "/api/auth/login/",
            {"email": email, "password": password, "clinic_slug": clinic_slug},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.json()['access']}"
        )
        return client

    def test_11_endpoint_funciona_para_usuario_autorizado(self):
        response = self.super_client.get("/api/audit-logs/")

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        self.assertGreaterEqual(len(response.json()), 4)

    def test_12_a_16_resposta_nao_contem_dados_sensiveis(self):
        response = self.super_client.get("/api/audit-logs/")
        self.assertEqual(response.status_code, 200)

        itens = response.json()
        body = response.content.decode("utf-8")

        # 12/13/14/15/16 - nenhum campo sensive sobrevive na estrutura.
        proibidas = _encontrar_chaves_proibidas(itens)
        self.assertEqual(proibidas, [])

        # Valores concretos que estavam no historico tambem nao aparecem.
        self.assertNotIn("pbkdf2_sha256$", body)      # 12/13 hash de senha
        self.assertNotIn("XYZ789hash", body)           # 13
        self.assertNotIn(SENHA_MARCA, body)            # 12
        self.assertNotIn("access_token", body)         # 14
        self.assertNotIn("refresh_token", body)        # 14
        self.assertNotIn(CPF_MARCA, body)              # 15
        self.assertNotIn("MG-7654321", body)           # 15
        self.assertNotIn(CONTEUDO_CLINICO_MARCA, body)  # 16

    def test_12b_dados_operacionais_continuam_expostos(self):
        body = self.super_client.get("/api/audit-logs/").json()
        by_id = {item["id"]: item for item in body}

        # Payload administrativo ute continua visivel.
        self.assertEqual(
            by_id[self.log_operacional.id]["after_data"]["name"],
            "Clinica Historica",
        )
        # Historico de senha: metadado sobrevive, credencial nao.
        self.assertEqual(
            by_id[self.log_senha.id]["after_data"]["email"],
            "usuario@clinica.test",
        )
        self.assertNotIn("password", by_id[self.log_senha.id]["after_data"])

    def test_17_lookup_individual_nao_recupera_conteudo_sensivel(self):
        for log in (self.log_senha, self.log_prontuario, self.log_paciente):
            response = self.super_client.get(f"/api/audit-logs/{log.pk}/")
            self.assertEqual(response.status_code, 200, response.content)

            payload = response.json()
            self.assertEqual(payload["id"], log.pk)
            self.assertEqual(payload["model_name"], log.model_name)

            if log.model_name in ("Prontuario", "Patient"):
                self.assertIsNone(payload["after_data"])
            else:
                self.assertNotIn("password", payload["after_data"])

            body = response.content.decode("utf-8")
            self.assertNotIn(CONTEUDO_CLINICO_MARCA, body)
            self.assertNotIn(CPF_MARCA, body)
            self.assertNotIn("pbkdf2_sha256$", body)

    def test_18_filtros_nao_contornam_a_protecao(self):
        alvos = (
            f"?model_name=Prontuario",
            f"?action=CREATE",
            f"?search={CONTEUDO_CLINICO_MARCA}",
            f"?before_data__contains={CONTEUDO_CLINICO_MARCA}",
            f"?after_data__contains={CONTEUDO_CLINICO_MARCA}",
            f"?ordering=-timestamp",
            f"?id={self.log_prontuario.pk}",
            f"?object_id=7&model_name=Prontuario",
        )

        for query in alvos:
            response = self.super_client.get(f"/api/audit-logs/{query}")
            self.assertEqual(response.status_code, 200, query)
            body = response.content.decode("utf-8")
            self.assertNotIn(CONTEUDO_CLINICO_MARCA, body, query)
            self.assertNotIn(CPF_MARCA, body, query)
            self.assertNotIn("pbkdf2_sha256$", body, query)

    def test_18b_lookup_direto_com_filtro_nao_contorna(self):
        response = self.super_client.get(
            f"/api/audit-logs/?id={self.log_senha.pk}"
        )
        self.assertEqual(response.status_code, 200)
        for item in response.json():
            if item["after_data"]:
                self.assertNotIn("password", item["after_data"])

    # --- SUPERUSER --------------------------------------------------------

    def test_19_superuser_nao_recupera_conteudo_clinico(self):
        response = self.super_client.get("/api/audit-logs/")
        self.assertEqual(response.status_code, 200)

        clinico = [
            item
            for item in response.json()
            if item["model_name"] in ("Prontuario", "Patient", "Atendimento")
        ]
        self.assertTrue(clinico)
        for item in clinico:
            self.assertIsNone(item["before_data"])
            self.assertIsNone(item["after_data"])

        detail = self.super_client.get(f"/api/audit-logs/{self.log_prontuario.pk}/")
        self.assertIsNone(detail.json()["after_data"])

    def test_20_superuser_continua_acessando_metadados(self):
        response = self.super_client.get("/api/audit-logs/")
        item = next(
            i for i in response.json() if i["id"] == self.log_operacional.id
        )

        campos_esperados = {
            "id",
            "severity",
            "action",
            "model_name",
            "object_id",
            "before_data",
            "after_data",
            "ip_address",
            "timestamp",
            "user_detail",
            "clinic_name",
            "user",
            "clinic",
        }
        self.assertEqual(set(item.keys()), campos_esperados)
        self.assertEqual(item["model_name"], "Clinic")
        self.assertEqual(item["action"], "CREATE")
        self.assertEqual(item["ip_address"], ACTOR_IP)
        self.assertEqual(item["clinic_name"], "Clinica Alpha")
        self.assertEqual(item["user_detail"]["email"], "super@plataforma.test")

    def test_20b_usuario_nao_superuser_recebe_403(self):
        membro = User.objects.create_user(
            email="recepcao@clinica.test",
            password=SENHA_MARCA,
            first_name="Recepcao",
            last_name="Clinica",
        )
        Membership.objects.create(
            user=membro, clinic=self.clinic, role="ATTENDANT"
        )
        client = self._login_clinic(
            "recepcao@clinica.test", SENHA_MARCA, self.clinic.slug
        )

        self.assertEqual(client.get("/api/audit-logs/").status_code, 403)
        self.assertEqual(
            client.get(f"/api/audit-logs/{self.log_prontuario.pk}/").status_code,
            403,
        )

    # --- TENANT -----------------------------------------------------------

    def test_21_e_22_isolamento_de_clinica_e_pela_permissao(self):
        """
        O modelo nao tem escopo por clinica no queryset (e nao deve ganhar
        migration para isso no B7): o isolamento e garantido porque o
        endpoint e exclusivo de SUPERUSER, que nao possui clinica, e todo
        usuario de clinica recebe 403 antes de chegar ao queryset.

        Portanto usuario da clinica A NAO alcanca logs da clinica B -
        nem os proprios logs.
        """
        outra_clinic = Clinic.objects.create(
            name="Clinica Beta",
            document="11000111000155",
            phone="11666667777",
            email="beta@clinica.test",
        )
        log_beta = AuditLog.objects.create(
            user=self.superuser,
            clinic=outra_clinic,
            action="CREATE",
            model_name="Clinic",
            object_id=str(outra_clinic.pk),
            after_data={"name": "Clinica Beta"},
        )

        membro_alpha = User.objects.create_user(
            email="admin@alpha.test",
            password=SENHA_MARCA,
            first_name="Admin",
            last_name="Alpha",
        )
        Membership.objects.create(
            user=membro_alpha, clinic=self.clinic, role="ADMIN"
        )
        client_alpha = self._login_clinic(
            "admin@alpha.test", SENHA_MARCA, self.clinic.slug
        )

        # Sem acesso algum ao endpoint -> nenhum log alcanca, nem o da
        # propria clinica, nem o de outra clinica.
        self.assertEqual(client_alpha.get("/api/audit-logs/").status_code, 403)
        self.assertEqual(
            client_alpha.get(f"/api/audit-logs/{log_beta.pk}/").status_code, 403
        )

        # O superuser (sem clinica) continua vendo apenas metadados.
        body = self.super_client.get(f"/api/audit-logs/{log_beta.pk}/").json()
        self.assertEqual(body["clinic_name"], "Clinica Beta")
        self.assertNotIn(CONTEUDO_CLINICO_MARCA, str(body))


# ---------------------------------------------------------------------------
# FASE 7 - HISTORICO: preservacao comprovada
# ---------------------------------------------------------------------------
class AuditHistoricoTestCase(BaseAuditTestCase):

    def test_23_nenhuma_alteracao_destrutiva_no_banco(self):
        linha_protegida = AuditLog.objects.create(
            user=self.superuser,
            clinic=None,
            action="UPDATE",
            model_name="User",
            object_id="42",
            after_data={"email": "historico@clinica.test"},
        )

        def snapshot(log):
            return (
                log.pk,
                log.action,
                log.model_name,
                log.object_id,
                log.before_data,
                log.after_data,
                log.ip_address,
                log.severity,
                log.user_id,
                log.clinic_id,
                str(log.timestamp),
            )

        antes_pk = linha_protegida.pk
        antes = snapshot(AuditLog.objects.get(pk=antes_pk))
        antes_count = AuditLog.objects.count()

        # Dispara operacoes normais de auditoria: CREATE, UPDATE e DELETE.
        _acting_as(self.superuser)
        clinic = Clinic.objects.create(
            name="Clinica Efemera",
            document="11333444000166",
            phone="11444445555",
            email="efemera@clinica.test",
        )
        clinic.phone = "11444449999"
        clinic.save()
        clinic.delete()

        depois = AuditLog.objects.get(pk=antes_pk)
        self.assertEqual(snapshot(depois), antes)
        # Apenas acrescimos: nenhuma linha antiga foi removida.
        self.assertEqual(depois.pk, antes_pk)
        self.assertGreater(AuditLog.objects.count(), antes_count)

    def test_24_nao_existem_migracoes_de_limpeza_ou_redaction(self):
        migracoes_dir = Path(audit_package.__file__).parent / "migrations"
        arquivos = sorted(p.name for p in migracoes_dir.glob("*.py"))

        self.assertEqual(
            arquivos,
            ["0001_initial.py", "__init__.py"],
            "Novo arquivo de migration encontrado: revisar se e destrutivo.",
        )

        proibido = (
            "RunSQL",
            "RunPython",
            "DELETE FROM audit",
            "UPDATE audit_auditlog",
            "TRUNCATE",
        )
        for arquivo in migracoes_dir.glob("*.py"):
            texto = arquivo.read_text(encoding="utf-8")
            for padrao in proibido:
                self.assertNotIn(
                    padrao,
                    texto,
                    f"Migration {arquivo.name} contem operacao '{padrao}'.",
                )

    def test_25_testes_rodan_somente_em_banco_de_teste(self):
        nome_banco = str(connection.settings_dict["NAME"])
        # O runner do Django ja aponta DATABASES["default"]["NAME"] para o
        # banco de teste; o nome do banco de desenvolvimento vem do ambiente.
        banco_dev = os.getenv("POSTGRES_DB")

        self.assertTrue(nome_banco.startswith("test_"))
        self.assertNotEqual(nome_banco, banco_dev)
        self.assertIn(
            "postgresql", settings.DATABASES["default"]["ENGINE"]
        )

    def test_25b_migracao_de_redaction_nao_foi_criada(self):
        # O B7 nao precisa de migration: a correcao e em escrita (signals)
        # e leitura (serializer/admin).
        migracoes_dir = Path(audit_package.__file__).parent / "migrations"
        self.assertFalse(
            any("redact" in p.name.lower() for p in migracoes_dir.glob("*.py"))
        )


# ---------------------------------------------------------------------------
# LOTE 6 - ATRIBUICAO, DEDUP E INTEGRIDADE FK
# ---------------------------------------------------------------------------
class AuditLote6RegressaoTestCase(BaseAuditTestCase):

    def test_26_api_atribui_usuario_autenticado_ao_auditlog(self):
        """
        Regressao L6 (P0): antes, o CurrentUserMiddleware registrava o
        AnonymousUser antes da autenticacao DRF e toda linha de auditoria
        de uma requisicao autenticada ficava com user=None.
        """
        _clear_actor()
        admin = User.objects.create_user(
            email="admin.l6@clinica.test",
            password=SENHA_MARCA,
            first_name="Admin",
            last_name="L6",
        )
        Membership.objects.create(user=admin, clinic=self.clinic, role="ADMIN")
        _clear_actor()

        client = APIClient()
        response = client.post(
            "/api/auth/login/",
            {
                "email": "admin.l6@clinica.test",
                "password": SENHA_MARCA,
                "clinic_slug": self.clinic.slug,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.json()['access']}"
        )

        # Cria um Patient via API com o usuario autenticado no JWT.
        response = client.post(
            "/api/patients/",
            {
                "full_name": "Paciente L6",
                "phone": "11922223333",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)

        log = AuditLog.objects.get(
            model_name="Patient", action="CREATE", object_id=str(response.json()["id"])
        )
        self.assertEqual(log.user_id, admin.pk)
        self.assertIsNotNone(log.ip_address)

    def test_27_login_atribui_usuario_em_user_auditlog(self):
        """
        Regressao L6 (P0): o mesmo problema da atribuicao afetava as
        operacoes sobre User/Membership disparadas via API. Aqui o usuario
        e criado por um request autenticado (POST /api/users/), de forma
        que todos os signals disparam dentro do contexto da requisicao.
        """
        _clear_actor()
        admin = User.objects.create_user(
            email="admin.l6b@clinica.test",
            password=SENHA_MARCA,
            first_name="Admin",
            last_name="L6B",
        )
        Membership.objects.create(user=admin, clinic=self.clinic, role="ADMIN")
        _clear_actor()

        client = APIClient()
        response = client.post(
            "/api/auth/login/",
            {
                "email": "admin.l6b@clinica.test",
                "password": SENHA_MARCA,
                "clinic_slug": self.clinic.slug,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.json()['access']}"
        )

        response = client.post(
            "/api/auth/users/",
            {
                "email": "criado.pela.api@clinica.test",
                "password": SENHA_MARCA,
                "first_name": "Criado",
                "last_name": "PelaApi",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        novo = User.objects.get(email="criado.pela.api@clinica.test")
        log = AuditLog.objects.get(
            model_name="User", action="CREATE", object_id=str(novo.pk)
        )
        self.assertEqual(log.user_id, admin.pk)

    def test_28_user_nao_duplica_auditlog(self):
        """
        Regressao L6 (P1): User possui emissor curado em accounts/signals.py;
        o emissor generico de apps/audit/signals.py precisa ignorar o modelo
        para nao gravar duas linhas para a mesma operacao.
        """
        _acting_as(self.superuser)
        user = User.objects.create_user(
            email="sem.duplicado@clinica.test", password=SENHA_MARCA
        )
        users = AuditLog.objects.filter(
            model_name="User", action="CREATE", object_id=str(user.pk)
        )
        self.assertEqual(users.count(), 1)

    def test_29_membership_nao_duplica_auditlog(self):
        """
        Regressao L6 (P1): idem para Membership.
        """
        _acting_as(self.superuser)
        user = User.objects.create_user(
            email="membro.sem.duplicado@clinica.test", password=SENHA_MARCA
        )
        member = Membership.objects.create(user=user, clinic=self.clinic, role="ATTENDANT")
        membros = AuditLog.objects.filter(
            model_name="Membership",
            action="CREATE",
            object_id=str(member.pk),
        )
        self.assertEqual(membros.count(), 1)

    def test_30_delete_de_usuario_nao_quebra_fk(self):
        """
        Regressao L6: o emissor post_delete de User precisa registrar a
        auditoria sem referenciar uma linha que acabou de ser apagada.
        O ator e o superuser (ainda existente); o alvo some do payload.
        """
        _acting_as(self.superuser)
        alvo = User.objects.create_user(
            email="alvo.delete.l6@clinica.test", password=SENHA_MARCA
        )

        alvo.delete()
        _clear_actor()

        log = AuditLog.objects.filter(
            model_name="User", action="DELETE"
        ).latest("id")
        self.assertEqual(log.user_id, self.superuser.pk)
        self.assertEqual(log.before_data["email"], "alvo.delete.l6@clinica.test")

    def test_31_delete_de_membership_nao_quebra_fk(self):
        """
        Regressao L6: idem para o post_delete de Membership, usada via
        cascade quando um User e apagado.
        """
        _acting_as(self.superuser)
        alvo = User.objects.create_user(
            email="membro.delete.l6@clinica.test", password=SENHA_MARCA
        )
        membership = Membership.objects.create(
            user=alvo, clinic=self.clinic, role="ATTENDANT"
        )
        membership_pk = membership.pk

        alvo.delete()
        _clear_actor()

        log = AuditLog.objects.filter(
            model_name="Membership", action="DELETE"
        ).latest("id")
        self.assertEqual(log.object_id, str(membership_pk))
        self.assertIsNotNone(log.clinic_id)

    def test_32_cleanup_audit_command_existe(self):
        """
        Regressao L6: o comando cleanup_audit vivia em
        management/commandsa/ (mismatch) e nunca era descoberto pelo
        Django. Agora esta em management/commands/.
        """
        from django.core.management import get_commands

        self.assertIn("cleanup_audit", get_commands())

"""
Politica central de minimizacao de dados do AuditLog (B7).

Unica fonte de verdade para as duas camadas obrigatorias do B7:

  Camada 1 - escrita (impede que dados sensiveis sejam gravados):
      apps/audit/signals.py
      apps/audit/services.py
      apps/audit/utils.py

  Camada 2 - leitura (impede que dados sensiveis historicos sejam expostos):
      apps/audit/serializers.py
      apps/audit/admin.py

Regra geral: a auditoria responde "quem fez o quê, quando e sobre qual
entidade?". Nunca armazena nem expoe credenciais, tokens, identificadores
de pacientes ou conteudo clinico.
"""

# Chaves bloqueadas. A comparacao e feita apos normalizacao
# (strip + lower), portanto cobre variacoes de caixa.
SENSITIVE_KEYS = frozenset(
    {
        # --- credenciais / hashes de senha ---
        "password",
        "password_hash",
        "new_password",
        "old_password",
        "current_password",
        "senha",
        "senha_hash",
        "hash_senha",
        # --- tokens ---
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
        # --- identificadores pessoais sensiveis ---
        "cpf",
        "cpf_hash",
        "rg",
        "document",
        # --- conteudo clinico / prontuario ---
        "conteudo",
        "observacoes",
        "hash_integridade",
        "diagnostico",
        "anotacoes",
        # --- payload arbitrario vindo do cliente ---
        "extra_preferences",
    }
)

# Models cujo payload NUNCA deve ser auditado: credencial, registro de
# paciente ou conteudo clinico. O registro AuditLog continua sendo criado,
# apenas sem despejar os campos do model - permanecem as colunas da propria
# linha (acao, entidade, objeto, usuario, clinica, ip, severidade, data),
# que ja respondem "quem fez o quê, quando e sobre qual entidade?".
RESTRICTED_PAYLOAD_MODELS = frozenset(
    {
        "Patient",
        "Atendimento",
        "Prontuario",
        "AdendoProntuario",
        "PasswordResetToken",
    }
)

REDACTED = "[REDACTADO]"

# Marcas irrefutaveis de segredo em valores string, para nao depender
# exclusivamente do nome do campo (defesa em profundidade caso um campo
# sensivel seja renomeado).
_SECRET_VALUE_PREFIXES = (
    "pbkdf2_sha256$",
    "pbkdf2_sha1$",
    "bcrypt$",
    "$2a$",
    "$2b$",
    "$2y$",
)
_BEARER_PREFIX = "bearer "


def _normalize(key):
    return str(key).strip().lower()


def _is_secret_value(value):
    if not isinstance(value, str):
        return False
    if value.strip().lower().startswith(_BEARER_PREFIX):
        return True
    return value.startswith(_SECRET_VALUE_PREFIXES)


def _sanitize_node(node):
    if isinstance(node, dict):
        return {
            key: _sanitize_node(value)
            for key, value in node.items()
            if _normalize(key) not in SENSITIVE_KEYS
        }

    if isinstance(node, (list, tuple)):
        return [_sanitize_node(item) for item in node]

    if _is_secret_value(node):
        return REDACTED

    return node


def sanitize_snapshot(model_name, data):
    """
    Retorna um payload seguro para gravacao/exibicao de AuditLog.

    Retorna None quando nao ha payload ou quando o model e de conteudo
    restrito (dai o log permanece apenas com os metadados da linha).
    """
    if not data or not isinstance(data, dict):
        return None

    if str(model_name) in RESTRICTED_PAYLOAD_MODELS:
        return None

    return _sanitize_node(data)

"""Requisitos de produção da disciplina de Secure DevOps: health check com versão,
segredos obrigatórios, cabeçalhos de segurança, limite de tentativas e telemetria opcional."""
import re

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from app import config
from app.config import Settings
from app.main import create_app
from app.protecao import LimiteTentativas
from app.telemetria import configurar_telemetria

CSRF_RE = re.compile(r'name="csrf_token" value="([^"]+)"')


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("APPLICATIONINSIGHTS_CONNECTION_STRING", raising=False)
    return create_app(database_url=f"sqlite:///{tmp_path / 'teste.db'}", seed=True)


@pytest.fixture()
def client(app):
    return TestClient(app)


def test_health_informa_banco_e_versao(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "banco": "ok", "versao": "dev"}


def test_health_usa_o_arquivo_versao_gravado_pelo_pipeline(tmp_path, monkeypatch):
    arquivo = tmp_path / "VERSAO"
    arquivo.write_text("abc1234\n", encoding="utf-8")
    monkeypatch.setattr(config, "ARQUIVO_VERSAO", arquivo)
    app = create_app(database_url=f"sqlite:///{tmp_path / 'teste.db'}", seed=False)
    assert TestClient(app).get("/health").json()["versao"] == "abc1234"


def test_health_responde_503_se_o_banco_cair(app, client):
    app.state.SessionLocal.kw["bind"].dispose()
    app.state.SessionLocal.configure(bind=_engine_quebrado())
    r = client.get("/health")
    assert r.status_code == 503
    assert r.json()["banco"] == "erro"


def _engine_quebrado():
    from sqlalchemy import create_engine

    # Diretório inexistente: o SQLite não consegue abrir o arquivo.
    return create_engine("sqlite:////caminho/que/nao/existe/x/y/banco.db")


def test_producao_nao_sobe_sem_segredos(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "x" * 64)
    monkeypatch.delenv("INTEGRATION_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="INTEGRATION_API_KEY"):
        Settings()


def test_producao_com_segredos_sobe(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "x" * 64)
    monkeypatch.setenv("INTEGRATION_API_KEY", "y" * 32)
    monkeypatch.setenv("FERNET_KEY", Fernet.generate_key().decode())  # chave gerada no teste, nunca fixa
    s = Settings()
    assert s.secret_key == "x" * 64
    assert s.https_only_cookies is True


def test_cabecalhos_de_seguranca(client):
    r = client.get("/")
    csp = r.headers["content-security-policy"]
    assert "default-src 'self'" in csp and "frame-ancestors 'none'" in csp
    assert "script-src 'self'" in csp and "unsafe-inline" not in csp.split("style-src-attr")[0]
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "strict-transport-security" not in r.headers  # HSTS só em produção (HTTPS)


def test_hsts_em_producao(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "x" * 64)
    monkeypatch.setenv("INTEGRATION_API_KEY", "y" * 32)
    monkeypatch.setenv("FERNET_KEY", Fernet.generate_key().decode())  # chave gerada no teste, nunca fixa
    app = create_app(database_url=f"sqlite:///{tmp_path / 'teste.db'}", seed=False)
    r = TestClient(app, base_url="https://testserver").get("/health")
    assert r.headers["strict-transport-security"].startswith("max-age=31536000")


def test_swagger_fica_fora_da_csp(client):
    r = client.get("/api/docs")
    assert r.status_code == 200
    assert "content-security-policy" not in r.headers


def test_login_bloqueia_forca_bruta(client):
    token = CSRF_RE.search(client.get("/entrar").text).group(1)
    dados = {"csrf_token": token, "login": "ninguem@exemplo.org", "senha": "errada123"}
    codigos = [client.post("/entrar", data=dados).status_code for _ in range(11)]
    assert codigos[:10] == [400] * 10
    assert codigos[10] == 429


def test_limite_tentativas_libera_depois_da_janela(monkeypatch):
    agora = [1000.0]
    monkeypatch.setattr("app.protecao.time.monotonic", lambda: agora[0])
    limite = LimiteTentativas(maximo=2, janela_s=60)
    assert limite.registrar("1.2.3.4") and limite.registrar("1.2.3.4")
    assert not limite.registrar("1.2.3.4")
    assert limite.registrar("5.6.7.8")  # outro cliente não é afetado
    agora[0] += 61
    assert limite.registrar("1.2.3.4")


def test_telemetria_desligada_sem_connection_string(monkeypatch):
    monkeypatch.delenv("APPLICATIONINSIGHTS_CONNECTION_STRING", raising=False)
    assert configurar_telemetria(object()) is False

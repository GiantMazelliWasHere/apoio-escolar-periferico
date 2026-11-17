"""Integração RPA → núcleo: o robô UiPath devolve os voluntários credenciados no SICREV."""
from sqlalchemy import select

from app.models import Auditoria, Usuario

from .test_fluxo import API_KEY, app, client, csrf  # noqa: F401 (fixtures)

URL = "/api/v1/integracao/voluntarios"
HDR = {"X-API-Key": API_KEY}


def lote(*ids):
    return [
        {"apelido": f"vol_{i}", "email": f"pessoa.{i.lower()}@exemplo.com.br", "bairro": "Capão Redondo", "aceita_boletim": True}
        for i in ids
    ]


def test_exige_api_key(client):
    assert client.post(URL, json=lote("I001")).status_code == 401
    assert client.post(URL, json=lote("I001"), headers={"X-API-Key": "errada"}).status_code == 401


def test_cria_pendentes_e_e_idempotente(app, client):
    r = client.post(URL, json=lote("I001", "I002"), headers=HDR)
    assert r.status_code == 201
    assert r.json() == {"criados": ["vol_I001", "vol_I002"], "rejeitados": [], "motivos": {}}

    with app.state.SessionLocal() as db:
        v = db.scalar(select(Usuario).where(Usuario.apelido == "vol_I001"))
        assert v.papel == "voluntario" and v.aprovado is False
        assert v.origem == "rpa_sicrev" and v.aceita_boletim is True and v.bairro == "Capão Redondo"
        assert v.nome is None
        assert db.scalar(select(Auditoria.quantidade).where(Auditoria.acao == "voluntarios_rpa")) == 2

    # Reexecução do robô: nada duplicado, todos voltam em rejeitados.
    r = client.post(URL, json=lote("I001", "I002"), headers=HDR)
    assert r.status_code == 201
    assert r.json()["criados"] == [] and r.json()["rejeitados"] == ["vol_I001", "vol_I002"]


def test_item_ruim_nao_derruba_o_lote(client):
    itens = lote("I010") + [
        {"apelido": "vol_I011", "email": "sem-arroba"},
        {"apelido": "vol_I012", "email": "a@b.com", "cpf": "123.456.789-00"},  # minimização: CPF é recusado
        {"apelido": "vol_I010", "email": "outro@exemplo.com"},  # repetido no lote
        "nao-e-objeto",
    ]
    j = client.post(URL, json=itens, headers=HDR).json()
    assert j["criados"] == ["vol_I010"]
    assert j["rejeitados"] == ["vol_I011", "vol_I012", "vol_I010", "item_4"]
    assert "email" in j["motivos"]["vol_I011"] and "cpf" in j["motivos"]["vol_I012"]


def test_email_ja_cadastrado_e_rejeitado(client):
    client.post(URL, json=lote("I020"), headers=HDR)
    outro = [{"apelido": "vol_I021", "email": "pessoa.i020@exemplo.com.br"}]
    assert client.post(URL, json=outro, headers=HDR).json()["motivos"] == {"vol_I021": "e-mail já cadastrado"}


def test_sem_senha_utilizavel(client):
    client.post(URL, json=lote("I030"), headers=HDR)
    token = csrf(client, "/entrar")
    r = client.post("/entrar", data={"csrf_token": token, "login": "pessoa.i030@exemplo.com.br", "senha": "!rpa"}, follow_redirects=False)
    assert r.status_code == 400


def test_coordenacao_ve_e_aprova(client):
    from fastapi.testclient import TestClient

    client.post(URL, json=lote("I040"), headers=HDR)
    coord = TestClient(client.app)
    token = csrf(coord, "/entrar")
    coord.post("/entrar", data={"csrf_token": token, "login": "coordenacao.demo@exemplo.org", "senha": "coordenacao123"})
    pagina = coord.get("/coordenacao/voluntarios").text
    assert "vol_I040" in pagina and "SICREV" in pagina

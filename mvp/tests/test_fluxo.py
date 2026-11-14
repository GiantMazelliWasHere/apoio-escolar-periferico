"""Testes do fluxo central do MVP: cadastro → busca → agendamento → presença → impacto."""
import re
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.models import Horario, Usuario

CSRF_RE = re.compile(r'name="csrf_token" value="([^"]+)"')
API_KEY = "chave-de-teste"


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("INTEGRATION_API_KEY", API_KEY)
    return create_app(database_url=f"sqlite:///{tmp_path / 'teste.db'}", seed=True)


@pytest.fixture()
def client(app):
    return TestClient(app)


def csrf(client, url):
    r = client.get(url)
    assert r.status_code == 200, r.text
    m = CSRF_RE.search(r.text)
    assert m, f"csrf_token ausente em {url}"
    return m.group(1)


def cadastrar_estudante(client, email="ana.teste@exemplo.org", consentimento=True):
    token = csrf(client, "/cadastro/estudante")
    escola_id = re.search(r'<option value="(\d+)"', client.get("/cadastro/estudante").text).group(1)
    data = {
        "csrf_token": token,
        "nome": "Ana Teste",
        "email": email,
        "senha": "senha-forte-123",
        "escola_id": escola_id,
        "ano_escolar": "9º ano EF",
        "bairro": "Jardim Exemplo",
    }
    if consentimento:
        data["consentimento"] = "on"
    return client.post("/cadastro/estudante", data=data, follow_redirects=False)


def entrar(client, email, senha):
    token = csrf(client, "/entrar")
    return client.post("/entrar", data={"csrf_token": token, "email": email, "senha": senha}, follow_redirects=False)


def primeiro_horario_livre(app, materia="Matemática"):
    with app.state.SessionLocal() as db:
        h = (
            db.query(Horario)
            .filter(Horario.materia == materia, Horario.inicio > datetime.now())
            .order_by(Horario.inicio)
            .first()
        )
        return h.id


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_paginas_publicas_abrem(client):
    for url in ["/", "/monitorias", "/impacto", "/privacidade", "/entrar", "/cadastro/estudante", "/cadastro/voluntario"]:
        assert client.get(url).status_code == 200, url


def test_cadastro_exige_consentimento_do_responsavel(client):
    r = cadastrar_estudante(client, consentimento=False)
    assert r.status_code == 400
    assert "consentimento" in r.text.lower()


def test_post_sem_csrf_e_rejeitado(client):
    r = client.post("/entrar", data={"email": "x@x.org", "senha": "x"})
    assert r.status_code == 403


def test_fluxo_completo_estudante_agenda_e_voluntario_registra_presenca(app, client):
    # 1. Cadastro do estudante já deixa logado e leva para a busca
    r = cadastrar_estudante(client)
    assert r.status_code == 303
    assert r.headers["location"].startswith("/monitorias")

    # 2. Busca por matéria mostra horários
    r = client.get("/monitorias", params={"materia": "Matemática"})
    assert r.status_code == 200
    assert "Matemática" in r.text
    assert "Agendar" in r.text

    # 3. Agenda um horário
    horario_id = primeiro_horario_livre(app)
    token = csrf(client, "/monitorias?materia=Matemática")
    r = client.post(
        f"/monitorias/{horario_id}/agendar",
        data={"csrf_token": token, "duvida": "Equação do primeiro grau"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    r = client.get(r.headers["location"])
    assert r.status_code == 200
    assert "Monitoria agendada" in r.text

    # 4. Aparece em "Minhas monitorias"
    r = client.get("/minhas-monitorias")
    assert "Matemática" in r.text and "Agendada" in r.text

    # 5. Voluntário dono do horário vê o agendamento e registra presença
    with app.state.SessionLocal() as db:
        h = db.get(Horario, horario_id)
        vol_email = h.voluntario.email
        ag_id = h.agendamentos[-1].id
    client.post("/sair", data={"csrf_token": csrf(client, "/minhas-monitorias")})
    assert entrar(client, vol_email, "voluntario123").status_code == 303
    r = client.get("/voluntario")
    assert "Ana Teste" in r.text
    token = csrf(client, "/voluntario")

    # Presença ainda não liberada (monitoria é em mais de 1 hora)
    r = client.post(f"/agendamentos/{ag_id}/presenca", data={"csrf_token": token, "status": "realizado"}, follow_redirects=False)
    assert r.status_code == 400

    # A monitoria chega: começa em 10 minutos
    with app.state.SessionLocal() as db:
        db.get(Horario, horario_id).inicio = datetime.now() + timedelta(minutes=10)
        db.commit()
    r = client.post(f"/agendamentos/{ag_id}/presenca", data={"csrf_token": token, "status": "realizado"}, follow_redirects=False)
    assert r.status_code == 303

    # 6. O painel de impacto conta a monitoria realizada
    dados = client.get("/api/v1/impacto").json()
    assert dados["monitorias_realizadas"] >= 1
    assert dados["horas_reforco"] > 0


def test_nao_agenda_horario_lotado(app, client):
    cadastrar_estudante(client)
    with app.state.SessionLocal() as db:
        h = db.query(Horario).filter(Horario.inicio > datetime.now()).first()
        h.vagas = 0
        db.commit()
        hid = h.id
    token = csrf(client, "/monitorias")
    r = client.post(f"/monitorias/{hid}/agendar", data={"csrf_token": token}, follow_redirects=False)
    assert r.status_code == 409


def test_agendar_exige_login_de_estudante(app, client):
    hid = primeiro_horario_livre(app)
    assert "Entre para agendar" in client.get("/monitorias").text
    token = csrf(client, "/entrar")  # mesma sessão anônima
    r = client.post(f"/monitorias/{hid}/agendar", data={"csrf_token": token}, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"].startswith("/entrar")


def test_voluntario_cria_horario(app, client):
    token = csrf(client, "/cadastro/voluntario")
    r = client.post(
        "/cadastro/voluntario",
        data={"csrf_token": token, "nome": "Vol Novo", "email": "vol.novo@exemplo.org", "senha": "senha-forte-123", "formacao": "Licenciatura"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    amanha = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    token = csrf(client, "/voluntario")
    r = client.post(
        "/voluntario/horarios",
        data={"csrf_token": token, "materia": "Física", "data": amanha, "hora": "18:00", "duracao_min": "60", "modalidade": "online", "local_ou_link": "https://meet.exemplo.org/abc", "vagas": "2"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "Física" in client.get("/voluntario").text


def test_csv_para_rpa_exige_chave_e_nao_expoe_dados_pessoais(client):
    assert client.get("/api/v1/agendamentos.csv").status_code == 401
    r = client.get("/api/v1/agendamentos.csv", headers={"X-API-Key": API_KEY})
    assert r.status_code == 200
    assert r.text.splitlines()[0].startswith("agendamento_id,")
    assert "@" not in r.text  # nenhum e-mail no export


def test_pipeline_de_dados_atualiza_prioridade_da_escola(app, client):
    payload = [{"escola_id": 1, "territorio_prioritario": True, "indice_prioridade": 0.87}]
    assert client.put("/api/v1/escolas/prioridade", json=payload).status_code == 401
    r = client.put("/api/v1/escolas/prioridade", json=payload, headers={"X-API-Key": API_KEY})
    assert r.status_code == 200
    assert r.json()["atualizadas"] == 1
    escolas = client.get("/api/v1/escolas").json()
    e1 = next(e for e in escolas if e["id"] == 1)
    assert e1["fonte_prioridade"] == "pipeline"
    assert e1["indice_prioridade"] == 0.87


def test_senha_guardada_com_hash(app, client):
    cadastrar_estudante(client, email="hash@exemplo.org")
    with app.state.SessionLocal() as db:
        u = db.query(Usuario).filter_by(email="hash@exemplo.org").one()
        assert "senha-forte-123" not in u.senha_hash


def test_filtro_por_turno_mostra_so_horarios_da_noite(app, client):
    with app.state.SessionLocal() as db:
        futuros = db.query(Horario).filter(Horario.inicio > datetime.now()).all()
        noite = sum(1 for h in futuros if h.inicio.hour >= 18 and h.vagas_livres > 0)
        dia = sum(1 for h in futuros if h.inicio.hour < 18 and h.vagas_livres > 0)
    assert noite and dia, "o seed precisa ter horários de dia e de noite"
    html = client.get("/monitorias?turno=noite").text
    horas = [int(hh) for hh in re.findall(r"às (\d{2}):\d{2}", html)]
    assert horas and all(hh >= 18 for hh in horas)
    assert 'value="noite" selected' in html
    # turno inválido é ignorado (mostra todos)
    todas = client.get("/monitorias?turno=madrugada").text
    assert any(int(hh) < 18 for hh in re.findall(r"às (\d{2}):\d{2}", todas))

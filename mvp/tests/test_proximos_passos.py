"""Próximos passos validados nas entrevistas (§9.3 da entrega de Business):
tags de matéria, prévia de horas e certificado do voluntário, grade horária semanal."""
import re
from datetime import datetime, timedelta

from app.models import Agendamento, Horario, Usuario

from .test_fluxo import app, cadastrar_estudante, client, csrf  # noqa: F401  (fixtures)


def cadastrar_voluntario(client, nome="Vol Certificado", email="vol.cert@exemplo.org"):
    token = csrf(client, "/cadastro/voluntario")
    r = client.post(
        "/cadastro/voluntario",
        data={"csrf_token": token, "nome": nome, "email": email, "senha": "senha-forte-123", "formacao": "Eng. de Software"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    return email


def test_busca_por_tags_de_materia(client):
    html = client.get("/monitorias").text
    assert 'type="radio" name="materia" value="Física"' in html
    html = client.get("/monitorias", params={"materia": "Química"}).text
    assert 'value="Química" checked' in html
    materias = re.findall(r'<p class="horario-materia">([^<]+)</p>', html)
    assert materias and set(materias) == {"Química"}


def test_voluntario_ve_horas_e_emite_certificado(app, client):
    email = cadastrar_voluntario(client)
    # Sem monitoria realizada: zero horas e certificado ainda indisponível
    assert "0 h" in client.get("/voluntario").text
    assert "ainda não tem horas" in client.get("/voluntario/certificado").text

    # Uma monitoria de 90 min realizada (2 estudantes presentes contam como 1 sessão)
    with app.state.SessionLocal() as db:
        vol = db.query(Usuario).filter_by(email=email).one()
        estudantes = db.query(Usuario).filter_by(papel="estudante").limit(1).all()
        h = Horario(voluntario_id=vol.id, materia="Química", inicio=datetime.now() - timedelta(days=2), duracao_min=90, vagas=3)
        db.add(h)
        db.flush()
        db.add(Agendamento(horario_id=h.id, estudante_id=estudantes[0].id, status="realizado"))
        db.add(Agendamento(horario_id=h.id, estudante_id=estudantes[0].id, status="faltou"))
        # Horário com só falta não conta
        h2 = Horario(voluntario_id=vol.id, materia="Química", inicio=datetime.now() - timedelta(days=1), duracao_min=60, vagas=1)
        db.add(h2)
        db.flush()
        db.add(Agendamento(horario_id=h2.id, estudante_id=estudantes[0].id, status="faltou"))
        db.commit()

    painel = client.get("/voluntario").text
    assert "1 h 30 min" in painel and "1 monitoria realizada" in painel
    cert = client.get("/voluntario/certificado").text
    assert "Vol Certificado" in cert and "1 h 30 min" in cert and "Química" in cert
    assert "Eng. de Software" in cert


def test_certificado_exige_voluntario(client):
    cadastrar_estudante(client)
    r = client.get("/voluntario/certificado", follow_redirects=False)
    assert r.status_code in (303, 403)


def test_grade_semanal_cria_horarios_nos_dias_escolhidos(app, client):
    email = cadastrar_voluntario(client, nome="Vol Grade", email="vol.grade@exemplo.org")
    amanha = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    token = csrf(client, "/voluntario")
    r = client.post(
        "/voluntario/horarios",
        data={"csrf_token": token, "materia": "Inglês", "data": amanha, "hora": "19:00", "duracao_min": "60",
              "modalidade": "online", "vagas": "2", "dias": ["0", "2"], "semanas": "2"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "criados=4" in r.headers["location"]
    with app.state.SessionLocal() as db:
        vol = db.query(Usuario).filter_by(email=email).one()
        hs = db.query(Horario).filter_by(voluntario_id=vol.id).all()
    assert len(hs) == 4
    assert {h.inicio.weekday() for h in hs} == {0, 2}
    assert all(h.inicio.hour == 19 and h.inicio > datetime.now() for h in hs)
    assert "4 horários publicados" in client.get(r.headers["location"]).text


def test_horario_unico_continua_funcionando_sem_dias(app, client):
    email = cadastrar_voluntario(client, nome="Vol Unico", email="vol.unico@exemplo.org")
    amanha = datetime.now() + timedelta(days=1)
    token = csrf(client, "/voluntario")
    r = client.post(
        "/voluntario/horarios",
        data={"csrf_token": token, "materia": "Física", "data": amanha.strftime("%Y-%m-%d"), "hora": "18:00"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    with app.state.SessionLocal() as db:
        vol = db.query(Usuario).filter_by(email=email).one()
        hs = db.query(Horario).filter_by(voluntario_id=vol.id).all()
    assert len(hs) == 1 and hs[0].inicio.date() == amanha.date()

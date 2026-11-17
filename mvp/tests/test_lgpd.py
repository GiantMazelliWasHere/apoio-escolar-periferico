"""LGPD by design: consentimento do responsável por link (WhatsApp), e-mail cifrado, direitos do
titular, expurgo em 30 dias, aprovação de voluntário, apelido no lugar de nome e supressão de grupos < 5."""
import json
import re
import sqlite3
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.lgpd import Cifra, expurgar_pendentes, suprimir
from app.main import create_app
from app.models import Agendamento, Auditoria, Usuario

from .test_fluxo import API_KEY, app, cadastrar_estudante, cadastrar_voluntario, client, csrf, entrar, primeiro_horario_livre  # noqa: F401

LINK_RE = re.compile(r'<code id="link-responsavel">[^<]*/responsavel/([A-Za-z0-9_\-]+)</code>')


def cadastrar_menor(client, apelido="leo.mat"):
    r = cadastrar_estudante(client, apelido=apelido, faixa_idade="13 a 15 anos")
    assert r.status_code == 200, r.text
    m = LINK_RE.search(r.text)
    assert m, "a tela pós-cadastro precisa mostrar o link do responsável"
    return m.group(1), r


def decidir(app, token, decisao, email="mae@exemplo.org", declaro=True):
    responsavel = TestClient(app)  # outra pessoa, outro navegador
    pagina = responsavel.get(f"/responsavel/{token}")
    if pagina.status_code != 200:
        return pagina
    dados = {"csrf_token": re.search(r'name="csrf_token" value="([^"]+)"', pagina.text).group(1), "decisao": decisao, "email_responsavel": email}
    if declaro:
        dados["declaro"] = "on"
    return responsavel.post(f"/responsavel/{token}", data=dados)


def agendar(app, client):
    hid = primeiro_horario_livre(app)
    return client.post(f"/monitorias/{hid}/agendar", data={"csrf_token": csrf(client, "/monitorias")}, follow_redirects=False)


# ---------- Cadastro mínimo ----------


def test_cadastro_nao_pede_nome_nem_email_do_estudante(client):
    html = client.get("/cadastro/estudante").text
    assert 'name="apelido"' in html and 'name="faixa_idade"' in html
    assert 'name="nome"' not in html and 'name="email"' not in html


@pytest.mark.parametrize("apelido", ["ab", "Maria da Silva", "joão", "x" * 21, "-comeca"])
def test_apelido_invalido(client, apelido):
    r = cadastrar_estudante(client, apelido=apelido)
    assert r.status_code == 400 and "apelido" in r.text.lower()


def test_apelido_repetido(client):
    assert cadastrar_estudante(client, apelido="leo").status_code == 303
    outro = TestClient(client.app)
    r = cadastrar_estudante(outro, apelido="LEO")
    assert r.status_code == 400 and "em uso" in r.text


def test_estudante_entra_com_apelido(client):
    cadastrar_estudante(client, apelido="Bia.Ok")
    client.post("/sair", data={"csrf_token": csrf(client, "/monitorias")})
    assert entrar(client, "bia.ok", "senha-forte-123").headers["location"] == "/monitorias"


def test_cadastro_registra_versao_do_aviso(app, client):
    cadastrar_estudante(client, apelido="aviso.ok")
    with app.state.SessionLocal() as db:
        u = db.query(Usuario).filter_by(apelido="aviso.ok").one()
        assert u.aviso_versao and u.aviso_aceito_em
        assert u.nome is None and u.email is None


# ---------- Consentimento do responsável ----------


def test_menor_fica_pendente_e_nao_agenda(app, client):
    token, r = cadastrar_menor(client)
    assert "wa.me/?text=" in r.text and token in r.text  # botão do WhatsApp com o link
    with app.state.SessionLocal() as db:
        u = db.query(Usuario).filter_by(apelido="leo.mat").one()
        assert u.consentimento_status == "pendente"
        assert u.consentimento_token_hash and token not in u.consentimento_token_hash  # só o hash
    assert "Falta a autorização do responsável" in client.get("/monitorias").text
    assert agendar(app, client).status_code == 403


def test_responsavel_autoriza_e_estudante_agenda(app, client):
    token, _ = cadastrar_menor(client)
    pagina = TestClient(app).get(f"/responsavel/{token}").text
    assert "leo.mat" in pagina and "cifrado" in pagina
    r = decidir(app, token, "autorizar")
    assert r.status_code == 200 and "autorizado" in r.text
    with app.state.SessionLocal() as db:
        u = db.query(Usuario).filter_by(apelido="leo.mat").one()
        assert u.consentimento_status == "autorizado" and u.consentimento_em
        assert u.email_responsavel_cifrado and "mae@exemplo.org" not in u.email_responsavel_cifrado
        assert app.state.cifra.decifrar(u.email_responsavel_cifrado) == "mae@exemplo.org"
        assert u.consentimento_token_hash is None
    assert agendar(app, client).status_code == 303


def test_link_e_de_uso_unico(app, client):
    token, _ = cadastrar_menor(client)
    decidir(app, token, "autorizar")
    assert decidir(app, token, "autorizar").status_code == 404


def test_autorizar_exige_email_e_declaracao(app, client):
    token, _ = cadastrar_menor(client)
    assert decidir(app, token, "autorizar", email="nao-e-email").status_code == 400
    assert decidir(app, token, "autorizar", declaro=False).status_code == 400
    with app.state.SessionLocal() as db:
        assert db.query(Usuario).filter_by(apelido="leo.mat").one().consentimento_status == "pendente"


def test_responsavel_nega_e_cadastro_e_apagado(app, client):
    token, _ = cadastrar_menor(client)
    r = decidir(app, token, "negar", email="")
    assert r.status_code == 200 and "apagados" in r.text
    with app.state.SessionLocal() as db:
        assert db.query(Usuario).filter_by(apelido="leo.mat").first() is None


def test_novo_link_invalida_o_anterior(app, client):
    antigo, _ = cadastrar_menor(client)
    r = client.post("/minha-conta/responsavel", data={"csrf_token": csrf(client, "/minha-conta/responsavel")})
    novo = LINK_RE.search(r.text).group(1)
    assert novo != antigo
    assert TestClient(app).get(f"/responsavel/{antigo}").status_code == 404
    assert TestClient(app).get(f"/responsavel/{novo}").status_code == 200


def test_maior_de_idade_nao_precisa_de_responsavel(app, client):
    assert cadastrar_estudante(client, apelido="adulto").status_code == 303
    assert agendar(app, client).status_code == 303


def test_link_vencido_nao_vale(app, client):
    token, _ = cadastrar_menor(client)
    with app.state.SessionLocal() as db:
        db.query(Usuario).filter_by(apelido="leo.mat").one().consentimento_expira_em = datetime.now() - timedelta(minutes=1)
        db.commit()
    assert TestClient(app).get(f"/responsavel/{token}").status_code == 404


def test_expurgo_apaga_pendentes_com_mais_de_30_dias(app, client):
    cadastrar_menor(client, apelido="velho")
    cadastrar_menor(TestClient(app), apelido="novo")
    with app.state.SessionLocal() as db:
        db.query(Usuario).filter_by(apelido="velho").one().criado_em = datetime.now() - timedelta(days=31)
        db.commit()
        assert expurgar_pendentes(db) == 1
        assert db.query(Usuario).filter_by(apelido="velho").first() is None
        assert db.query(Usuario).filter_by(apelido="novo").one()
        assert db.query(Usuario).filter_by(apelido="estudante.demo").one()  # autorizado: nunca expurgado


def test_api_de_expurgo_exige_chave(client):
    assert client.post("/api/v1/manutencao/expurgo").status_code == 401
    assert client.post("/api/v1/manutencao/expurgo", headers={"X-API-Key": API_KEY}).json() == {"apagados": 0}


# ---------- Direitos do titular ----------


def test_baixar_meus_dados(app, client):
    token, _ = cadastrar_menor(client)
    decidir(app, token, "autorizar")
    agendar(app, client)
    r = client.get("/minha-conta/dados.json")
    assert r.status_code == 200 and "attachment" in r.headers["content-disposition"]
    dados = r.json()
    assert dados["conta"]["apelido"] == "leo.mat"
    assert dados["conta"]["consentimento"]["email_do_responsavel"] == "mae@exemplo.org"
    assert len(dados["agendamentos"]) == 1
    texto = json.dumps(dados)
    assert "senha" not in texto and "token" not in texto


def test_apagar_conta_exige_senha_e_apaga_tudo(app, client):
    cadastrar_estudante(client, apelido="tchau")
    agendar(app, client)
    token = csrf(client, "/minha-conta")
    assert client.post("/minha-conta/apagar", data={"csrf_token": token, "senha": "errada"}).status_code == 400
    r = client.post("/minha-conta/apagar", data={"csrf_token": token, "senha": "senha-forte-123"}, follow_redirects=False)
    assert r.status_code == 303 and "conta_apagada" in r.headers["location"]
    with app.state.SessionLocal() as db:
        assert db.query(Usuario).filter_by(apelido="tchau").first() is None
        assert db.query(Agendamento).count() == 0
    assert client.get("/minha-conta", follow_redirects=False).status_code == 303  # sessão encerrada


def test_voluntario_apaga_conta_com_horarios(app, client):
    email = cadastrar_voluntario(client, app, email="sai@exemplo.org")
    amanha = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    client.post("/voluntario/horarios", data={"csrf_token": csrf(client, "/voluntario"), "materia": "Física", "data": amanha, "hora": "18:00"})
    dados = client.get("/minha-conta/dados.json").json()
    assert dados["conta"]["email"] == email and len(dados["horarios"]) == 1
    client.post("/minha-conta/apagar", data={"csrf_token": csrf(client, "/minha-conta"), "senha": "senha-forte-123"})
    with app.state.SessionLocal() as db:
        assert db.query(Usuario).filter_by(email=email).first() is None


# ---------- Papéis ----------


def test_voluntario_novo_espera_aprovacao(app, client):
    email = cadastrar_voluntario(client, app, email="novo.vol@exemplo.org", aprovar=False)
    assert "em análise" in client.get("/voluntario").text
    amanha = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    r = client.post("/voluntario/horarios", data={"csrf_token": csrf(client, "/voluntario"), "materia": "Física", "data": amanha, "hora": "18:00"})
    assert r.status_code == 403

    coord = TestClient(app)
    entrar(coord, "coordenacao.demo@exemplo.org", "coordenacao123")
    pagina = coord.get("/coordenacao/voluntarios").text
    assert email in pagina
    with app.state.SessionLocal() as db:
        vid = db.query(Usuario).filter_by(email=email).one().id
    coord.post(f"/coordenacao/voluntarios/{vid}", data={"csrf_token": csrf(coord, "/coordenacao/voluntarios"), "decisao": "aprovar"})
    with app.state.SessionLocal() as db:
        assert db.query(Usuario).filter_by(email=email).one().aprovado is True


def test_coordenacao_recusa_voluntario(app, client):
    coord = TestClient(app)
    entrar(coord, "coordenacao.demo@exemplo.org", "coordenacao123")
    with app.state.SessionLocal() as db:
        vid = db.query(Usuario).filter_by(email="voluntario5@exemplo.org").one().id  # em análise no seed
    coord.post(f"/coordenacao/voluntarios/{vid}", data={"csrf_token": csrf(coord, "/coordenacao/voluntarios"), "decisao": "recusar"})
    with app.state.SessionLocal() as db:
        assert db.get(Usuario, vid) is None


def test_so_coordenacao_aprova(app, client):
    cadastrar_estudante(client)
    assert client.get("/coordenacao/voluntarios").status_code == 403


# ---------- Indicadores e auditoria ----------


def test_suprimir_grupos_pequenos():
    assert [suprimir(n) for n in (0, 1, 4, 5, 12)] == [0, None, None, 5, 12]


def test_impacto_esconde_grupos_menores_que_5_e_ignora_pendentes(app, client):
    cadastrar_menor(client)  # pendente: não conta
    k = client.get("/api/v1/impacto").json()
    assert k["estudantes_cadastrados"] is None  # só o estudante demo autorizado: 1 < 5
    assert k["k_minimo"] == 5
    with app.state.SessionLocal() as db:
        assert db.query(Usuario).filter_by(papel="estudante").count() == 2
    for i in range(4):
        cadastrar_estudante(TestClient(app), apelido=f"adulto{i}")
    assert client.get("/api/v1/impacto").json()["estudantes_cadastrados"] == 5
    assert "Estudantes cadastrados</td><td>5<" in client.get("/impacto").text


def test_auditoria_registra_acao_sem_dados_pessoais(app, client):
    token, _ = cadastrar_menor(client)
    decidir(app, token, "autorizar")
    with app.state.SessionLocal() as db:
        acoes = [a.acao for a in db.query(Auditoria).order_by(Auditoria.id)]
        assert acoes[-2:] == ["cadastro_estudante", "consentimento_autorizado"]
        for a in db.query(Auditoria):
            texto = f"{a.acao} {a.papel} {a.ator}"
            assert "leo.mat" not in texto and "@" not in texto


def test_cifra_rejeita_chave_errada():
    a = Cifra(Cifra.chave_de_desenvolvimento("um"))
    b = Cifra(Cifra.chave_de_desenvolvimento("outro"))
    token = a.cifrar("x@exemplo.org")
    assert a.decifrar(token) == "x@exemplo.org"
    assert b.decifrar(token) is None


def test_producao_exige_fernet_key(monkeypatch):
    from app.config import Settings

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "x" * 64)
    monkeypatch.setenv("INTEGRATION_API_KEY", "y" * 32)
    monkeypatch.delenv("FERNET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="FERNET_KEY"):
        Settings()


def test_banco_da_primeira_versao_e_migrado(tmp_path):
    """Banco antigo: nome/e-mail obrigatórios. Estudantes viram apelido, sem nome nem e-mail."""
    caminho = tmp_path / "v1.db"
    con = sqlite3.connect(caminho)
    con.executescript(
        """
        CREATE TABLE escolas (id INTEGER PRIMARY KEY, nome VARCHAR(200) NOT NULL, bairro VARCHAR(120) NOT NULL,
          municipio VARCHAR(120) NOT NULL, territorio_prioritario BOOLEAN NOT NULL, indice_prioridade FLOAT,
          fonte_prioridade VARCHAR(40) NOT NULL);
        CREATE TABLE usuarios (id INTEGER PRIMARY KEY, nome VARCHAR(120) NOT NULL, email VARCHAR(200) NOT NULL UNIQUE,
          senha_hash VARCHAR(300) NOT NULL, papel VARCHAR(20) NOT NULL, criado_em DATETIME NOT NULL,
          escola_id INTEGER REFERENCES escolas(id), ano_escolar VARCHAR(40), bairro VARCHAR(120),
          consentimento_responsavel BOOLEAN NOT NULL, consentimento_em DATETIME, formacao VARCHAR(200));
        INSERT INTO usuarios VALUES (1, 'Ana Real', 'ana@exemplo.org', 'x', 'estudante', '2026-11-01 10:00:00', NULL, '9º ano EF', NULL, 1, '2026-11-01 10:00:00', NULL);
        INSERT INTO usuarios VALUES (2, 'Vol Real', 'vol@exemplo.org', 'x', 'voluntario', '2026-11-01 10:00:00', NULL, NULL, NULL, 0, NULL, 'Letras');
        """
    )
    con.commit()
    con.close()
    app = create_app(database_url=f"sqlite:///{caminho}", seed=False)
    with app.state.SessionLocal() as db:
        ana = db.get(Usuario, 1)
        assert (ana.apelido, ana.nome, ana.email, ana.consentimento_status) == ("estudante1", None, None, "autorizado")
        vol = db.get(Usuario, 2)
        assert (vol.nome, vol.email, vol.aprovado) == ("Vol Real", "vol@exemplo.org", True)

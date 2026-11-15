"""Testes da Visão Computacional (endereço a partir da foto da conta).

O OCR é sempre simulado: o CI não instala o EasyOCR. A geometria (cantos do papel,
correção de perspectiva) e a leitura de imagem/PDF usam OpenCV e pypdfium2 de verdade.
"""
import io
import re
import sqlite3

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

import app.main as main_mod
from app.main import create_app, normalizar_cep
from app.models import Usuario
from app.visao import (
    ArquivoInvalido,
    LeitorEndereco,
    achar_cantos_do_papel,
    carregar_imagem,
    corrigir_perspectiva,
    detectar_empresa,
    extrair_campos,
    ordenar_cantos,
)

CSRF_META_RE = re.compile(r'<meta name="csrf-token" content="([^"]+)"')

CABECALHO_SABESP = "CONCESSIONÁRIA SABESP DE SÃO PAULO S.A.  SEDE CORPORATIVA: AV. DAS NAÇÕES UNIDAS, 14401 - SÃO PAULO/SP - CEP: 04794-000"
ENDERECO_SABESP = (
    "ENDEREÇO DO IMÓVEL / LIGAÇÃO DE ÁGUA  NOME: LUCAS PEREIRA  AVENIDA RUA DOS PALMARES, 141  "
    "GRAJAU - SÃO PAULO/SP  CEP: 07657-532"
)


def png(largura=600, altura=800) -> bytes:
    img = np.full((altura, largura, 3), 255, np.uint8)
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return buf.tobytes()


def ocr_fixo(*textos):
    """OCR simulado: devolve os textos na ordem das chamadas (cabeçalho, depois endereço)."""
    fila = list(textos)
    chamadas = []

    def ler(imagem):
        chamadas.append(imagem.shape)
        return fila.pop(0) if fila else ""

    ler.chamadas = chamadas
    return ler


@pytest.fixture()
def app(tmp_path):
    a = create_app(database_url=f"sqlite:///{tmp_path / 'teste.db'}", seed=True)
    a.state.visao = LeitorEndereco(ocr_fixo(CABECALHO_SABESP, ENDERECO_SABESP))
    return a


@pytest.fixture()
def client(app):
    return TestClient(app)


def token(client):
    return CSRF_META_RE.search(client.get("/cadastro/estudante").text).group(1)


def enviar(client, dados=None, tipo="image/png", csrf=None):
    csrf = token(client) if csrf is None else csrf
    return client.post(
        "/api/v1/visao/endereco",
        files={"arquivo": ("conta.png", dados if dados is not None else png(), tipo)},
        headers={"X-CSRF-Token": csrf},
    )


# ---------- Texto → campos ----------

def test_extrai_endereco_do_cliente_da_conta_sabesp():
    campos = extrair_campos(CABECALHO_SABESP + "  " + ENDERECO_SABESP)
    assert campos["logradouro"] == "Avenida Rua dos Palmares"
    assert campos["numero"] == "141"
    assert campos["bairro"] == "Grajau"
    assert campos["cep"] == "07657-532"  # o CEP da sede (04794-000) é ignorado
    assert campos["uf"] == "SP"


def test_ignora_endereco_da_sede_e_normaliza_cep():
    texto = "ENEL DISTRIBUIÇÃO SEDE: AV. DAS NAÇÕES UNIDAS, 14401 CEP 04794-000  DADOS DO CLIENTE  RUA DAS FLORES, 692  BAIRRO: BRASILANDIA  CEP 07825 441"
    campos = extrair_campos(texto)
    assert campos["logradouro"] == "Rua das Flores"
    assert campos["numero"] == "692"
    assert campos["bairro"] == "Brasilandia"
    assert campos["cep"] == "07825-441"


def test_texto_da_entrega_original():
    """Mesmo caso do test_cv.py da entrega."""
    campos = extrair_campos("CLIENTE: CARLOS SILVA RUA DOMINGOS DE MORAIS, Nº 2500 VILA MARIANA SAO PAULO SP CEP: 04036-100")
    assert campos["cep"] == "04036-100"
    assert campos["numero"] == "2500"
    assert campos["logradouro"] == "Rua Domingos de Morais"


def test_numero_de_data_nao_vira_numero_da_casa():
    campos = extrair_campos("EMISSÃO RUA X 05/11/2026  ESTRADA DO COPO, 1895  ITAQUERA - SÃO PAULO/SP")
    assert campos["logradouro"] == "Estrada do Copo"
    assert campos["numero"] == "1895"
    assert campos["bairro"] == "Itaquera"


@pytest.mark.parametrize(
    "texto, numero, bairro, cep",
    [
        # Saídas reais do EasyOCR sobre o dataset sintético da entrega (palavras grudadas, "Nº" mal lido).
        ("DADOS DO CLIENTE  RUA RUA DASFLORES NE692 BAIRRO BRASILANDIA MUNICEPIO SOPAULO - SP CEP  07825-441", "692", "Brasilandia", "07825-441"),
        ("AVENIDA PRINCIPAL NI6O3 BAIRRO ITAQUERA MUNICEPIO SOPAULO - SP CEP  09624-902", "603", "Itaquera", "09624-902"),
        ("ENDEREODOINEVEL /LIGATODEDGUA  NOME LUCASPEREIRA  AVENIDA RUABOAVISTA 1336  ITHQUERA-SDPHULOISP  CEP 06230-731", "1336", "Ithquera", "06230-731"),
        ("DESTINAIERIODAFATURA  MARIADASILVA  FUAFUABOAVSTA 3489  GRAJAU  SDPAULO- SP 01535-303", "3489", "Grajau", "01535-303"),
    ],
)
def test_texto_com_ruido_de_ocr(texto, numero, bairro, cep):
    campos = extrair_campos(texto)
    assert (campos["numero"], campos["bairro"], campos["cep"]) == (numero, bairro, cep)


def test_texto_sem_endereco():
    assert extrair_campos("DOCUMENTO QUALQUER SEM DADOS") == {"logradouro": None, "numero": None, "bairro": None, "cep": None, "uf": None}


def test_detecta_concessionaria():
    assert detectar_empresa("CONTA DE ENERGIA ENEL DISTRIBUIÇÃO") == "ENEL"
    assert detectar_empresa("COMPANHIA SABESP DE SANEAMENTO") == "SABESP"
    assert detectar_empresa("FATURA CLARO BRASIL") == "CLARO"
    assert detectar_empresa("DOCUMENTO GENÉRICO") is None


def test_normalizar_cep():
    assert normalizar_cep("01234567") == "01234-567"
    assert normalizar_cep(" 01.234-567 ") == "01234-567"
    assert normalizar_cep("") is None
    with pytest.raises(ValueError):
        normalizar_cep("1234")


# ---------- Geometria e entrada ----------

def test_ordena_cantos():
    rect = ordenar_cantos(np.array([[100, 200], [0, 0], [100, 0], [0, 200]]))
    assert rect.tolist() == [[0, 0], [100, 0], [100, 200], [0, 200]]


def test_acha_papel_inclinado_e_corrige_perspectiva():
    foto = np.full((900, 700, 3), 40, np.uint8)  # mesa escura
    papel = np.array([[150, 120], [560, 170], [600, 780], [110, 740]], np.int32)  # papel torto
    cv2.fillPoly(foto, [papel], (245, 245, 245))
    cantos = achar_cantos_do_papel(foto)
    assert np.abs(ordenar_cantos(cantos) - papel).max() < 12
    plano = corrigir_perspectiva(foto, cantos)
    assert 470 < plano.shape[1] < 510 and 590 < plano.shape[0] < 640  # maior largura (490) e altura (620) do papel
    assert plano.mean() > 200  # sobrou só o papel


def test_sem_papel_usa_a_foto_inteira():
    foto = np.full((300, 200, 3), 255, np.uint8)
    assert ordenar_cantos(achar_cantos_do_papel(foto)).tolist() == [[0, 0], [199, 0], [199, 299], [0, 299]]


def test_carrega_pdf_e_reduz_imagem_grande():
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument.new()
    pdf.new_page(595, 842)
    buf = io.BytesIO()
    pdf.save(buf)
    img = carregar_imagem(buf.getvalue())
    assert img.ndim == 3 and max(img.shape[:2]) <= 3000

    grande = carregar_imagem(png(4500, 3000))
    assert max(grande.shape[:2]) == 3000


def test_arquivo_invalido():
    with pytest.raises(ArquivoInvalido):
        carregar_imagem(b"isto nao e imagem")
    with pytest.raises(ArquivoInvalido):
        carregar_imagem(b"%PDF-1.4 quebrado")


# ---------- API ----------

def test_api_devolve_campos_para_conferir(app, client):
    r = enviar(client)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d == {
        "logradouro": "Avenida Rua dos Palmares",
        "numero": "141",
        "bairro": "Grajau",
        "cep": "07657-532",
        "uf": "SP",
        "empresa": "SABESP",
        "empresa_nome": "Sabesp (água)",
        "confianca": 1.0,
        "fonte": "ocr",
    }
    assert len(app.state.visao.ocr.chamadas) == 2  # cabeçalho + região do endereço


def test_api_nao_grava_nada(app, client):
    enviar(client)
    with app.state.SessionLocal() as db:
        assert db.query(Usuario).filter(Usuario.cep.is_not(None)).count() == 0


def test_api_tenta_pagina_inteira_quando_regiao_nao_tem_endereco(app, client):
    app.state.visao = LeitorEndereco(ocr_fixo("CLARO", "NADA AQUI", "FATURA CLARO  RUA BOA VISTA, 2089  CAPAO REDONDO - SÃO PAULO/SP  CEP 01929-465"))
    d = enviar(client).json()
    assert (d["empresa"], d["bairro"], d["cep"]) == ("CLARO", "Capao Redondo", "01929-465")


def test_imagem_estreita_nao_explode_de_tamanho():
    ocr = ocr_fixo()
    LeitorEndereco(ocr).ler(png(largura=8, altura=3000))
    assert ocr.chamadas and all(s[0] * s[1] <= 2400 * 4800 for s in ocr.chamadas)


def test_api_exige_csrf(client):
    assert enviar(client, csrf="errado").status_code == 403


def test_api_rejeita_tipo_tamanho_e_arquivo_quebrado(client, monkeypatch):
    assert enviar(client, tipo="text/plain").status_code == 415
    assert enviar(client, dados=b"nao e imagem").status_code == 422
    monkeypatch.setattr(main_mod, "MAX_BYTES", 100)
    r = enviar(client)
    assert r.status_code == 413
    assert "8 MB" in r.json()["detail"]


def test_api_sem_ocr_instalado(app, client):
    app.state.visao = LeitorEndereco(None)
    d = enviar(client).json()
    assert d["fonte"] == "indisponivel" and d["cep"] is None


def test_api_falha_do_ocr_vira_resposta_vazia(app, client):
    def quebrado(imagem):
        raise RuntimeError("modelo não carregou")

    app.state.visao = LeitorEndereco(quebrado)
    d = enviar(client).json()
    assert d["fonte"] == "erro" and d["confianca"] == 0


def test_api_limite_por_minuto(app, client):
    app.state.visao = LeitorEndereco(ocr_fixo(), por_minuto=2)
    t = token(client)
    assert [enviar(client, csrf=t).status_code for _ in range(3)] == [200, 200, 429]


# ---------- Cadastro ----------

def test_tela_de_cadastro_mostra_foto_so_com_ocr(app, client):
    html = client.get("/cadastro/estudante").text
    assert 'id="visao"' in html and "visao.js" in html
    app.state.visao = LeitorEndereco(None)
    html = client.get("/cadastro/estudante").text
    assert 'id="visao"' not in html and 'name="cep"' in html


def dados_cadastro(client, **extra):
    html = client.get("/cadastro/estudante").text
    escola_id = re.search(r'<option value="(\d+)"', html).group(1)
    return {
        "csrf_token": re.search(r'name="csrf_token" value="([^"]+)"', html).group(1),
        "nome": "Bia",
        "email": "bia@exemplo.org",
        "senha": "senha-segura",
        "escola_id": escola_id,
        "ano_escolar": "9º ano EF",
        "consentimento": "on",
        **extra,
    }


def test_cadastro_grava_bairro_e_cep_confirmados(app, client):
    r = client.post("/cadastro/estudante", data=dados_cadastro(client, bairro="Grajau", cep="07657532"), follow_redirects=False)
    assert r.status_code == 303
    with app.state.SessionLocal() as db:
        u = db.query(Usuario).filter_by(email="bia@exemplo.org").one()
        assert (u.bairro, u.cep) == ("Grajau", "07657-532")


def test_cadastro_rejeita_cep_invalido(client):
    r = client.post("/cadastro/estudante", data=dados_cadastro(client, cep="123"), follow_redirects=False)
    assert r.status_code == 400
    assert "8 números" in r.text


def test_banco_antigo_ganha_coluna_cep(tmp_path):
    caminho = tmp_path / "antigo.db"
    con = sqlite3.connect(caminho)
    con.execute("CREATE TABLE usuarios (id INTEGER PRIMARY KEY, nome VARCHAR(120), email VARCHAR(200), senha_hash VARCHAR(300), papel VARCHAR(20))")
    con.commit()
    con.close()
    create_app(database_url=f"sqlite:///{caminho}", seed=False)
    con = sqlite3.connect(caminho)
    colunas = {linha[1] for linha in con.execute("PRAGMA table_info(usuarios)")}
    con.close()
    assert "cep" in colunas

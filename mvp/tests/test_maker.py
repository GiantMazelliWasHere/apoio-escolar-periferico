"""Integração com a peça do Maker Lab: QR code → /qr → cadastro com origem → painel de impacto."""
import re

import cv2
import numpy as np
from fastapi.testclient import TestClient

from app.maker import matriz_qr, qr_svg, url_do_qr
from app.models import Usuario

from .test_fluxo import app, cadastrar_estudante, client, csrf  # noqa: F401  (fixtures)


def decodificar(matriz) -> str:
    img = np.array([[0 if v else 255 for v in linha] for linha in matriz], dtype=np.uint8)
    img = cv2.resize(img, None, fx=10, fy=10, interpolation=cv2.INTER_NEAREST)
    texto, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
    return texto


def test_qr_codifica_a_url_publica():
    url = url_do_qr("https://apoio-escolar.azurewebsites.net/")
    assert url == "https://apoio-escolar.azurewebsites.net/qr"
    assert decodificar(matriz_qr(url)) == url


def test_qr_svg_tem_tamanho_fisico():
    svg = qr_svg("https://exemplo.org/qr", tamanho_mm=40)
    assert svg.startswith("<svg") and 'width="40mm"' in svg and "<rect" in svg


def test_endpoint_svg_usa_public_url(tmp_path, monkeypatch):
    monkeypatch.setenv("PUBLIC_URL", "https://apoio-escolar.azurewebsites.net")
    from app.main import create_app

    c = TestClient(create_app(database_url=f"sqlite:///{tmp_path / 'm.db'}", seed=False))
    r = c.get("/maker/qrcode.svg?tamanho_mm=500")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/svg+xml")
    assert 'width="200mm"' in r.text  # limitado
    assert "https://apoio-escolar.azurewebsites.net/qr" in r.text


def test_pagina_maker(client):
    r = client.get("/maker")
    assert r.status_code == 200
    assert "Suporte de tablet" in r.text
    assert "http://testserver/qr" in r.text
    assert "<svg" in r.text


def test_cadastro_pelo_qr_conta_no_impacto(client, app):
    antes = client.get("/api/v1/impacto").json()["cadastros_via_peca_maker"]

    r = client.get("/qr", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/"
    assert "QR code do" in client.get("/").text

    assert cadastrar_estudante(client, email="qr@exemplo.org").status_code == 303
    with app.state.SessionLocal() as db:
        assert db.query(Usuario).filter_by(email="qr@exemplo.org").one().origem == "peca_maker"

    depois = client.get("/api/v1/impacto").json()["cadastros_via_peca_maker"]
    assert depois == antes + 1
    assert re.search(r"Cadastros vindos da peça Maker Lab</td><td>\d+", client.get("/impacto").text)


def test_cadastro_sem_qr_nao_tem_origem(client, app):
    assert cadastrar_estudante(client, email="direto@exemplo.org").status_code == 303
    with app.state.SessionLocal() as db:
        assert db.query(Usuario).filter_by(email="direto@exemplo.org").one().origem is None

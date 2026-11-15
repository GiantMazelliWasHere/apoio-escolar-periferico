import os
import json
import pytest
from scanner import order_points
from ocr_engine import detect_company, parse_address_from_text
import numpy as np

def test_order_points_geometria():
    """Valida a ordenação correta dos 4 vértices do papel."""
    pts = np.array([
        [100, 200], # bl
        [0, 0],     # tl
        [100, 0],   # tr
        [0, 200]    # bl
    ])
    rect = order_points(pts)
    assert rect.shape == (4, 2)
    # Top-left deve ser o ponto com menor soma
    assert rect[0][0] == 0 and rect[0][1] == 0

def test_detect_company_concessionarias():
    """Testa identificação de Enel, Sabesp e Claro."""
    assert detect_company("CONTA DE ENERGIA ENEL DISTRIBUIÇÃO") == "ENEL"
    assert detect_company("COMPANHIA SABESP DE SANEAMENTO") == "SABESP"
    assert detect_company("FATURA CLARO BRASIL TELECOM") == "CLARO"
    assert detect_company("DOCUMENTO GENERICO QUALQUER") == "DESCONHECIDA"

def test_parse_address_regex():
    """Testa isolamento de CEP, logradouro e número via regex."""
    texto = "CLIENTE: CARLOS SILVA RUA DOMINGOS DE MORAIS, Nº 2500 VILA MARIANA SAO PAULO SP CEP: 04036-100"
    res = parse_address_from_text(texto)
    
    assert res["cep"] == "04036-100"
    assert res["numero"] == "2500"
    assert "Domingos De Morais" in res["logradouro"]
    assert res["uf"] == "SP"

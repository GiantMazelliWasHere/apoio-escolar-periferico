import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "dags"))

from etl_apoio_escolar import INDICE_MAXIMO, carregar, extrair, montar_payload, transformar  # noqa: E402


def test_trusted_so_tem_escolas_perifericas_ordenadas():
    trusted = transformar(extrair())
    assert len(trusted) == 4
    assert "EE Exemplo Centro Novo" not in set(trusted["nome_escola"])
    assert list(trusted["indice_prioridade"]) == sorted(trusted["indice_prioridade"], reverse=True)


def test_ideb_faltante_vira_media_do_recorte_e_nao_zero():
    trusted = transformar(extrair()).set_index("nome_escola")
    # média de 3.5, 4.1 e 3.8 = 3.8 → 10 - 3.8 + 2 (sem lab) + 2 (sem internet)
    assert trusted.loc["EE Exemplo Morro Azul", "ideb_anos_finais"] == pytest.approx(3.8)
    assert trusted.loc["EE Exemplo Morro Azul", "indice_prioridade"] == pytest.approx(10.2)
    assert trusted.loc["EE Exemplo Jardim das Flores", "indice_prioridade"] == pytest.approx(8.5)


def test_payload_segue_o_contrato_do_nucleo():
    payload = montar_payload(transformar(extrair()))
    assert {"codigo_inep", "territorio_prioritario", "indice_prioridade"} == set(payload[0])
    assert all(p["codigo_inep"].startswith("99") for p in payload)
    assert all(0 <= p["indice_prioridade"] <= 1 for p in payload)
    assert payload[0]["indice_prioridade"] == round(10.2 / INDICE_MAXIMO, 2)


def test_sem_url_a_carga_e_simulada(monkeypatch):
    monkeypatch.delenv("MVP_API_URL", raising=False)
    assert carregar([{"codigo_inep": "1"}]) == {"atualizadas": 0, "simulada": True}


def test_com_url_e_sem_chave_falha(monkeypatch):
    monkeypatch.delenv("INTEGRATION_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        carregar([], api_url="http://localhost:1")


def test_carga_envia_put_com_a_chave():
    recebido = {}

    class Handler(BaseHTTPRequestHandler):
        def do_PUT(self):
            recebido["path"] = self.path
            recebido["key"] = self.headers["X-API-Key"]
            recebido["body"] = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            corpo = json.dumps({"atualizadas": len(recebido["body"])}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(corpo)

        def log_message(self, *args):
            pass

    servidor = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=servidor.handle_request, daemon=True).start()
    payload = montar_payload(transformar(extrair()))
    resultado = carregar(payload, api_url=f"http://127.0.0.1:{servidor.server_port}/", api_key="chave-teste")
    servidor.server_close()

    assert resultado == {"atualizadas": 4}
    assert recebido["path"] == "/api/v1/escolas/prioridade"
    assert recebido["key"] == "chave-teste"
    assert recebido["body"] == payload

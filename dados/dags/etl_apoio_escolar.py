"""Etapas do ETL do Apoio Escolar Periférico, sem dependência do Airflow.

A DAG (`dag_etl_apoio_escolar.py`) chama estas funções em cada tarefa. Elas
ficam separadas para rodar e testar o pipeline também fora do Airflow
(`python rodar_local.py`), por exemplo no Windows, onde o Airflow não roda.

Regras de negócio da entrega de Big Data (Jó Sales):
- só escolas em região periférica entram na camada Trusted;
- Índice de Prioridade Educacional = (10 - IDEB) + 2 sem laboratório + 2 sem internet.

Mudanças da integração com o núcleo do MVP (documentadas em docs/INTEGRACAO.md):
- as escolas simuladas são as mesmas do seed do MVP, com código INEP fictício
  (prefixo 99, UF inexistente, para nunca coincidir com uma escola real);
- IDEB faltante é imputado pela média das escolas do recorte, não por zero
  (zero tornava a escola sem nota a mais prioritária de todas);
- a carga chama de verdade `PUT /api/v1/escolas/prioridade` no núcleo.
"""
from __future__ import annotations

import json
import os
import tempfile
import urllib.error
import urllib.request

import pandas as pd

DATA_PATH = os.environ.get("CITIZENTECH_DATA_PATH", os.path.join(tempfile.gettempdir(), "citizentech_data"))

# Maior valor possível do índice: IDEB 0, sem laboratório e sem internet.
INDICE_MAXIMO = 10 + 2 + 2

COLUNAS_TRUSTED = ["cod_municipio", "cod_escola", "nome_escola", "ideb_anos_finais", "indice_prioridade"]


def extrair() -> pd.DataFrame:
    """MOCK da extração INEP (Censo Escolar + IDEB) e IBGE (malha territorial).

    Dados SINTÉTICOS: as escolas são as fictícias do seed do MVP. Na versão com
    dados reais, este passo baixa os microdados do INEP e cruza com a malha do IBGE.
    """
    dados = {
        "cod_municipio": [3550308, 3550308, 3550308, 3550308, 3550308, 3550308],
        "cod_escola": [99000101, 99000102, 99000103, 99000104, 99000105, 99000106],
        "nome_escola": [
            "EE Exemplo Jardim das Flores",
            "EE Exemplo Vila Esperança",
            "EE Exemplo Parque do Sol",
            "EE Exemplo Morro Azul",
            "EE Exemplo Centro Novo",
            "EE Exemplo Bela Vista",
        ],
        "regiao_periferica": [1, 1, 1, 1, 0, 0],  # 1 = Sim, 0 = Não
        "ideb_anos_finais": [3.5, 4.1, 3.8, None, 6.2, 7.0],  # None simula dado faltante
        "qtd_alunos": [450, 600, 250, 320, 300, 800],
        "lab_informatica": [0, 0, 0, 0, 1, 1],
        "acesso_internet": [1, 0, 1, 0, 1, 1],
    }
    return pd.DataFrame(dados)


def calcular_prioridade(linha: pd.Series) -> float:
    score = 10 - linha["ideb_anos_finais"]  # menor nota = maior prioridade
    if linha["lab_informatica"] == 0:
        score += 2
    if linha["acesso_internet"] == 0:
        score += 2
    return round(float(score), 2)


def transformar(df: pd.DataFrame) -> pd.DataFrame:
    """Camada Trusted: recorte periférico, imputação do IDEB e índice de prioridade."""
    recorte = df[df["regiao_periferica"] == 1].copy()
    media_ideb = recorte["ideb_anos_finais"].mean()
    recorte["ideb_anos_finais"] = recorte["ideb_anos_finais"].fillna(round(media_ideb, 2))
    recorte["indice_prioridade"] = recorte.apply(calcular_prioridade, axis=1)
    recorte = recorte.sort_values(by="indice_prioridade", ascending=False)
    return recorte[COLUNAS_TRUSTED].reset_index(drop=True)


def montar_payload(trusted: pd.DataFrame) -> list[dict]:
    """Converte a camada Trusted no contrato do núcleo (índice normalizado de 0 a 1)."""
    return [
        {
            "codigo_inep": str(int(linha["cod_escola"])),
            "territorio_prioritario": True,
            "indice_prioridade": round(float(linha["indice_prioridade"]) / INDICE_MAXIMO, 2),
        }
        for _, linha in trusted.iterrows()
    ]


def carregar(payload: list[dict], api_url: str | None = None, api_key: str | None = None, timeout: int = 30) -> dict:
    """Envia a priorização ao núcleo do MVP.

    Configuração por variável de ambiente: `MVP_API_URL` (ex.: http://localhost:8000
    ou a URL do App Service) e `INTEGRATION_API_KEY` (a mesma do núcleo).
    Sem `MVP_API_URL`, a carga é só simulada (comportamento da entrega original).
    """
    api_url = (api_url or os.environ.get("MVP_API_URL") or "").rstrip("/")
    api_key = api_key or os.environ.get("INTEGRATION_API_KEY")
    if not api_url:
        print(f"MVP_API_URL não configurada: carga simulada de {len(payload)} escolas.")
        return {"atualizadas": 0, "simulada": True}
    if not api_key:
        raise RuntimeError("INTEGRATION_API_KEY não configurada: o núcleo recusaria a carga.")

    req = urllib.request.Request(
        f"{api_url}/api/v1/escolas/prioridade",
        data=json.dumps(payload).encode("utf-8"),
        method="PUT",
        headers={"Content-Type": "application/json", "X-API-Key": api_key},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resultado = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as erro:
        raise RuntimeError(f"O núcleo respondeu {erro.code} na carga de prioridade.") from erro

    if resultado.get("atualizadas", 0) < len(payload):
        print(
            f"Atenção: {len(payload) - resultado.get('atualizadas', 0)} escola(s) não existem no núcleo "
            "(código INEP não cadastrado) e foram ignoradas."
        )
    print(f"Carga concluída no núcleo: {resultado}")
    return resultado

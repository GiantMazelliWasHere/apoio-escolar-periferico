"""Roda o ETL de ponta a ponta sem o Airflow (mesmas funções da DAG).

Uso, com o núcleo do MVP rodando em http://localhost:8000:

    set MVP_API_URL=http://localhost:8000
    set INTEGRATION_API_KEY=<mesma chave do núcleo>
    .venv/Scripts/python rodar_local.py

Sem MVP_API_URL, a carga é só simulada.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "dags"))

from etl_apoio_escolar import DATA_PATH, carregar, extrair, montar_payload, transformar  # noqa: E402


def main() -> None:
    os.makedirs(DATA_PATH, exist_ok=True)
    bruto = extrair()
    bruto.to_csv(os.path.join(DATA_PATH, "raw_inep_ibge.csv"), index=False)
    print(f"[extract] {len(bruto)} escolas lidas (INEP/IBGE simulados)")

    trusted = transformar(bruto)
    trusted.to_csv(os.path.join(DATA_PATH, "trusted_escolas_prioritarias.csv"), index=False)
    print(f"[transform] {len(trusted)} escolas no recorte periférico:")
    print(trusted.to_string(index=False))

    payload = montar_payload(trusted)
    print(f"[load] {carregar(payload)}")


if __name__ == "__main__":
    main()

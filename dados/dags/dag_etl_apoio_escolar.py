from airflow.decorators import dag, task
from datetime import datetime
import pandas as pd
import os

# Lógica de cada etapa em módulo próprio (roda e é testada também sem o Airflow).
from etl_apoio_escolar import DATA_PATH, carregar, extrair, montar_payload, transformar

os.makedirs(DATA_PATH, exist_ok=True)

@dag(
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['citizentech', 'educacao', 'apoio-escolar']
)
def etl_apoio_escolar_periferico():
    """
    Pipeline de Dados do MVP: Apoio Escolar Periférico
    Extrai microdados simulados do INEP e IBGE, processa os indicadores de
    infraestrutura e notas (IDEB) e carrega a priorização no núcleo do MVP
    (PUT /api/v1/escolas/prioridade), que alimenta o painel de impacto.
    """

    @task()
    def extract_inep_ibge():
        # MOCK: Simula a extração via API ou download de CSV do INEP (Censo Escolar e IDEB)
        print("Iniciando extração de dados do INEP/IBGE...")
        df = extrair()
        raw_path = os.path.join(DATA_PATH, "raw_inep_ibge.csv")
        df.to_csv(raw_path, index=False)
        print(f"Extração concluída. Dados brutos salvos em {raw_path}")
        return raw_path

    @task()
    def transform_data(raw_path: str):
        # Camada Trusted: recorte periférico, imputação do IDEB e Índice de Prioridade Educacional
        print("Iniciando transformação e limpeza (ETL)...")
        df_final = transformar(pd.read_csv(raw_path))
        trusted_path = os.path.join(DATA_PATH, "trusted_escolas_prioritarias.csv")
        df_final.to_csv(trusted_path, index=False)
        print(f"Transformação concluída. Dados modelados salvos em {trusted_path}")
        print(df_final.to_string(index=False))
        return trusted_path

    @task()
    def load_to_azure(trusted_path: str):
        # Carga no núcleo do MVP (App Service na Azure ou local), pelo contrato de integração
        df_trusted = pd.read_csv(trusted_path)
        print(f"Preparando carga de {len(df_trusted)} escolas para o núcleo do MVP...")
        resultado = carregar(montar_payload(df_trusted))
        return f"Carga concluída: {resultado}"

    # Definição do Fluxo da DAG (Dependências)
    raw_data = extract_inep_ibge()
    trusted_data = transform_data(raw_data)
    load_to_azure(trusted_data)

# Instancia a DAG
etl_apoio_escolar_periferico()

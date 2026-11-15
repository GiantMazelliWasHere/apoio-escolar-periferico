from airflow.decorators import dag, task
from datetime import datetime
import pandas as pd
import os

# Configurações de diretórios temporários para o ETL
DATA_PATH = "/tmp/citizentech_data"
os.makedirs(DATA_PATH, exist_ok=True)

@dag(
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['citizentech', 'educacao', 'apoio-escolar']
)
def etl_apoio_escolar_periferico():
    """
    Pipeline de Dados do MVP: Apoio Escolar Periférico
    Extrai microdados simulados do INEP e IBGE, processa os indicadores de 
    infraestrutura e notas (IDEB), e carrega a tabela priorizada para o banco na Azure.
    """

    @task()
    def extract_inep_ibge():
        # MOCK: Simula a extração via API ou download de CSV do INEP (Censo Escolar e IDEB)
        print("Iniciando extração de dados do INEP/IBGE...")
        data = {
            'cod_municipio': [3550308, 3550308, 3550308, 3509502, 3304557, 3550308],
            'cod_escola': [101, 102, 103, 104, 105, 106],
            'nome_escola': ['Escola Estadual A', 'Escola Municipal B', 'Escola Estadual C', 'Escola D', 'Escola E', 'Escola F'],
            'regiao_periferica': [1, 0, 1, 1, 0, 1], # 1 = Sim, 0 = Não
            'ideb_anos_finais': [3.5, 6.2, 4.1, 3.8, 7.0, None], # None simula dado faltante
            'qtd_alunos': [450, 300, 600, 250, 800, 320],
            'lab_informatica': [0, 1, 0, 0, 1, 0],
            'acesso_internet': [1, 1, 0, 1, 1, 0]
        }
        df = pd.DataFrame(data)
        raw_path = os.path.join(DATA_PATH, "raw_inep_ibge.csv")
        df.to_csv(raw_path, index=False)
        print(f"Extração concluída. Dados brutos salvos em {raw_path}")
        return raw_path

    @task()
    def transform_data(raw_path: str):
        # MOCK: Simula a camada de Transformação (Limpeza e Modelagem)
        print("Iniciando transformação e limpeza (ETL)...")
        df = pd.read_csv(raw_path)

        # 1. Filtra apenas escolas mapeadas em regiões periféricas (Regra de Negócio do MVP)
        df_filtered = df[df['regiao_periferica'] == 1].copy()

        # 2. Tratamento de nulos no IDEB (substitui nulos pela média ou zero)
        df_filtered['ideb_anos_finais'] = df_filtered['ideb_anos_finais'].fillna(0)

        # 3. Engenharia de Features: Cálculo do 'Índice de Prioridade Educacional'
        # Escolas com IDEB menor e sem infraestrutura ganham maior pontuação de prioridade
        def calc_prioridade(row):
            score = 10 - row['ideb_anos_finais'] # Inverte o IDEB (menor nota = maior prioridade)
            if row['lab_informatica'] == 0:
                score += 2 # Penalidade por falta de laboratório
            if row['acesso_internet'] == 0:
                score += 2 # Penalidade por falta de internet
            return round(score, 2)

        df_filtered['indice_prioridade'] = df_filtered.apply(calc_prioridade, axis=1)

        # 4. Ordenação final para a camada Trusted
        df_trusted = df_filtered.sort_values(by='indice_prioridade', ascending=False)
        
        # Seleciona apenas as colunas que o banco de dados do MVP precisa
        colunas_finais = ['cod_municipio', 'cod_escola', 'nome_escola', 'ideb_anos_finais', 'indice_prioridade']
        df_final = df_trusted[colunas_finais]

        trusted_path = os.path.join(DATA_PATH, "trusted_escolas_prioritarias.csv")
        df_final.to_csv(trusted_path, index=False)
        print(f"Transformação concluída. Dados modelados salvos em {trusted_path}")
        return trusted_path

    @task()
    def load_to_azure(trusted_path: str):
        # MOCK: Simula a carga dos dados no banco relacional da Azure usado pelo MVP
        df_trusted = pd.read_csv(trusted_path)
        
        print(f"Preparando carga de {len(df_trusted)} registros para o Azure SQL Database...")
        # Código real usaria SQLAlchemy: df_trusted.to_sql('escolas_alvo', con=azure_engine, if_exists='replace')
        
        print("Carga finalizada com sucesso!")
        print("Amostra dos dados carregados para o MVP:")
        print(df_trusted.head())
        return "Carga Azure Concluída"

    # Definição do Fluxo da DAG (Dependências)
    raw_data = extract_inep_ibge()
    trusted_data = transform_data(raw_data)
    load_to_azure(trusted_data)

# Instancia a DAG
etl_apoio_escolar_periferico()

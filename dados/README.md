# Ficha Técnica - MVP: Apoio Escolar Periférico

**Componente Avaliado:** Big Data Architecture & Data Integration  
**Disciplina:** Global Solution 2026.2 - CitizenTech (Engenharia de Software 4º Ano)

---

## 1. Ficha Técnica do MVP

* **Nome do produto:** Apoio Escolar Periférico
* **Cidadão e território:** Estudantes de escolas públicas em comunidades periféricas.
* **Problema, em uma frase:** A falta de suporte educacional extraclasse e de infraestrutura digital agrava a defasagem escolar e a exclusão tecnológica em áreas vulneráveis.
* **Proposta de valor:** Plataforma que conecta estudantes de baixa renda a vagas de monitoria voluntária, materiais digitais e trilhas de inclusão tecnológica, usando dados para priorizar o atendimento.
* **Arquitetura (componentes):** Airflow (ETL de Dados INEP/IBGE) -> Azure SQL (Banco do MVP) -> Web App (Interface DevOps/Cloud) -> OCR (Visão Computacional) -> Tutor IA (Inteligência Generativa) -> RPA UiPath (Automação de cadastros).
* **Fontes de dados:** Microdados do INEP (Censo Escolar e IDEB) e IBGE (Malha Territorial). *Nota: Para viabilidade do protótipo, foi gerado um mock justificado no pipeline simulando a extração dessas bases governamentais.*
* **Modelos de IA utilizados:** OCR (para leitura de comprovantes de endereço) e LLM (para o assistente virtual Tutor IA adaptativo).
* **URL do MVP e repositório:** [INSERIR_LINK_DA_AZURE] | [INSERIR_LINK_DO_GITHUB]
* **Indicadores de impacto:** Número de alunos engajados; Horas de monitoria ministradas; Aumento simulado na taxa de retenção escolar.
* **ODS conectados:** ODS 4 (Educação de Qualidade) e ODS 10 (Redução das Desigualdades).

---

## 2. Arquitetura do Pipeline (ETL)

O pipeline foi orquestrado utilizando **Apache Airflow** (TaskFlow API) contemplando três etapas:
1. **Extract (`extract_inep_ibge`):** Ingestão de dados de infraestrutura e notas escolares.
2. **Transform (`transform_data`):** Filtragem de regiões periféricas, tratamento de nulos e cálculo do *Índice de Prioridade Educacional* (escolas com menor IDEB e sem infraestrutura pontuam mais alto para receberem apoio primeiro).
3. **Load (`load_to_azure`):** Carga dos dados tratados no banco relacional da aplicação (simulação de insert no Azure SQL).

*(Lembre-se de anexar o diagrama visual e os prints do Airflow rodando no PDF final da entrega).*

---

## 3. Dicionário de Dados (Camada Trusted)

| Tabela Destino | Coluna | Tipo de Dado | Chave | Descrição |
| :--- | :--- | :--- | :--- | :--- |
| `escolas_alvo` | `cod_municipio` | INT | FK | Código do município padrão IBGE (Ex: 3550308). |
| `escolas_alvo` | `cod_escola` | INT | PK | Código único da escola no Censo INEP. |
| `escolas_alvo` | `nome_escola` | VARCHAR | - | Nome oficial da instituição de ensino. |
| `escolas_alvo` | `ideb_anos_finais`| FLOAT | - | Nota do IDEB referente aos anos finais do ensino fundamental. |
| `escolas_alvo` | `indice_prioridade`| FLOAT | - | Índice calculado via ETL. Quanto maior, maior a vulnerabilidade digital e educacional da escola. |

---

## 4. Instruções para Executar o Pipeline

1. Instale as dependências: `pip install -r requirements.txt`
2. Configure a pasta dags no seu ambiente Airflow: `export AIRFLOW_HOME=~/airflow`
3. Inicialize o banco de dados do Airflow: `airflow db init`
4. Crie um usuário admin: `airflow users create -u admin -p admin -f Admin -l User -r Admin -e admin@example.com`
5. Inicie o webserver e o scheduler:
   ```bash
   airflow webserver --port 8080 -D
   airflow scheduler -D
   ```
6. Acesse `http://localhost:8080`, ative a DAG `etl_apoio_escolar_periferico` e clique em *Trigger DAG*.

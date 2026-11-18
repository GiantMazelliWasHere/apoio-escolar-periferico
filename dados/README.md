# Pipeline de Dados: Apoio Escolar Periférico

**Disciplina:** Big Data Architecture & Data Integration (Prof.ª Ana Machado). Global Solution 2026.2, CitizenTech, Engenharia de Software 4º ano.

**Entrega no portal:** o link deste repositório e o PDF [`Entrega_BigData_ApoioEscolar_com_evidencias.pdf`](Entrega_BigData_ApoioEscolar_com_evidencias.pdf), que traz a ficha técnica, a arquitetura, o dicionário de dados, o diagrama (Anexo A) e os prints da execução (Anexo B). O [`Entrega_BigData_ApoioEscolar.pdf`](Entrega_BigData_ApoioEscolar.pdf) é o original do Jó, guardado sem alterações. O PDF de entrega é gerado a partir dele por [`evidencias/montar_pdf.py`](evidencias/montar_pdf.py).

---

## 1. Ficha Técnica do MVP

* **Nome do produto:** Apoio Escolar Periférico
* **Cidadão e território:** Estudantes de escolas públicas em comunidades periféricas.
* **Problema, em uma frase:** A falta de suporte educacional extraclasse e de infraestrutura digital agrava a defasagem escolar e a exclusão tecnológica em áreas vulneráveis.
* **Proposta de valor:** Plataforma que conecta estudantes de baixa renda a vagas de monitoria voluntária e materiais digitais, usando dados para priorizar o atendimento.
* **Arquitetura (componentes):** Airflow (ETL INEP/IBGE) → API do núcleo do MVP (FastAPI no Azure App Service, banco SQLite) → painel `/impacto`. Ao lado: OCR de comprovantes (Visão), Tutor IA (GenAI) e RPA UiPath, que credencia voluntários no portal SICREV e envia os boletins.
* **Fontes de dados:** Microdados do INEP (Censo Escolar e IDEB) e IBGE (malha territorial). No protótipo, a extração é **simulada**: escolas fictícias com as mesmas regras de negócio, porque o objetivo é provar o pipeline de ponta a ponta sem nenhum dado real de escola ou aluno.
* **Modelos de IA utilizados:** OCR (leitura de comprovantes de endereço) e LLM (Tutor IA).
* **URL do MVP e repositório:** https://app-apoioescolar-mvp-6e7462.azurewebsites.net · https://github.com/GiantMazelliWasHere/apoio-escolar-periferico
* **Indicadores de impacto:** Número de alunos engajados; horas de monitoria; acessos vindos de escolas em território prioritário.
* **ODS conectados:** ODS 4 (Educação de Qualidade) e ODS 10 (Redução das Desigualdades).

---

## 2. Arquitetura do Pipeline (ETL)

DAG `etl_apoio_escolar_periferico` ([`dags/dag_etl_apoio_escolar.py`](dags/dag_etl_apoio_escolar.py)), feita com a TaskFlow API do Airflow e agendada como `@daily`. Tem três tarefas, e a lógica de cada uma fica em [`dags/etl_apoio_escolar.py`](dags/etl_apoio_escolar.py), para rodar e ser testada também sem o Airflow:

1. **Extract (`extract_inep_ibge`):** lê os dados de infraestrutura e IDEB das escolas (simulados) e grava a camada Raw (`raw_inep_ibge.csv`).
2. **Transform (`transform_data`):** mantém só as escolas de região periférica, imputa o IDEB faltante pela média do recorte e calcula o *Índice de Prioridade Educacional*. Grava a camada Trusted (`trusted_escolas_prioritarias.csv`).
3. **Load (`load_to_azure`):** envia a Trusted ao núcleo do MVP por `PUT /api/v1/escolas/prioridade` (com `X-API-Key`). O núcleo grava o índice na tabela `escolas`, e o painel `/impacto` passa a mostrar a origem "Pipeline INEP/IBGE".

Os CSVs ficam em `CITIZENTECH_DATA_PATH` (padrão: `<temp>/citizentech_data`). O diagrama está em [`evidencias/00_diagrama_pipeline.png`](evidencias/00_diagrama_pipeline.png), e o contrato da API em [docs/INTEGRACAO.md](../docs/INTEGRACAO.md).

---

## 3. Dicionário de Dados

Todos os dados são sintéticos. As escolas são fictícias, com código INEP de prefixo `99` para nunca coincidir com uma escola real, e não há nenhum dado pessoal.

### Camada Raw: `raw_inep_ibge.csv`

| Coluna | Tipo | Chave | Descrição |
| :--- | :--- | :--- | :--- |
| `cod_municipio` | INT | - | Código IBGE do município (7 dígitos). |
| `cod_escola` | INT | PK | Código INEP da escola (fictício, prefixo 99). |
| `nome_escola` | VARCHAR | - | Nome da escola (fictício). |
| `regiao_periferica` | INT | - | 1 = região periférica, 0 = não. Define o recorte da Trusted. |
| `ideb_anos_finais` | FLOAT | - | IDEB dos anos finais do fundamental. Pode vir vazio (dado faltante simulado). |
| `qtd_alunos` | INT | - | Matrículas da escola. Não segue para a Trusted. |
| `lab_informatica` | INT | - | 1 = tem laboratório de informática, 0 = não. |
| `acesso_internet` | INT | - | 1 = tem internet, 0 = não. |

### Camada Trusted: `trusted_escolas_prioritarias.csv`

| Coluna | Tipo | Chave | Descrição |
| :--- | :--- | :--- | :--- |
| `cod_municipio` | INT | - | Copiado da Raw. |
| `cod_escola` | INT | PK | Copiado da Raw. |
| `nome_escola` | VARCHAR | - | Copiado da Raw. |
| `ideb_anos_finais` | FLOAT | - | IDEB faltante imputado pela média das escolas do recorte periférico (e não por zero, que tornaria a escola sem nota a mais prioritária). |
| `indice_prioridade` | FLOAT | - | De 0 a 14: `(10 - IDEB) + 2 sem laboratório + 2 sem internet`. Quanto maior, mais prioritária. A tabela sai ordenada por ele. |

### MVP: tabela `escolas` (colunas gravadas pela carga)

| Coluna | Tipo | Chave | Descrição |
| :--- | :--- | :--- | :--- |
| `codigo_inep` | VARCHAR(20) | busca | Recebe `cod_escola`. É por ele que o núcleo encontra a escola. Códigos que não existem no núcleo são ignorados. |
| `territorio_prioritario` | BOOLEAN | - | `true` para toda escola da Trusted. |
| `indice_prioridade` | FLOAT | - | `indice_prioridade` da Trusted dividido por 14 (de 0 a 1). |
| `fonte_prioridade` | VARCHAR(40) | - | Passa de `sintetico` (seed) para `pipeline` quando a carga grava a escola. |

**Modelo-alvo para os dados reais:** a dimensão `dim_municipios_ibge` (`cod_municipio_ibge`, `nome_municipio`, `uf`) e o fato `fact_escolas_vulnerabilidade`, ligados pelo código do município (desenho do PDF original). Ainda não foi implementado no protótipo.

---

## 4. Como executar

O núcleo do MVP precisa estar rodando para a carga ser real (veja o [README principal](../README.md)). A chave de integração é a mesma `INTEGRATION_API_KEY` do `mvp/.env`.

### Opção A: Airflow no Docker (o caminho usado nas evidências)

```bash
cd dados
echo INTEGRATION_API_KEY=<a mesma do mvp/.env> > .env   # fora do git
docker compose up -d
```

Abra http://localhost:8080. Não há login: o acesso anônimo entra como admin, o que serve **só para uso local**. A DAG já aparece ativa. Para rodar na hora, clique em ▶ ou use `docker compose exec airflow airflow dags trigger etl_apoio_escolar_periferico`. Para desligar, `docker compose down`. A imagem usada é `apache/airflow:2.10.5-python3.12`, e por padrão a carga vai para o núcleo em `http://host.docker.internal:8000`. Para mandar para outra instância, defina `MVP_API_URL`.

### Opção B: sem Airflow (Windows ou teste rápido)

Roda as mesmas funções da DAG, na mesma ordem:

```bash
cd dados
python -m venv .venv
.venv/Scripts/pip install pandas pytest      # no Linux: .venv/bin/pip
set MVP_API_URL=http://localhost:8000        # sem esta variável, a carga é só simulada
set INTEGRATION_API_KEY=<a mesma do mvp/.env>
.venv/Scripts/python rodar_local.py
```

### Opção C: Airflow instalado direto (Linux ou WSL)

```bash
pip install "apache-airflow==2.10.5" pandas \
  --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.5/constraints-3.12.txt"
export AIRFLOW_HOME=~/airflow
export AIRFLOW__CORE__DAGS_FOLDER="$(pwd)/dags"
export MVP_API_URL=http://localhost:8000 INTEGRATION_API_KEY=<a mesma do mvp/.env>
airflow standalone   # cria o banco e o usuário admin (a senha aparece no terminal) e sobe a UI em :8080
```

### Testes

```bash
cd dados
.venv/Scripts/python -m pytest -q
```

São 6 testes. Eles cobrem o recorte periférico, a imputação do IDEB, o contrato do payload e a carga HTTP com a chave.

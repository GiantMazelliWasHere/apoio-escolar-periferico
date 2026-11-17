# Integração entre as disciplinas

Um único produto atravessa as sete disciplinas (slide 18 do PDF oficial). O **núcleo do MVP** fica em [`mvp/`](../mvp/) e é o ponto onde tudo se encaixa. Cada disciplina entrega o seu componente na própria pasta e conversa com o núcleo pelos **contratos abaixo**: API, banco ou arquivo, nunca prints colados lado a lado (slide 21).

## Estrutura do repositório

| Pasta | Disciplina | Responsável | Status |
|---|---|---|---|
| `mvp/` | Núcleo (front + API + banco) | Equipe | ✅ fluxo central funcionando localmente, com testes |
| `dados/` | Big Data Architecture & Data Integration | Jó Sales | ✅ entrega copiada e integrada ao núcleo: a DAG grava a prioridade das escolas pela API e o painel `/impacto` mostra o resultado |
| `ia/` | Generative AI for Engineering | Edson Leonardo | ✅ entrega copiada e integrada ao núcleo (tela "Ajuda"), testada com a chave real do OpenRouter |
| `visao/` | Applied Computer Vision | Edson Leonardo | ✅ entrega copiada ([EdLeo0708/Applied-Computer-Vision](https://github.com/EdLeo0708/Applied-Computer-Vision)) e integrada ao cadastro do núcleo; testada com EasyOCR real |
| `rpa/` | Robotic Process Automation | Miguel Garcez | 🟡 relatório copiado e contrato do robô implementado no núcleo (`POST /api/v1/integracao/voluntarios`); ⬜ copiar o projeto UiPath para `rpa/` |
| `.github/workflows/` + `infra/` | Secure DevOps Tools & Cloud Computing | Miguel Garcez | ✅ no ar em https://app-apoioescolar-mvp-6e7462.azurewebsites.net, publicado pelo pipeline (qualidade, gitleaks, deploy OIDC com smoke test); detalhes em [DEVOPS.md](DEVOPS.md) |
| `maker/` | Project-Based Maker Lab | Vinicius Souza | ✅ entrega copiada (suporte de tablet: CAD, 3MF e DXF) e integrada ao núcleo pelo QR code: `/qr` marca a origem, o cadastro grava e o `/impacto` conta |
| `docs/business/` | BI & Startup Development | Eduardo Mazelli | ✅ |

## Contratos já disponíveis no núcleo

Documentação interativa da API: `/api/docs` (Swagger, gerado pelo FastAPI).

Integrações máquina-a-máquina usam o cabeçalho **`X-API-Key`**, com o valor da variável de ambiente `INTEGRATION_API_KEY`. A chave nunca vai para o código (slide 21).

### Dados → núcleo: priorização territorial
`PUT /api/v1/escolas/prioridade` (exige `X-API-Key`)

```json
[
  {"codigo_inep": "35000000", "territorio_prioritario": true, "indice_prioridade": 0.87},
  {"escola_id": 2, "territorio_prioritario": false, "indice_prioridade": 0.31}
]
```
Resposta: `{"atualizadas": 2}`. A escola passa a ter `fonte_prioridade = "pipeline"`. Código INEP desconhecido é ignorado (não conta em `atualizadas`).
Para conferir: `GET /api/v1/escolas` ou a tabela "Prioridade territorial das escolas" em `/impacto`.

- **Origem do código:** a pasta [`dados/`](../dados/) traz a entrega da disciplina (zip e PDF do Jó Sales). A DAG [`dag_etl_apoio_escolar.py`](../dados/dags/dag_etl_apoio_escolar.py) mantém as três tarefas da entrega (`extract_inep_ibge` → `transform_data` → `load_to_azure`), com CSVs Raw e Trusted entre elas. A lógica de cada etapa foi para [`etl_apoio_escolar.py`](../dados/dags/etl_apoio_escolar.py), para rodar e testar também sem o Airflow.
- **Regras da entrega mantidas:** só escolas em região periférica entram na camada Trusted; Índice de Prioridade Educacional = (10 − IDEB anos finais) + 2 sem laboratório de informática + 2 sem internet.
- **Mudanças da integração:**
  - as escolas simuladas são as 6 do seed do MVP, com **código INEP fictício** `99000101` a `99000106` (prefixo 99 é uma UF inexistente, então nunca coincide com escola real). O seed grava esses códigos e completa bancos antigos;
  - IDEB faltante é imputado pela **média das escolas do recorte** (a entrega usava zero, o que tornava a escola sem nota a mais prioritária de todas);
  - a carga chama de verdade este endpoint. O índice vai **normalizado de 0 a 1** (índice ÷ 14, o máximo possível) e as escolas do recorte vão com `territorio_prioritario = true`; as de fora do recorte mantêm o valor que já tinham;
  - `schedule` no lugar de `schedule_interval` e Airflow fixado em `<3` no `requirements.txt` (os comandos do README da entrega são do Airflow 2); a pasta temporária usa o diretório temporário do sistema (funciona também no Windows).
- **Configuração da carga:** `MVP_API_URL` (ex.: `http://localhost:8000` ou a URL do App Service) e `INTEGRATION_API_KEY` (a mesma do núcleo), como variáveis de ambiente do Airflow. Sem `MVP_API_URL`, a carga é só simulada, como na entrega original; com a URL e sem a chave, a tarefa falha.
- **Rodar sem Airflow** (Windows, ou para gravar a demo):
  ```bash
  cd dados
  python -m venv .venv
  .venv/Scripts/python -m pip install "pandas>=2.0.0" pytest
  .venv/Scripts/python -m pytest -q
  set MVP_API_URL=http://localhost:8000
  set INTEGRATION_API_KEY=<mesma chave do mvp/.env>
  .venv/Scripts/python rodar_local.py
  ```
  Com o núcleo rodando, as 4 escolas periféricas passam a `fonte_prioridade = "pipeline"` (testado em 15/11/2026: `{"atualizadas": 4}`).
- **Rodar no Airflow (Docker):** com o núcleo rodando na porta 8000 e a chave em `dados/.env` (`INTEGRATION_API_KEY=...`, fora do git):
  ```bash
  cd dados
  docker compose up -d
  ```
  Abrir http://localhost:8080 (sem login: o acesso anônimo é admin, **só para uso local**, via [`webserver_config.py`](../dados/airflow/webserver_config.py)). A DAG aparece ativa; para rodar na hora: botão ▶ ou `docker compose exec airflow airflow dags trigger etl_apoio_escolar_periferico`. Testado em 15/11/2026 com Airflow 2.10.5: as 3 tarefas em `success` e `{'atualizadas': 4}` no núcleo. Para desligar: `docker compose down`. Sem Docker, seguir o README de `dados/` (Linux ou WSL).
- **Evidências e PDF da disciplina:** os prints estão em [`dados/evidencias/`](../dados/evidencias/) e o diagrama em [`diagrama_pipeline.html`](../dados/evidencias/diagrama_pipeline.html). [`montar_pdf.py`](../dados/evidencias/montar_pdf.py) gera [`Entrega_BigData_ApoioEscolar_com_evidencias.pdf`](../dados/Entrega_BigData_ApoioEscolar_com_evidencias.pdf): o PDF do Jó com as duas caixas apontando para os anexos A (diagrama) e B (prints do Airflow e do `/impacto`). O PDF original fica intacto ao lado.
- **README e PDF de `dados/`:** são a documentação da entrega como foi feita para a disciplina. O dicionário de dados do PDF (`dim_municipios_ibge`, `fact_escolas_vulnerabilidade`, nota de 1 a 10) é o modelo-alvo; o que roda hoje é a tabela da camada Trusted descrita no README (`cod_municipio`, `cod_escola`, `nome_escola`, `ideb_anos_finais`, `indice_prioridade`).

### Núcleo → RPA: presenças para o relatório de impacto
`GET /api/v1/agendamentos.csv` (exige `X-API-Key`)

Colunas: `agendamento_id, estudante_pseudo, escola, territorio_prioritario, materia, inicio, duracao_min, status, voluntario_pseudo`. Só aparecem estudantes autorizados pelo responsável (pendentes não agendam).
Sem nomes nem e-mails: os identificadores são pseudônimos (hash). O robô UiPath pode baixar o CSV (HTTP Request), consolidar presenças, montar o relatório do patrocinador e enviá-lo por e-mail.

`GET /api/v1/impacto` (público, agregado e anônimo): os mesmos indicadores do painel `/impacto`, em JSON Contagens de pessoas entre 1 e 4 vêm como `null` ("menos de 5", LGPD) e matérias com menos de 5 agendamentos ficam fora de `agendamentos_por_materia` (`materias_ocultas` diz quantas); quem consome a API deve tratar `null`.

`POST /api/v1/manutencao/expurgo` (exige `X-API-Key`): apaga na hora os cadastros de menores sem autorização do responsável há mais de 30 dias. O app já faz isso sozinho na subida e a cada hora; o endpoint serve para automação ou demonstração. Resposta: `{"apagados": n}`.

### Front → núcleo → IA Generativa: assistente AI Bits
`POST /api/v1/assistente` (chamado pela tela [`/ajuda`](../mvp/app/templates/ajuda.html); exige o cabeçalho `X-CSRF-Token` da sessão)

```json
{"pergunta": "Como agendo uma monitoria?"}
```
Resposta:
```json
{
  "resposta": "Oi! É bem rápido marcar uma monitoria.",
  "passos": ["Entre com a sua conta de estudante.", "Abra \"Monitorias\" e escolha a matéria.", "Toque em \"Agendar\"."],
  "categoria": "Agendamento",
  "acao": {"rotulo": "Ver monitorias", "url": "/monitorias"},
  "encaminhar_humano": false,
  "fonte": "ia"
}
```
- **Origem do código:** a pasta [`ia/`](../ia/) é a cópia fiel do repositório da disciplina (`EdLeo0708/GAE`, commit `5fcb6c8`). O núcleo usa [`mvp/app/assistente.py`](../mvp/app/assistente.py), que mantém o mesmo pipeline (persona, contexto, few-shot, delimitadores, JSON validado com Pydantic, retentativa com Tenacity) com a base de conhecimento reescrita para o nome e as telas reais do MVP. O deploy publica só `mvp/`, por isso o código integrado mora lá.
- **Configuração:** `OPENROUTER_API_KEY` (obrigatória para a IA responder) e `GENAI_MODEL_NAME` (opcional; padrão `google/gemini-2.5-flash`). Local: copiar [`mvp/.env.example`](../mvp/.env.example) para `mvp/.env`. Azure: Configurações de aplicativo.
- **Falhas:** sem chave, com o modelo fora do ar ou com JSON fora do esquema, a resposta vem com `"fonte": "fallback"` (mensagem amigável + link para agendar com um monitor) e o erro fica só no log. A tela sempre mostra as perguntas frequentes, que não dependem da IA.
- **Limites:** pergunta de até 800 caracteres (`422` acima disso); 8 perguntas por minuto por cliente e 300 por hora no total (`429`). O limite é em memória, por processo.
- **Privacidade:** só o texto da pergunta vai ao provedor; nada do cadastro é enviado e a conversa não é gravada. `acao` só aceita destinos de uma lista fixa do servidor.
- **README de `ia/`:** é a documentação da entrega da disciplina, mantida pelo autor no repositório dele (`EdLeo0708/GAE`). Ele descreve a entrega como foi avaliada pelo professor de IA Generativa, por isso pode usar outro nome de produto e citar telas que o MVP integrado não tem. A referência do produto integrado é este repositório.

### Front → núcleo → Visão Computacional: endereço pela foto da conta
`POST /api/v1/visao/endereco` (chamado pela tela [`/cadastro/estudante`](../mvp/app/templates/cadastro_estudante.html); `multipart/form-data` com o campo `arquivo`; exige o cabeçalho `X-CSRF-Token` da sessão)

Resposta:
```json
{
  "logradouro": "Avenida Rua dos Palmares",
  "numero": "141",
  "bairro": "Grajau",
  "cep": "07657-532",
  "uf": "SP",
  "empresa": "SABESP",
  "empresa_nome": "Sabesp (água)",
  "confianca": 1.0,
  "fonte": "ocr"
}
```
- **Origem do código:** a pasta [`visao/`](../visao/) é a cópia fiel do repositório da disciplina (`EdLeo0708/Applied-Computer-Vision`, commit `9cdac0e`). O núcleo usa [`mvp/app/visao.py`](../mvp/app/visao.py), com o mesmo pipeline: decodificação em memória (foto ou 1ª página do PDF), cantos do papel por Canny + aproximação poligonal, `cv2.warpPerspective`, recorte do cabeçalho e da região do endereço, EasyOCR e regras que separam o endereço do cliente do endereço da sede (CEPs e "Av. das Nações Unidas" ignorados). Mudanças em relação à entrega: o papel corrigido é ampliado para 2400 px de largura antes do OCR, o bairro é lido também pela linha abaixo do logradouro (formato das contas Sabesp e Claro) e o "Nº" mal lido pelo OCR ("NE692", "NI6O3") é tratado.
- **Acerto medido com EasyOCR real** nas 15 contas sintéticas de `visao/dataset_sintetico` (5 por empresa): imagem plana: CEP 15/15, número 15/15, bairro 10/15; foto simulada (papel inclinado sobre fundo escuro): CEP 10/15, bairro 9/15. Os erros que sobram são letras trocadas pelo OCR, por isso a tela sempre pede para o estudante **conferir e corrigir**. Cerca de 11 s por conta num PC comum (CPU).
- **O que é gravado:** nada nesta chamada. A foto fica só na memória do processo. No envio do cadastro, o estudante confirma e o núcleo grava **só bairro e CEP** (coluna `usuarios.cep`, adicionada automaticamente em bancos antigos).
- **Instalação:** OpenCV, NumPy e pypdfium2 estão no `requirements.txt`. O OCR (EasyOCR + PyTorch CPU, ~1 GB) fica em [`mvp/requirements-visao.txt`](../mvp/requirements-visao.txt). Sem ele, `fonte` vem `"indisponivel"`, o botão da foto não aparece e o cadastro pede bairro e CEP digitados. O CI instala só o `requirements-dev.txt` e testa a Visão com OCR simulado.
- **Falhas e limites:** arquivo de até 8 MB (`413`), só JPG, PNG, WebP ou PDF (`415`), arquivo ilegível (`422`), 6 leituras por minuto por cliente e 120 por hora no total (`429`). Se o OCR quebrar, a resposta vem com `"fonte": "erro"` e campos vazios; o erro fica só no log.
- **README de `visao/`:** é a documentação da entrega como foi avaliada pelo professor de Visão Computacional (usa outro nome de produto e um hub web próprio em Flask). A referência do produto integrado é este repositório.

### Peça física (Maker Lab) → núcleo: QR code do suporte de tablet
`GET /qr` (público; é a URL gravada no QR da etiqueta)

Marca a sessão com `origem = "peca_maker"` (só se a pessoa não estiver logada) e redireciona para `/`, que mostra o aviso "Você chegou pelo QR code do suporte de estudo". Se a pessoa se cadastrar (estudante ou voluntário) na mesma visita, a conta grava `usuarios.origem = "peca_maker"` (coluna adicionada automaticamente em bancos antigos). O indicador `cadastros_via_peca_maker` aparece em `/impacto` e em `GET /api/v1/impacto`.

- **Origem da peça:** a pasta [`maker/`](../maker/) traz a entrega da disciplina na rev. C (desenho 3DP-2026-004): desenho técnico em PDF e DXF, STEP, 3MF/STL para impressão 3D e renders. É uma peça única de chapa dobrada de 2 mm (110 × 125 × 104 mm), com painel de leitura a 65°, perna traseira a 80° e encaixe de 15 mm na base. A etiqueta QR de 30 mm vai na face de trás da perna traseira. Detalhes em [`maker/README.md`](../maker/README.md).
- **Etiqueta:** `GET /maker` mostra a peça e o QR; `GET /maker/qrcode.svg?tamanho_mm=30` baixa o QR vetorial no tamanho físico (15 a 200 mm; padrão 30 mm), para imprimir em papel adesivo. O QR é gerado pelo OpenCV, que o núcleo já instala para a Visão (sem dependência nova).
- **Configuração:** `PUBLIC_URL` (ex.: `https://<app>.azurewebsites.net`). O QR aponta para `PUBLIC_URL` + `/qr`. Sem ela, usa o endereço da requisição, o que só serve para teste local: gerar a etiqueta definitiva depois do deploy.
- **Privacidade:** só o rótulo do canal fica gravado, sem localização nem dados do aparelho (descrito em `/privacidade`). Valores fora da lista do servidor são ignorados.
- **Testes:** [`mvp/tests/test_maker.py`](../mvp/tests/test_maker.py) gera o QR, lê de volta com o detector do OpenCV e percorre QR → cadastro → indicador.

### RPA → núcleo: voluntários credenciados no SICREV
`POST /api/v1/integracao/voluntarios` (exige `X-API-Key`)

O robô UiPath ([relatório](../rpa/Relatorio_RPA_ApoioEscolar.pdf), seção 7) faz a triagem das inscrições, credencia cada voluntário no portal legado da Diretoria (SICREV, sem API, por automação de tela) e devolve ao núcleo, pelo workflow `AtualizarBaseMVP.xaml`, quem ficou `CREDENCIADO` ou `JA_CREDENCIADO`:

```json
[
  {"apelido": "vol_I001", "email": "pessoa@exemplo.com.br", "bairro": "Capão Redondo", "aceita_boletim": true}
]
```
Resposta **201**:
```json
{"criados": ["vol_I001"], "rejeitados": [], "motivos": {}}
```
- **Estado no núcleo:** cada voluntário entra como pendente de aprovação (`aprovado = false`, `origem = "rpa_sicrev"`) e aparece em `/coordenacao/voluntarios` com a marca "Já credenciado no SICREV pelo robô"; a coordenação aprova ou recusa (e apaga).
- **Idempotência:** apelido (sem diferenciar maiúsculas) ou e-mail já existente volta em `rejeitados`, com o motivo em `motivos`; reexecutar o robô não duplica nada.
- **Item ruim não derruba o lote:** e-mail inválido, apelido fora do padrão (3 a 30 caracteres: letras, números, `_ . -`) ou repetido no mesmo lote vai para `rejeitados`. Lote máximo: 500 itens (acima disso, `413`).
- **Minimização (LGPD):** só os quatro campos acima. Campo extra (CPF, nome, telefone) faz o item ser rejeitado. `aceita_boletim` é gravado como opt-in do boletim.
- **Conta sem senha:** o voluntário vindo do robô ainda não consegue entrar (não há senha utilizável); a conta serve à coordenação. Falta o fluxo para ele definir a senha (ver pendências).
- **No robô:** `MvpApiUrl` no `Config.xlsx` = URL do App Service + `/api/v1/integracao/voluntarios`; a chave vem da variável de ambiente `APOIO_MVP_API_KEY`, com o valor do segredo `integration-api-key` do Key Vault.
- **Testes:** [`mvp/tests/test_rpa.py`](../mvp/tests/test_rpa.py).

O export `GET /api/v1/agendamentos.csv` (abaixo) continua disponível para relatórios do robô.

## Contratos a criar quando as entregas chegarem

| Componente | Ponto de encaixe sugerido | O que o núcleo precisa |
|---|---|---|
| **RPA** | ✅ `POST /api/v1/integracao/voluntarios` (acima) | Projeto UiPath em `rpa/`; fluxo para o voluntário vindo do robô definir a senha |

## Executar o núcleo localmente

```bash
cd mvp
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
.venv/Scripts/python -m pytest -q
.venv/Scripts/python -m uvicorn app.main:app --reload
```
Abrir http://localhost:8000. No Linux/macOS, use `.venv/bin/python`.

## Publicar no Azure (disciplina de DevOps)

Tudo automatizado; detalhes em [DEVOPS.md](DEVOPS.md).

1. Rodar [`infra/provisionar.sh`](../infra/provisionar.sh) (Azure Cloud Shell): cria App Service, Key Vault com os segredos, Application Insights, alertas, orçamento e a identidade OIDC do GitHub, e grava as variáveis do pipeline no repositório.
2. Push na `main`: o workflow [`ci-cd.yml`](../.github/workflows/ci-cd.yml) testa, varre segredos, publica e confere `/health` com a versão do commit.
3. Depois do 1º deploy: gerar a etiqueta definitiva do QR em `https://<app>.azurewebsites.net/maker` e apontar o Airflow (`MVP_API_URL`) e o robô RPA para a URL pública, com a `INTEGRATION_API_KEY` lida do Key Vault (`az keyvault secret show --vault-name <kv> -n integration-api-key --query value -o tsv`).

Configurações do App Service (o script já define): `APP_ENV=production`, `SECRET_KEY`, `INTEGRATION_API_KEY`, `FERNET_KEY` e `OPENROUTER_API_KEY` como referências ao Key Vault, `DATABASE_URL=sqlite:////home/data/apoio-mvp.db`, `PUBLIC_URL`, `SCM_DO_BUILD_DURING_DEPLOYMENT=true`, `APPLICATIONINSIGHTS_CONNECTION_STRING` e comando de inicialização `sh startup.sh`. A leitura da foto da conta (OCR) continua desligada no B1: exige publicar com o `requirements-visao.txt` e um plano com pelo menos 3,5 GB de RAM.

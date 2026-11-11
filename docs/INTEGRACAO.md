# Integração entre as disciplinas

Um único produto atravessa as sete disciplinas (slide 18 do PDF oficial). O **núcleo do MVP** fica em [`mvp/`](../mvp/) e é o ponto onde tudo se encaixa. Cada disciplina entrega o seu componente na própria pasta e conversa com o núcleo pelos **contratos abaixo**: API, banco ou arquivo, nunca prints colados lado a lado (slide 21).

## Estrutura do repositório

| Pasta | Disciplina | Responsável | Status |
|---|---|---|---|
| `mvp/` | Núcleo (front + API + banco) | Equipe | ✅ fluxo central funcionando localmente, com testes |
| `dados/` | Big Data Architecture & Data Integration | Jó Sales | ⬜ aguardando entrega |
| `ia/` | Generative AI for Engineering | Edson Leonardo | ✅ entrega copiada e integrada ao núcleo (tela "Ajuda"); 🟡 falta testar com a chave real do OpenRouter |
| `visao/` | Applied Computer Vision | Edson Leonardo | ⬜ aguardando entrega |
| `rpa/` | Robotic Process Automation | Miguel Garcez | ⬜ aguardando entrega |
| `.github/workflows/` + Azure | Secure DevOps Tools & Cloud Computing | Miguel Garcez | 🟡 CI pronto; deploy em modelo |
| `maker/` | Project-Based Maker Lab | Vinicius Souza | ⬜ aguardando entrega |
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
Resposta: `{"atualizadas": 2}`. A escola passa a ter `fonte_prioridade = "pipeline"`.
**Sugestão para a DAG do Airflow:** ingerir IDEB/Censo Escolar (INEP) + IBGE → calcular o índice → chamar este endpoint como última tarefa.
Para conferir: `GET /api/v1/escolas`.

> Hoje as escolas do seed são **fictícias**. Quando o pipeline chegar, vale trocá-las por escolas reais do território (nome + código INEP), que são dados públicos.

### Núcleo → RPA: presenças para o relatório de impacto
`GET /api/v1/agendamentos.csv` (exige `X-API-Key`)

Colunas: `agendamento_id, estudante_pseudo, escola, territorio_prioritario, materia, inicio, duracao_min, status, voluntario_pseudo`.
Sem nomes nem e-mails: os identificadores são pseudônimos (hash). O robô UiPath pode baixar o CSV (HTTP Request), consolidar presenças, montar o relatório do patrocinador e enviá-lo por e-mail.

`GET /api/v1/impacto` (público, agregado e anônimo): os mesmos indicadores do painel `/impacto`, em JSON.

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
- **Divergência a alinhar com o autor:** o README de `ia/` ainda chama o produto de "EduConecta Periferia" e descreve telas (envio de comprovante, trilhas) que o MVP não tem.

## Contratos a criar quando as entregas chegarem

| Componente | Ponto de encaixe sugerido | O que o núcleo precisa |
|---|---|---|
| **Visão** (extração de endereço) | Tela de cadastro: botão "enviar foto do comprovante" → serviço de Visão → campos preenchidos para o estudante **confirmar** | Endpoint do serviço (ex.: `POST /extrair-endereco` recebendo a imagem e devolvendo `{logradouro, numero, bairro, cep, cidade, confianca}`). Hoje o cadastro pede só o bairro, de forma opcional |
| **Maker Lab** | QR code na peça fabricada | Só a URL pública do MVP |

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

1. Criar um App Service Linux com Python 3.12.
2. Em **Configuração > Configurações de aplicativo**:
   - `APP_ENV=production`
   - `SECRET_KEY=<valor longo e aleatório>`
   - `INTEGRATION_API_KEY=<outro valor aleatório>`
   - `OPENROUTER_API_KEY=<chave do OpenRouter>` (assistente da tela "Ajuda"; sem ela, só as perguntas frequentes)
   - `DATABASE_URL=sqlite:////home/data/apoio.db` (o `/home` é persistente no App Service; para produção real, usar PostgreSQL)
   - `SCM_DO_BUILD_DURING_DEPLOYMENT=true` (instala o `requirements.txt` no deploy)
3. **Comando de inicialização:** `sh startup.sh`
4. No GitHub: secret `AZURE_WEBAPP_PUBLISH_PROFILE` e variável `AZURE_WEBAPP_NAME`. O workflow [`deploy-azure.yml`](../.github/workflows/deploy-azure.yml) publica depois que o CI passa.
5. Application Insights + alerta sobre `/health` (exigência de monitoramento do slide 40).

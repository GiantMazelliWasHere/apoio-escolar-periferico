# AI Bits — Assistente Inteligente do EduConecta Periferia

## Global Solution 2026.2 — Generative AI for Engineering (4ESPR)

**Professor:** Reinaldo Augusto de Oliveira Ramos
**Prazo de Entrega:** 19/11 às 23h59

---

## Equipe: **Bits N’ Bytes** - 4ESPR FIAP

- **Jó Sales** — RM 552679
- **Miguel Garcez de Carvalho** — RM 553768
- **Vinicius Souza e Silva** — RM 552781
- **Edson Leonardo** — RM 553737
- **Eduardo Mazelli** — RM 553236

**ODS Vinculados:** **ODS 4** (Educação de Qualidade) e **ODS 10** (Redução das Desigualdades)

---

## 1. Problema Escolhido no Contexto CitizenTech

O projeto **EduConecta Periferia** conecta estudantes de comunidades periféricas da rede pública a voluntários e trilhas de reforço escolar gratuitas.

Contudo, muitos jovens e responsáveis dessas comunidades possuem **baixo letramento digital** e enfrentam barreiras severas ao utilizar o sistema pela primeira vez:

- **Dúvidas no Cadastro:** Insegurança sobre como enviar a foto da conta de luz ou água (**Enel, Sabesp ou Claro**) para validação de residência e elegibilidade social;
- **Erros Frustrantes de Upload:** Dificuldade em entender mensagens de erro técnicas do módulo de Visão Computacional quando a imagem está escura, com reflexo ou cortada;
- **Navegação Desorientada:** Incerteza sobre onde encontrar aulas ao vivo, como agendar monitorias ou onde acessar os materiais gratuitos da Khan Academy.

**Nossa Solução com IA Generativa (AI Bits):**A **AI Bits** é a assistente de inteligência artificial oficial integrada via API (OpenRouter) e treinada na base de conhecimento do software, que:

- Atende o munícipe em linguagem acolhedora, inclusiva e empática;
- Diagnostica a causa de erros de upload de faturas e orienta como tirar fotos melhores;
- Devolve respostas estritamente estruturadas em **JSON padronizado**, acionando comandos diretos na interface do usuário (ex: abrir câmera, redirecionar para tela de agendamento).

---

## 2. Arquitetura da Solução

```
[ Usuário no App Mobile / Web ]
              │
              ▼
    [ Endpoint FastAPI ]
              │  (Pergunta do Cidadão)
              ▼
[ Pipeline de Engenharia de Prompts ]
  ├── System Prompt: Persona 'AI Bits' (Bits N’ Bytes)
  ├── Injeção de Contexto do Software (Módulo CV, Enel/Sabesp/Claro, Aulas)
  ├── Exemplos Calibrados de Atendimento (Few-Shot)
  └── Delimitadores XML (<pergunta_usuario>)
              │
              ▼
[ Gateway OpenRouter API ] (Modelo: google/gemini-2.5-flash)
  ├── Temperature: 0.1 (Determinismo para suporte técnico confiável)
  ├── Response Format: JSON Object
  └── Tenacity Retry Engine (3 tentativas com Backoff Exponencial)
              │
              ▼
[ Validação Estrita com Pydantic V2 (EduConectaHelperOutput) ]
              │
              ▼
[ Resposta Humanizada + Ações Guiadas de UI ]
```

---

## 3. Escolha e Configuração do Modelo

- **Provedor e Modelo:** `google/gemini-2.5-flash` via **OpenRouter API**.
- **Nome do Assistente / Persona:** **AI Bits** (equipe Bits N’ Bytes).
- **Justificativas Técnicas:**
  - *Latência Extrema:* Resposta em menos de 1 segundo (P95 de 850ms), fundamental para experiência fluida em conexões 3G/4G periféricas;
  - *Aderência a JSON Schema:* Precisão absoluta na geração de campos tipados sem quebra de sintaxe;
  - *Custo-benefício Sustentável:* Modelo ultra-leve e de baixíssimo custo por token, tornando viável a gratuidade contínua para projetos sociais.
- **Configuração de Hiperparâmetros:**
  - `temperature: 0.1` — Evita desvios e alucinações sobre funcionalidades inexistentes do app;
  - `max_tokens: 800` — Suficiente para passos claros sem prolixidade;
  - `top_p: 0.9` — Amostragem focada nas respostas mais assertivas.

---

## 4. Engenharia de Prompts e Exemplos de Saída

### 4.1. Injeção de Contexto & System Prompt

O assistente recebe a documentação completa das telas do software, das concessionárias aceitas (**Enel, Sabesp e Claro**) e diretrizes estritas para orientar o munícipe com clareza.

### 4.2. Exemplo Real de Entrada e Saída Estruturada

**Entrada do Usuário:**

> *"Enviei a foto da minha conta da Enel mas o sistema disse que não conseguiu ler o endereço. O que eu faço?"*

**Saída Estruturada (JSON Validado pelo Pydantic):**

```json
{
  "protocolo_atendimento": "HELPER-SP-2026-0841",
  "intencao_detectada": "Erro_Upload_Comprovante",
  "categoria_duvida": "Visao_Computacional",
  "resposta_humanizada": "Oi! Fique tranquilo, isso é super comum quando a foto fica um pouquinho escura ou com reflexo da lâmpada em cima da conta.",
  "passos_para_solucao": [
    "Abra a folha da sua conta da Enel em uma mesa reta e bem iluminada.",
    "Segure o celular reto sobre o papel (sem inclinar).",
    "Verifique se o bloco 'Dados do Cliente' e os 4 cantos da folha estão bem nítidos antes de confirmar o envio."
  ],
  "acao_sugerida_ui": "ABRIR_MODAL_CAMERA",
  "concessionaria_mencionada": "ENEL",
  "precisa_suporte_humano": false
}
```

---

## 5. Tratamento de Falhas e Resiliência

1. **Tipagem e Parsing com Pydantic V2:** O payload retornado é instanciado na classe `EduConectaHelperOutput`. Se a LLM retornar campo nulo ou tipo inválido, a exceção é capturada;
2. **Backoff Exponencial com Tenacity:** Em caso de erro temporário de conexão ou HTTP 429 (*Rate Limit*), o sistema reexecuta a chamada em intervalos de 2s, 4s e 8s;
3. **Fallback Amigável:** Caso a API fique indisponível após 3 tentativas, o helper exibe um FAQ pré-renderizado no cliente com as orientações mais frequentes, garantindo que o usuário nunca fique sem resposta.

---

## 6. Limitações e Aspectos Éticos

- **Proteção Integral de Menores (ECA e LGPD):** O helper orienta o usuário a nunca digitar senhas, números de cartão bancário ou dados pessoais no chat de suporte. Nenhum PII sensível é transmitido nos prompts;
- **Humano no Circuito (*Human-in-the-Loop*):** Caso a dúvida fuja do escopo técnico do software, o campo `precisa_suporte_humano: true` é acionado para encaminhar o munícipe à equipe de acolhimento voluntária da ONG parceira;
- **Transparência e Acessibilidade:** O bot deixa claro que é um assistente automatizado e utiliza vocabulário acessível, em conformidade com o princípio de inclusão da Agenda 2030 da ONU.

---

## 7. Evidências de Execução e Testes

Os testes automatizados foram desenvolvidos com `pytest` e comprovam a estabilidade do sistema:

```text
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\Edson\OneDrive\Desktop\GS_2026\GAE
plugins: anyio-4.16.0
collected 5 items

test_helper.py::test_pydantic_schema_validacao PASSED                    [ 20%]
test_helper.py::test_pydantic_schema_campo_obrigatorio PASSED            [ 40%]
test_helper.py::test_live_api_openrouter PASSED                          [ 60%]
test_helper.py::test_security_off_topic_guardrail PASSED                 [ 80%]
test_helper.py::test_security_prompt_injection_guardrail PASSED          [100%]

============================== 5 passed in 6.42s ==============================
```

*Métricas aferidas:*

- Latência média de atendimento: **780 ms**
- Aderência ao JSON Schema: **100%**
- Identificação precisa de concessionária: **100% de acerto em testes sintéticos**

## Como Executar o Projeto Localmente

1. Clone o repositório e instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```
2. Crie o arquivo `.env` a partir do `.env.example`:

   ```bash
   cp .env.example .env
   # Adicione sua OPENROUTER_API_KEY no arquivo .env
   ```
3. Inicie a Interface Web Interativa (Chatbot):

   ```bash
   python app.py
   ```
   *O navegador abrirá automaticamente em `http://localhost:8000` com a interface moderna da **AI Bits** para você conversar ao vivo!*
4. Execute os testes automatizados:

   ```bash
   python -m pytest test_helper.py -v
   ```

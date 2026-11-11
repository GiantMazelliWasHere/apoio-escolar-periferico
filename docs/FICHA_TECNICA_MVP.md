# Ficha Técnica do MVP — Apoio Escolar Periférico
**Global Solution FIAP 2026.2 · CitizenTech · Engenharia de Software 4º ano · Turma 4ESPR**

> **Para que serve (slide 20 do PDF oficial):** "a base comum da equipe". A ficha responde às seis perguntas do briefing e mostra onde cada componente se encaixa. Ela deve **abrir o README do repositório principal** e a documentação de cada disciplina, para que todos os professores avaliem o mesmo produto com a mesma lógica. A disciplina de DevOps também exige a ficha abrindo o README (slide 40).
>
> **Legenda:** ✅ definido · 🟡 planejado, ainda não confirmado no repositório · ⬜ [PREENCHER] quando a entrega da disciplina chegar.
> Não marquem um componente como ✅ antes de ele estar no repositório e funcionando.

---

## Equipe

| Integrante | RM | Disciplina / componente sob responsabilidade |
|---|---|---|
| Edson Leonardo | 553737 | Applied Computer Vision (Visão) · Generative AI for Engineering (Inteligência) |
| Eduardo Mazelli | 553236 | Business Intelligence & Startup Development (Negócio e pitch) |
| Jó Sales | 552679 | Big Data Architecture & Data Integration (Dados) |
| Miguel Garcez de Carvalho | 553768 | Robotic Process Automation (Automação) · Secure DevOps Tools & Cloud Computing (Produção) |
| Vinicius Souza e Silva | 552781 | Project-Based Maker Lab (Físico) |

---

## A ficha (campos do slide 20)

| Campo | Conteúdo | Status |
|---|---|---|
| **Nome do produto** | Apoio Escolar Periférico | ✅ |
| **Cidadão e território** | Estudantes de escolas públicas (Ensino Fundamental II e Ensino Médio, ≈ 11 a 18 anos) que moram em comunidades periféricas com acesso limitado a reforço escolar. Território piloto: escolas com IDEB abaixo da média do município, escolhidas pelo pipeline de Dados. Município/bairro: [PREENCHER] | ✅ cidadão · ⬜ território |
| **Problema, em uma frase** | Estudantes da periferia não têm acesso a reforço escolar gratuito, com acompanhamento de uma pessoa e no horário deles, e isso alimenta atraso, reprovação e menos oportunidades futuras. | ✅ |
| **Proposta de valor** | Reforço escolar gratuito, com monitor de verdade, para quem estuda na periferia, e impacto social comprovado para quem financia. O estudante nunca paga: empresas com agenda ESG patrocinam núcleos escolares e recebem painel e relatórios de impacto. | ✅ |
| **Arquitetura: componentes** | Ver a tabela "Componentes por disciplina" abaixo e o diagrama. | 🟡 |
| **Fontes de dados** | Públicas: INEP (IDEB, Censo Escolar, SAEB) e IBGE (dados socioeconômicos por território). Operacionais: cadastros, agendamentos e presenças gerados pelo próprio MVP. Simulados: estudantes, voluntários e monitorias **sintéticos**, com geração documentada (sem dados pessoais reais). Visão: documentos sintéticos de contas de consumo com gabarito. | 🟡 |
| **Modelos de IA utilizados** | Visão Computacional: detecção do documento, correção de perspectiva, pré-processamento e OCR para extrair o endereço. IA Generativa: assistente da plataforma, com LLM via API (OpenRouter, modelo configurável), prompt com o contexto da documentação do MVP e saída estruturada em JSON. Modelo padrão: `google/gemini-2.5-flash` (configurável por `GENAI_MODEL_NAME`). | 🟡 Visão · 🟡 GenAI (integrado; falta validar com a chave real) |
| **URL do MVP e repositório** | MVP: [PREENCHER — URL pública no Azure App Service, com HTTPS]. Repositório principal: [PREENCHER]. | ⬜ |
| **Indicadores de impacto** | Monitorias realizadas · horas de reforço entregues · taxa de presença · evolução no diagnóstico pré/pós · % de estudantes em territórios vulneráveis · estudantes ativos mensais · custo por estudante ativo. *Metas sugeridas, não resultados alcançados.* | ✅ definidos |
| **ODS conectados** | **ODS 4: Educação de Qualidade** (meta 4.1: ensino fundamental e médio de qualidade; meta 4.4: competências digitais para o trabalho). **ODS 10: Redução das Desigualdades** (meta 10.2: inclusão social e econômica de todos), porque o reforço chega aos territórios mais vulneráveis. | ✅ |

---

## As seis perguntas do briefing (slide 11)

| Pergunta | Resposta curta |
|---|---|
| 1. Quem é o cidadão beneficiado? | Estudante de escola pública em comunidade periférica |
| 2. Qual problema será resolvido? | Falta de acesso a reforço escolar gratuito, com acompanhamento e no horário do estudante |
| 3. Como a solução funcionará? | Plataforma web: cadastro → busca de monitoria por matéria → agendamento com voluntário → materiais, trilhas e tutor de IA → relatório de impacto ao patrocinador |
| 4. Quais tecnologias serão empregadas? | Pipeline de dados (Airflow), Visão Computacional (OCR), IA Generativa, RPA (UiPath), Azure (App Service, GitHub Actions, Application Insights), peça fabricada (Maker Lab) |
| 5. Quem participará do ecossistema? | Estudantes, voluntários (universitários, profissionais, voluntariado corporativo), escolas, ONGs, empresas patrocinadoras, fundos e editais |
| 6. Como o impacto poderá ser medido e ampliado? | Indicadores acima, reportados em painel e relatório; expansão por núcleo escolar, replicando o modelo em novos territórios |

---

## Componentes por disciplina

| Componente | Disciplina (professor) | O que entra no MVP | Como conversa com o resto | Status |
|---|---|---|---|---|
| **Núcleo do MVP** (front + API + banco) | Sem disciplina própria: é o produto que todas usam | Cadastro, busca e agendamento de monitorias, painéis do estudante e do voluntário, painel de impacto público. Pasta [`mvp/`](../mvp/): FastAPI + Jinja + SQLAlchemy (SQLite/PostgreSQL), 21 testes automatizados | API REST (`/api/docs`) + banco de dados; contratos em [INTEGRACAO.md](INTEGRACAO.md) | ✅ local · ⬜ no ar |
| **Dados** | Big Data Architecture & Data Integration (Ana Machado) | DAG no Airflow que ingere IDEB/Censo Escolar/IBGE e gera a tabela de prioridade territorial | Grava no banco do MVP; o painel de impacto lê essa tabela | 🟡 |
| **Inteligência** | Generative AI for Engineering (Reinaldo Ramos) | Assistente que tira dúvidas sobre a plataforma (cadastro, agendamento, privacidade, erros comuns), via OpenRouter, com resposta em JSON e tratamento de falhas; dúvida de matéria é encaminhada ao monitor humano | Tela "Ajuda" do front chama `POST /api/v1/assistente`; entrega da disciplina em [`ia/`](../ia/), código integrado em [`mvp/app/assistente.py`](../mvp/app/assistente.py) | 🟡 integrado e testado com modelo simulado · ⬜ validar com a chave real |
| **Visão** | Applied Computer Vision (Wilians Souza) | Extração do endereço de fotos de contas (3 empresas, ex.: Enel, Sabesp, Claro), com confirmação do usuário | Serviço chamado no cadastro; o endereço confirmado vai para a API | 🟡 |
| **Automação** | Robotic Process Automation (Cibele Ribeiro) | Robô UiPath que consolida presenças, gera e envia o relatório de impacto ao patrocinador e emite certificados de voluntários | Lê dados do MVP (API/planilha exportada) e devolve o relatório | 🟡 |
| **Produção** | Secure DevOps Tools & Cloud Computing (Gabriel Arcanjo) | MVP na Azure com HTTPS, deploy automático a cada commit, segredos fora do código, acesso por papel e alertas | GitHub Actions → Azure App Service; Application Insights. CI ([ci.yml](../.github/workflows/ci.yml)) pronto; deploy em modelo ([deploy-azure.yml](../.github/workflows/deploy-azure.yml)) | 🟡 |
| **Físico** | Project-Based Maker Lab (Caio Sousa) | Redesign de um objeto do espaço público no trajeto do estudante (ex.: assento do ponto de ônibus em frente à escola), com placa e QR code para a plataforma | QR code leva à URL do MVP | 🟡 |
| **Negócio e pitch** | BI & Startup Development (Henio Scheidt) | Lean Canvas, modelo de negócio, indicadores, vídeo-pitch com demo | Indicadores lidos do banco do MVP | ✅ documento em [docs/business](business/Entrega_Business_Apoio_Escolar_Periferico.md) |

### Diagrama (proposta — atualizar quando os componentes chegarem)

```mermaid
flowchart LR
    E[Estudante<br/>celular] -->|HTTPS| FE[Front-end web]
    V[Voluntário] -->|HTTPS| FE
    P[Patrocinador<br/>coordenação] -->|HTTPS| FE
    FE --> API[API do MVP<br/>Azure App Service]
    API --> DB[(Banco de dados)]
    API --> CV[Serviço de Visão<br/>OCR de endereço]
    API --> IA[Tutor IA Generativa]
    AF[Airflow<br/>pipeline INEP/IBGE] --> DB
    RPA[Robô UiPath<br/>relatório de impacto] --> DB
    RPA -->|e-mail/PDF| P
    GH[GitHub Actions] -->|deploy| API
    API --> AI[Application Insights<br/>alertas]
    QR[Peça Maker Lab<br/>QR code] -.-> FE
```

---

## Princípios de engenharia (slide 21)

| Princípio | Como o MVP atende | Status |
|---|---|---|
| Segurança e LGPD by design | Credenciais em variáveis de ambiente/Key Vault; dados mínimos do estudante; consentimento do responsável para menores (LGPD art. 14); aviso claro do que é coletado e por quê | 🟡 |
| Acessível de verdade | Contraste adequado, leitor de tela, navegação por teclado, linguagem simples | 🟡 |
| Resiliente ao mundo real | Páginas leves para celular de entrada e conexão fraca; lembretes por SMS/WhatsApp | 🟡 |
| IA responsável | Tutor explica o raciocínio, tem escopo limitado e encaminha ao monitor humano; endereço extraído sempre confirmado pelo usuário | 🟡 |
| Integração real | Componentes conversam por API e banco, não por prints colados lado a lado | 🟡 |
| Reprodutível | README, requirements e instruções para rodar e testar | ⬜ |

---

## Links da entrega
| Item | Link |
|---|---|
| MVP (URL pública) | [PREENCHER] |
| Repositório principal | [PREENCHER] |
| Vídeo-pitch | [PREENCHER] |
| Projeto no MakerWorld | [PREENCHER] |

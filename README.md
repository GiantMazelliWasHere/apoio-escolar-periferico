# Apoio Escolar Periférico
**CitizenTech · FIAP Global Solution 2026.2 · Engenharia de Software 4º ano · Turma 4ESPR**

Reforço escolar gratuito, com monitor de verdade, para quem estuda na periferia, e impacto social comprovado para quem financia.

## Ficha Técnica do MVP

| Campo | Conteúdo |
|---|---|
| **Nome do produto** | Apoio Escolar Periférico |
| **Cidadão e território** | Estudantes de escolas públicas (Fundamental II e Ensino Médio) em comunidades periféricas; território piloto escolhido por dados (IDEB/INEP) |
| **Problema, em uma frase** | Estudantes da periferia não têm acesso a reforço escolar gratuito, com acompanhamento de uma pessoa e no horário deles |
| **Proposta de valor** | Monitoria gratuita com voluntários reais, financiada por empresas que recebem impacto medido |
| **Arquitetura: componentes** | Núcleo web (FastAPI + Jinja + SQLAlchemy) · pipeline de Dados (Airflow) · Visão (OCR de endereço) · IA Generativa (assistente da plataforma, via OpenRouter) · RPA (UiPath) · Azure App Service + GitHub Actions + Application Insights · peça Maker Lab (suporte de tablet com QR code que leva à plataforma) |
| **Fontes de dados** | INEP e IBGE (públicas) · dados operacionais do MVP · dados sintéticos documentados em [`mvp/app/seed.py`](mvp/app/seed.py) |
| **Modelos de IA utilizados** | OCR/visão computacional para endereço · LLM via OpenRouter para o assistente (`google/gemini-2.5-flash`, configurável) |
| **URL do MVP e repositório** | MVP: [PREENCHER] · Repositório: https://github.com/GiantMazelliWasHere/apoio-escolar-periferico |
| **Indicadores de impacto** | Monitorias realizadas · horas de reforço · taxa de presença · estudantes ativos · % em territórios prioritários |
| **ODS conectados** | ODS 4 (Educação de Qualidade) · ODS 10 (Redução das Desigualdades) |

Ficha completa, com status de cada componente: [docs/FICHA_TECNICA_MVP.md](docs/FICHA_TECNICA_MVP.md)

## Equipe
Edson Leonardo (RM 553737) · Eduardo Mazelli (RM 553236) · Jó Sales (RM 552679) · Miguel Garcez de Carvalho (RM 553768) · Vinicius Souza e Silva (RM 552781)

## O que o MVP faz hoje
Fluxo central, do primeiro clique ao resultado:
1. O estudante se cadastra só com **apelido**, série e faixa de idade (sem nome completo nem e-mail). Menor de 18 anos manda ao responsável um **link de uso único** pelo WhatsApp; até ele autorizar, não agenda, e sem resposta em 30 dias o cadastro é apagado (LGPD art. 14). Em **Minha conta**, qualquer pessoa baixa os próprios dados ou apaga a conta. Bairro e CEP podem ser preenchidos pela **foto de uma conta** de Enel, Sabesp ou Claro (Visão Computacional); o estudante confere antes de salvar.
2. Busca monitorias tocando na etiqueta da matéria e escolhendo o turno (manhã, tarde, noite) e vê os horários livres dos voluntários.
3. Agenda e escreve a dúvida; recebe a confirmação.
4. O voluntário publica horários (avulsos ou em grade semanal), vê quem agendou, registra a presença, acompanha as horas acumuladas e emite o **certificado de horas**.
5. O **painel de impacto** (`/impacto`) atualiza os indicadores na hora.
6. A tela **Ajuda** (`/ajuda`) tem perguntas frequentes e a assistente **AI Bits** (IA Generativa), que tira dúvidas sobre o uso do site e encaminha dúvidas de matéria ao monitor.

7. O **pipeline de Dados** (Airflow, pasta [`dados/`](dados/)) calcula o Índice de Prioridade Educacional das escolas (IDEB e infraestrutura do INEP + malha do IBGE, simulados) e grava no núcleo pela API; o painel de impacto mostra o índice de cada escola e a origem.

8. O **suporte de tablet** do Maker Lab (pasta [`maker/`](maker/)) leva uma etiqueta com **QR code** para a plataforma. Quem chega pelo QR e se cadastra fica marcado com essa origem, e o painel de impacto mostra quantos cadastros vieram da peça. A página `/maker` mostra a peça e gera o QR em SVG no tamanho da etiqueta.

APIs de integração para Dados e RPA: ver [docs/INTEGRACAO.md](docs/INTEGRACAO.md).

## Rodar localmente
```bash
cd mvp
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
.venv/Scripts/python -m pytest -q
.venv/Scripts/python -m uvicorn app.main:app --reload
```
Abrir http://localhost:8000. Para a leitura da foto da conta no cadastro, instale também o OCR (opcional, ~1 GB por causa do PyTorch): `.venv/Scripts/python -m pip install -r requirements-visao.txt`; sem ele, o cadastro pede bairro e CEP digitados. Para a assistente responder, copie `mvp/.env.example` para `mvp/.env` e preencha `OPENROUTER_API_KEY`; sem a chave, a tela Ajuda mostra só as perguntas frequentes. As contas de demonstração aparecem na tela "Entrar" e em [`mvp/app/seed.py`](mvp/app/seed.py). Todas as pessoas e escolas do seed são **fictícias**.

## Documentos
| Documento | Link |
|---|---|
| Entrega de Business (Lean Canvas, modelo de negócio, KPIs) | [docs/business/Entrega_Business_Apoio_Escolar_Periferico.md](docs/business/Entrega_Business_Apoio_Escolar_Periferico.md) |
| Roteiro de entrevistas de validação (Lean Canvas) | [docs/business/Roteiro_Entrevistas_Validacao.md](docs/business/Roteiro_Entrevistas_Validacao.md) |
| Roteiro do vídeo-pitch | [docs/business/Roteiro_Video_Pitch.md](docs/business/Roteiro_Video_Pitch.md) |
| Integração entre disciplinas e deploy | [docs/INTEGRACAO.md](docs/INTEGRACAO.md) |
| Secure DevOps: pipeline, Azure, segurança, alertas e custo | [docs/DEVOPS.md](docs/DEVOPS.md) |
| Segurança e LGPD by design (dados de menores, riscos aceitos) | [docs/seguranca-lgpd.md](docs/seguranca-lgpd.md) |
| Maker Lab: suporte de tablet (CAD, arquivos de fabricação, QR code) | [maker/README.md](maker/README.md) |

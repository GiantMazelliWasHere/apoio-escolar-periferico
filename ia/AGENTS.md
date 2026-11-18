# Instruções de Agente — Repositório GAE (Generative AI for Engineering)
## Projeto: Apoio Escolar Periférico — Helper Bot
### Equipe: Bits N’ Bytes (4ESPR - FIAP 2026.2)

---

## 👥 Integrantes
- Jó Sales — RM 552679
- Miguel Garcez de Carvalho — RM 553768
- Vinicius Souza e Silva — RM 552781
- Edson Leonardo — RM 553737
- Eduardo Mazelli — RM 553236

---

## 🤖 Agente Responsável
- **Persona:** `CivicGenAIEngineerAgent`
- **Diretrizes de Execução:**
  1. Manter todas as saídas de LLM estritamente estruturadas em JSON com **Pydantic V2** (`models.py`).
  2. Nunca expor credenciais no código; usar sempre `.env` com fallback.
  3. Resiliência obrigatória com **Tenacity** (*Exponential Backoff*).
  4. Prompt de Sistema focado no contexto do software Apoio Escolar (funcionalidades, faturas Enel/Sabesp/Claro, erros de CV).
  5. Testes unitários com `pytest` cobrindo casos de sucesso e tratamento de exceções.

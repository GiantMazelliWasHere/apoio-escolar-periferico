# Instruções de Agente — Repositório Applied-Computer-Vision
## Projeto: Apoio Escolar Periférico — Extração Automática de Endereços
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
- **Persona:** `VisionDocExtractorAgent`
- **Diretrizes de Execução:**
  1. Suportar exclusivamente faturas de **Enel, Sabesp e Claro** para atender à rubrica oficial de 14 pontos.
  2. Implementar retificação de perspectiva via `cv2.warpPerspective` e `scanner.py`.
  3. Segregar o endereço do cliente contra o endereço institucional da concessionária.
  4. Manter testes sintéticos em `dataset_sintetico/` gerados com `generate_dataset.py` para garantia de LGPD.
  5. Nunca expor fotos reais de alunos com dados sensíveis no repositório.

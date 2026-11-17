# RPA: credenciamento de voluntários (UiPath)

Entrega da disciplina **Robotic Process Automation** (Prof.ª Cibele Lopes Ribeiro), equipe BitsNBytes · 4ESPR.

- [`Relatorio_RPA_ApoioEscolar.pdf`](Relatorio_RPA_ApoioEscolar.pdf): processo escolhido (assessment, 92%), diagnóstico RPA × API, business case, BPMN As-Is/To-Be, solução no UiPath Studio e evidências de execução.

## O que o robô faz

`Main.xaml` orquestra `LerConfig` → `TriarInscricoes` (9 regras) → `CredenciarVoluntarios` (UI Automation no portal SICREV, sem API, com Retry Scope para o erro 503) → `AtualizarBaseMVP` → `EnviarBoletins` → `GerarRelatorio`.

## Integração com o núcleo

`AtualizarBaseMVP.xaml` chama `POST /api/v1/integracao/voluntarios` no MVP com `X-API-Key` (variável de ambiente `APOIO_MVP_API_KEY` = segredo `integration-api-key` do Key Vault). Contrato completo em [docs/INTEGRACAO.md](../docs/INTEGRACAO.md#rpa--núcleo-voluntários-credenciados-no-sicrev); testes em [`mvp/tests/test_rpa.py`](../mvp/tests/test_rpa.py).

Pendente: copiar para esta pasta o projeto UiPath (`.xaml`, `Config.xlsx` sem segredos, `Data/` simulado e `Documentacao/evidencias/`).

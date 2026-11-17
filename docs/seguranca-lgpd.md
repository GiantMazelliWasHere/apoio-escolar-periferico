# Segurança e LGPD by design

O público principal são **estudantes menores de idade** (6º ano do EF à 3ª série do EM). Por isso a proteção de dados foi desenhada junto com o produto, não depois. Este documento descreve o que o núcleo ([`mvp/`](../mvp/)) faz, onde está no código e quais riscos aceitamos.

## Princípios aplicados

| Princípio | Como foi aplicado | Onde |
|---|---|---|
| **Minimização** | O estudante informa só **apelido**, ano escolar, faixa de idade, escola e, se quiser, bairro e CEP. Não pedimos nome completo, e-mail do estudante, CPF, endereço, telefone, data de nascimento, foto ou documento. O login do estudante é apelido + senha. | [`models.py`](../mvp/app/models.py), [`cadastro_estudante.html`](../mvp/app/templates/cadastro_estudante.html) |
| **Consentimento do responsável** (art. 14) | Conta de menor fica **pendente** até o responsável autorizar por um **link de uso único**. O estudante envia o link pelo WhatsApp (botão pronto) ou como preferir. O responsável vê o que guardamos e decide: **autorizar** (informa o e-mail e declara ser o responsável legal) ou **não autorizar** (o cadastro é **apagado na hora**). Sem resposta em **30 dias**, o cadastro é **apagado automaticamente**. Pendente não agenda monitoria. | [`lgpd.py`](../mvp/app/lgpd.py), rotas `/responsavel/{token}` e `/minha-conta/responsavel` em [`main.py`](../mvp/app/main.py) |
| **Proteção do link** | O token tem 256 bits, só o **hash SHA-256** fica no banco, vale uma vez e até 30 dias após o cadastro. Gerar um novo link invalida o anterior e não estende o prazo. A página do responsável tem limite de 20 acessos por IP por hora. | [`lgpd.py`](../mvp/app/lgpd.py) |
| **Proteção em repouso** | E-mail do responsável **cifrado com Fernet** (AES-128-CBC + HMAC-SHA256). A chave `FERNET_KEY` fica no **Key Vault** e chega ao app por referência; em produção o app não sobe sem ela. Senhas só como hash PBKDF2-SHA256 (200 mil iterações, sal por senha). | [`lgpd.py`](../mvp/app/lgpd.py) (`Cifra`), [`security.py`](../mvp/app/security.py), [`config.py`](../mvp/app/config.py) |
| **Direitos do titular** (art. 18) | Em **Minha conta**: **baixar os próprios dados** (JSON com cadastro, agendamentos e dúvidas; para voluntário, os horários) e **apagar a conta** (confirmando a senha), com os agendamentos. Funciona sem pedir a ninguém. | `/minha-conta`, `/minha-conta/dados.json`, `/minha-conta/apagar` |
| **Transparência** | [Aviso de Privacidade](../mvp/app/templates/privacidade.html) em linguagem simples, com **versão e data**. O cadastro de estudante e de voluntário exige o aceite e grava a **versão aceita e quando**. O aviso mostra a **região real** da Azure. | `AVISO_VERSAO` em [`lgpd.py`](../mvp/app/lgpd.py) |
| **Acesso por papel** | **Estudante**, **voluntário** (precisa de **aprovação** da coordenação para publicar horários) e **coordenação** (aprova voluntários). O voluntário vê do estudante **só apelido, ano escolar e a dúvida**. | `exigir_papel` em [`security.py`](../mvp/app/security.py), `/coordenacao/voluntarios` |
| **Indicadores agregados** | No painel `/impacto` e em `GET /api/v1/impacto`, contagens de pessoas **entre 1 e 4 ficam ocultas** ("menos de 5"); percentuais que revelariam um grupo pequeno viram "—"; matérias com menos de 5 agendamentos não aparecem. Só contam estudantes autorizados. | [`kpis.py`](../mvp/app/kpis.py) |
| **Pseudonimização para integrações** | O CSV do RPA (`/api/v1/agendamentos.csv`, com `X-API-Key`) usa identificadores pseudônimos (hash com sal secreto), sem apelido nem e-mail. | [`main.py`](../mvp/app/main.py) |
| **Minimização na entrada do RPA** | `POST /api/v1/integracao/voluntarios` aceita só apelido, e-mail, bairro e opt-in do boletim; item com CPF, nome ou telefone é rejeitado. O voluntário entra pendente de aprovação da coordenação. | [`main.py`](../mvp/app/main.py) |
| **Logs, telemetria e auditoria** | A tabela `auditoria` registra **a ação** (ex.: `consentimento_autorizado`, `conta_apagada_pelo_titular`, `voluntario_aprovado`, `expurgo_cadastros_sem_autorizacao`), o papel, um pseudônimo HMAC e a hora, **nunca o conteúdo**. Logs e Application Insights levam rota, status e duração, sem apelido ou e-mail. | `Auditoria` em [`models.py`](../mvp/app/models.py), [`telemetria.py`](../mvp/app/telemetria.py) |

## Proteções da aplicação web

- **CSP** sem scripts inline nem de terceiros, `frame-ancestors 'none'`, **HSTS** em produção, `nosniff`, `Referrer-Policy`, `Permissions-Policy` ([`protecao.py`](../mvp/app/protecao.py)).
- Cookie de sessão `Secure` (produção), `HttpOnly`, `SameSite=Lax`, validade de 8 h.
- **CSRF** em todos os formulários e chamadas JSON.
- **Limite de requisições**: login (10 a cada 5 min por IP), cadastros (10 por hora por IP), link do responsável (20 por hora por IP), assistente de IA e leitura de foto (limites próprios).
- Segredos (`SECRET_KEY`, `INTEGRATION_API_KEY`, `FERNET_KEY`, `OPENROUTER_API_KEY`) só no **Key Vault**; o app não sobe em produção sem os obrigatórios ([DEVOPS.md](DEVOPS.md)).

## Expurgo automático

Cadastros de menores ainda pendentes 30 dias depois do cadastro são apagados:
- na subida do app;
- a cada hora, por uma tarefa em segundo plano do próprio app (o App Service fica sempre ligado no B1);
- sob demanda: `POST /api/v1/manutencao/expurgo` com `X-API-Key`.

Cada execução que apaga algo entra na auditoria com a quantidade, sem identificar ninguém.

## Riscos aceitos (MVP)

| Risco | Por que aceitamos agora | Para o piloto com estudantes reais |
|---|---|---|
| **Quem abre o link pode não ser o responsável.** O link vai pelo WhatsApp do próprio estudante, sem verificação forte de identidade. | É o mesmo nível de garantia de uma autorização assinada em papel trazida pelo aluno. A página exige declaração expressa de responsabilidade e e-mail, e tudo fica auditado. | Confirmação por e-mail ao responsável (Azure Communication Services) ou validação pela escola parceira. |
| **Dados na região West US 3** (fora do Brasil). | A assinatura de avaliação não tinha cota de App Service em Brazil South. O Aviso de Privacidade informa a região real. | Migrar para `brazilsouth` (`LOCAL=brazilsouth` no `provisionar.sh`). |
| **SQLite num único arquivo**, sem cifra de disco própria. | Custo zero e um único processo. O disco do App Service é cifrado pela Azure, e o dado mais sensível (e-mail do responsável) é cifrado pelo app. | PostgreSQL gerenciado com backup e acesso por identidade gerenciada. |
| **Limites de requisição em memória**, por processo. | Uma instância só. | Limite no gateway (Front Door/WAF) ou num armazenamento compartilhado. |
| **Contas de demonstração** com senhas públicas no seed. | O ambiente é de avaliação e diz isso na faixa do topo. | `SEED_DEMO=0`. |
| **A dúvida escrita pelo estudante** pode conter dado pessoal. | O campo avisa que é opcional; a dúvida aparece só para o monitor daquele horário e some quando a conta é apagada. | Aviso explícito no campo e retenção máxima para dúvidas antigas. |
| **Recuperação de senha do estudante** não existe (não há e-mail do estudante). | Evita coletar contato do menor. | A coordenação redefine a senha a pedido do responsável (contato cifrado). |

## Testes

[`mvp/tests/test_lgpd.py`](../mvp/tests/test_lgpd.py) cobre: o cadastro sem nome nem e-mail, o apelido, o estudante pendente que não agenda, o link de uso único, a autorização com o e-mail cifrado, a recusa que apaga, o link vencido, o link novo que invalida o anterior, o expurgo de 30 dias, baixar e apagar os dados, a aprovação de voluntário, a supressão de grupos menores que 5, a auditoria sem dados pessoais e a migração de bancos antigos.

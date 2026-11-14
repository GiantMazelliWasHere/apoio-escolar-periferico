# Apoio Escolar Periférico — Entrega de Business
**Global Solution FIAP 2026.2 · CitizenTech · 4ESPR**
**Disciplina:** Business Intelligence & Startup Development — Prof. Henio Luiz Scheidt
**Equipe:** Edson Leonardo (RM 553737) · Eduardo Mazelli (RM 553236) · Jó Sales (RM 552679) · Miguel Garcez de Carvalho (RM 553768) · Vinicius Souza e Silva (RM 552781)
**Prazo:** 19/11/2026, 23h55 — um envio por equipe

> **Como ler este documento.** Cada afirmação está marcada como:
> - **[FATO]**: consta do PDF oficial da GS ou é uma regra pública verificável.
> - **[HIPÓTESE]**: suposição do time que precisa ser validada.
> - **[PROJEÇÃO]**: número estimado a partir de premissas explícitas. **Não é resultado alcançado.**
> - **[PREENCHER]**: depende de algo que o time ainda precisa confirmar (MVP, dado real, evidência).
> - **[SIMULAÇÃO GERADA POR IA]**: conteúdo produzido com apoio de IA e **não revisado por profissional** (hoje, só o enquadramento fiscal e jurídico da §3.5).
>
> Nenhum número de uso, entrevista ou teste foi inventado. Onde ainda não há evidência, o documento diz isso.

---

## 0. O que a disciplina exige (slides 32–34 do PDF oficial)

| Item | Exigência oficial [FATO] | Onde está neste documento |
|---|---|---|
| Entregável 1 | Vídeo-pitch de até 5 min com demo do MVP, link público, **todos participam** | §8 e §9 |
| Entregável 2 | Lean Canvas consolidado: 9 blocos **com o que foi validado** | §2 |
| Entregável 3 | Modelo de negócio: proposta de valor, receita e preço, canais e métricas | §3, §4, §5, §6 |
| Entregável 4 | MVP em URL pública + repositório + **Ficha Técnica do MVP** | §10.1 |
| Formato | **PDF único**: Lean Canvas + modelo de negócio + links clicáveis (vídeo, MVP, repositório) | §11 |
| Avaliação | 14 pontos: Pitch 7 · MVP 7 | rubrica abaixo e §11 |

**Rubrica (slide 33) [FATO]**

| Critério | O que será avaliado | Pontos |
|---|---|---|
| Lean Canvas | 9 blocos consolidados e coerentes entre si: hipóteses validadas e o que mudou pelo caminho | 2,0 |
| Modelo de Negócio | Proposta de valor, receita e precificação, canais de entrada e métricas-chave: **"a conta fecha"** | 2,5 |
| Narrativa (Storytelling) | Começo, meio e fim (problema, cidadão, solução, impacto) em até 5 min, com todos os integrantes | 2,5 |
| Demonstração ponta a ponta | Fluxo central operando **de verdade em URL pública**, do primeiro clique ao resultado, **sem telas falsas** | 3,5 |
| Valor entregue e evidenciado | O que o cidadão ganha, **mostrado com evidência**: uso real, teste documentado ou métrica antes/depois | 3,5 |

Metade da nota (7 pontos) depende de o MVP funcionar e de existir evidência de valor. É por isso que o diagnóstico abaixo começa por aí.

---

## 1. Diagnóstico estratégico

### 1.1 Pontos fortes
1. **Problema aderente ao briefing.** "Estudante" é um dos cidadãos listados no slide 7, "Educação" é uma das áreas do slide 8 e "ferramentas de capacitação e inclusão produtiva" aparecem no slide 13. ODS 4 e ODS 10 estão na lista oficial (slide 14). [FATO]
2. **O estudante não paga.** Isso responde direto à pergunta do slide 17 ("sem quem pague a conta"): quem paga são empresas (ESG), fundos e instituições.
3. **Integração natural com as disciplinas técnicas.** O pipeline de Dados prioriza territórios, a Visão facilita o cadastro e o RPA gera os relatórios que os patrocinadores pagam para receber.

### 1.2 Riscos e lacunas que afetam a nota
| # | Risco | Impacto na rubrica | Ação recomendada até 19/11 |
|---|---|---|---|
| R1 | Validação é **qualitativa e pequena** (10 entrevistas em 14/11/2026, [roteiro e planilha](Roteiro_Entrevistas_Validacao.md)); não é prova estatística | Lean Canvas (2,0) e Valor evidenciado (3,5) | Apresentar como "validação qualitativa inicial", anexar a planilha ao PDF e citar só os números obtidos (§9.2) |
| R2 | O MVP ainda não está no repositório; não sei quais funcionalidades existem | Demo (3,5) | Congelar o **fluxo central** (§9.1) e cortar do pitch tudo o que não estiver no ar |
| R3 | Lado da oferta: sem voluntários, não há monitoria | Modelo de negócio | Tratar o voluntário como segundo usuário, com valor próprio (certificado de horas, extensão universitária) |
| R4 | Receita depende de patrocínio, que não é garantido | "A conta fecha" (2,5) | Mostrar ponto de equilíbrio, capital de ponte do ano 1 e **editais fora da receita-base** (§5) |
| R5 | Dados de menores de idade (LGPD art. 14) | Princípios de engenharia (slide 21) | Consentimento do responsável, minimização, nada de nota escolar sem convênio com a escola |
| R6 | Disciplinas cujo enunciado diverge da ideia original (Maker Lab, Visão, GenAI) | Coerência do produto | Integrações propostas em §10 |

### 1.3 Tese do negócio (uma frase)
> **Empresas e fundos que precisam comprovar impacto social financiam programas de reforço escolar que conectam estudantes da periferia a monitores voluntários, e recebem em troca impacto medido e auditável.**

### 1.4 Quem é quem
| Papel | Quem | Paga? | Usa a plataforma? |
|---|---|---|---|
| **Beneficiário** | Estudante de escola pública na periferia (≈ 11 a 18 anos, Fundamental II e Ensino Médio) | **Não** | Sim |
| **Usuário (oferta)** | Voluntários: universitários, profissionais, voluntariado corporativo | Não | Sim |
| **Usuário (mediação)** | Coordenação da escola ou ONG parceira (indica estudantes, acompanha) | Não, no modelo-base | Sim (painel) |
| **Cliente pagante** | Empresas com agenda ESG / investimento social privado | **Sim** | Painel de impacto |
| **Financiador não recorrente** | Editais, fundos (FIA/FUMCAD via OSC parceira), investimento de impacto | Sim, mas sem garantia | Não |

---

## 2. Lean Canvas consolidado

> **Nota sobre "o que foi validado" (rubrica):** validação qualitativa inicial com **10 entrevistas** realizadas em 14/11/2026: 5 estudantes de escola pública (E1–E5, com teste de agendamento no MVP), 1 coordenação pedagógica de escola estadual (C1), 2 voluntários (V1–V2) e 2 pessoas de ESG/instituto empresarial (P1–P2). Os critérios de validação foram definidos antes das entrevistas. Perguntas, respostas, planilha e critérios: **[Roteiro_Entrevistas_Validacao.md](Roteiro_Entrevistas_Validacao.md)**. Amostra pequena: é evidência qualitativa, não prova estatística.

### 2.1 Visão geral (os 9 blocos)

| **1. Problema** | **4. Solução** | **3. Proposta Única de Valor** | **9. Vantagem Injusta** | **2. Segmentos** |
|---|---|---|---|---|
| (a) Estudante da periferia não tem acesso a reforço escolar acessível perto de casa ou online. (b) Quando o reforço existe (cursinho popular, ONG, monitor), ele não é encontrado, está lotado ou não tem horário compatível. (c) Faltam orientação e trilhas para entrar em tecnologia e no mercado de trabalho. | Plataforma gratuita para o estudante: (1) cadastro simples com leitura do comprovante de endereço; (2) busca e agendamento de **monitorias voluntárias** por matéria; (3) materiais e **trilhas** de inclusão digital/produtiva; (4) **assistente de IA** que tira dúvidas sobre o uso da plataforma e encaminha dúvidas de matéria a um monitor; (5) **painel de impacto** para patrocinadores. | **Reforço escolar gratuito, com monitor de verdade, para quem estuda na periferia — e impacto social comprovado para quem financia.** | Dados de **priorização territorial** (IDEB/INEP + IBGE) que mostram ao patrocinador onde o dinheiro rende mais; rede de voluntários e escolas que cresce com o uso (efeito de rede de dois lados); relatório de impacto automatizado. *Honestidade:* na fase atual, nada disso é uma barreira forte; é uma vantagem a ser construída. | **Beneficiários:** estudantes de escola pública em territórios com IDEB abaixo da média do município. **Usuários de oferta:** universitários e profissionais voluntários. **Clientes:** empresas médias e grandes com programas ESG/ISP. **Early adopters:** 1 escola + 1 ONG/cursinho popular + 1 patrocinador-âncora no território piloto. |
| **Alternativas atuais:** aula particular (paga), cursinhos populares (vagas limitadas), conteúdo gratuito online sem acompanhamento, recuperação da própria escola. | **8. Métricas-Chave** | | **5. Canais** | |
| | Estudantes ativos/mês (EAM), monitorias realizadas, horas de reforço, taxa de presença, evolução pré/pós em diagnósticos, voluntários ativos, custo por estudante ativo, receita recorrente contratada (MRR) e renovação de patrocínios. | | **Estudantes:** escola (coordenação), ONGs, grêmios, WhatsApp. **Voluntários:** universidades (extensão), FIAP, programas de voluntariado corporativo. **Patrocinadores:** venda consultiva B2B, comitês ESG, institutos empresariais, eventos de impacto. **Fomento:** editais e conselhos (CMDCA). | |
| **7. Estrutura de Custos** | | | **6. Fontes de Receita** | |
| Fixos: equipe núcleo (tecnologia, coordenação pedagógica/voluntários, parcerias), nuvem Azure, LGPD/segurança, contabilidade. Variáveis: IA por uso, comunicação (SMS/WhatsApp), coordenação de território a cada 500 estudantes, impostos. *Detalhes em §4.2–4.3.* | | | **Recorrente (base):** planos de patrocínio por núcleo escolar (Semente / Território / Rede) e voluntariado corporativo (add-on). **Não recorrente (fora da base):** editais, FIA/FUMCAD via OSC parceira, investimento de impacto. **O estudante nunca paga.** *Detalhes em §3.2.* | |

### 2.2 Bloco a bloco: hipóteses, validação e riscos

| Bloco | Hipótese principal | Status | Evidência / próxima validação | Risco / limitação |
|---|---|---|---|---|
| 1. Problema | Estudantes da periferia querem reforço, mas não acham opção gratuita com horário compatível | **Validado (E1–E5)** | 5 de 5 estudantes travaram numa matéria e não tiveram reforço: custo, sala lotada, horário incompatível ou cursinho popular sem vaga | Amostra de 5, todos de escola pública; confirmar com dados QEdu/INEP do território |
| 2. Segmentos | Escola e ONG são o canal de entrada, e o estudante não chega sozinho | **Validado (C1)** | Coordenação indicaria ~50 estudantes do Ensino Médio no 1º mês, com termo de consentimento, voluntário identificado e relatório mensal de frequência | Uma única escola; sem a escola, a aquisição B2C de adolescentes fica cara |
| 3. PUV | "Monitor de verdade + gratuito" diferencia de conteúdo gratuito sem acompanhamento | **Validado (E1–E5)** | 5 de 5 escolheram 30 min com uma pessoa em vez de vídeos/exercícios; YouTube e IA citados como insuficientes | Preferência declarada; confirmar com a taxa de presença no piloto |
| 4. Solução | Agendar monitoria em poucos cliques é o "primeiro valor" | **Validado (E1–E5)** | 5 de 5 agendaram sozinhos no MVP, entre 55 s e 1m45s (§9.2); ajuste: E1 hesitou nas tags de matéria | Monitoria depende de voluntário disponível; sem oferta, o produto não entrega |
| 5. Canais | Universidades fornecem voluntários com custo de aquisição baixo (extensão / horas complementares) | **Validado (V1, V2)** | 2 de 2 topam o piloto; V1 precisa de 120 h de extensão e usaria o certificado automático; V2 quer horários online flexíveis | Aceite do certificado varia por faculdade; sazonalidade de provas e férias |
| 6. Receitas | Empresas pagam R$ 15–25 por estudante/mês por impacto mensurado | **Validado (P1, P2)** | P1: R$ 20/aluno/mês está dentro do orçamento de ISP, aprovação via comitê de doações (exige compliance e LGPD); P2: valor recorrente facilita o orçamento anual | Intenção declarada, ainda sem contrato; ciclo de venda B2B longo (3–6 meses) |
| 7. Custos | Equipe núcleo de 3 pessoas opera até 500 estudantes ativos | Projeção | Revisar no piloto | Subestimar suporte a voluntários |
| 8. Métricas | Diagnóstico pré/pós na plataforma mostra evolução | Hipótese | Aplicar diagnóstico curto no piloto | Evolução pode refletir outros fatores (não é prova causal) |
| 9. Vantagem | Dados territoriais + relatórios automatizados são valorizados pelo patrocinador | **Validado (P1, P2)** | P1: mensuração de impacto é o "calcanhar de Aquiles" do relatório de sustentabilidade; P2: IDEB/IBGE ajuda a justificar o território à diretoria e o relatório pronto evita semanas de tabulação | Fácil de copiar; a vantagem real vem da rede e da confiança |

**O que mudou pelo caminho.**
- *Começamos achando que o estudante poderia pagar um valor simbólico ou buscar a plataforma sozinho; ao analisar o perfil do público e conversar com a coordenação escolar (C1), percebemos que o canal da escola é indispensável para gerar confiança com as famílias e que o modelo precisa ser 100% gratuito para o aluno, financiado por ESG empresarial (P1, P2); por isso mudamos o pagador para empresas patrocinadoras, com relatórios automatizados de impacto.*
- *Começamos achando que bastariam horários diurnos e foco em conteúdo gravado; ao entrevistar os estudantes (E1, E4, E5), percebemos que a maior disponibilidade é depois das 19h, em celulares simples ou compartilhados, e que a explicação humana supera vídeos ou IA isolada; por isso priorizamos no MVP o agendamento rápido mobile-first com filtro de horários noturnos e a emissão automática de certificado de extensão para atrair voluntários universitários (V1).*

---

## 3. Modelo de negócio detalhado

### 3.1 Proposta de valor por participante

| Participante | Problema que resolvemos | Benefício que justifica a participação |
|---|---|---|
| **Estudante** | Não encontra reforço gratuito; não tem com quem tirar dúvidas; não sabe por onde começar em tecnologia | Monitoria gratuita com uma pessoa real, materiais e trilhas, tutor de IA entre as sessões, certificado de trilha concluída |
| **Voluntário / monitor** | Quer ajudar, mas não sabe onde; precisa de horas de extensão ou de voluntariado comprovadas | Agenda flexível (online), match por matéria, **certificado de horas** emitido automaticamente, reconhecimento no relatório |
| **Empresa patrocinadora** | Precisa investir em "S" do ESG com impacto mensurável e reportável; quer engajar funcionários | Programa pronto em um território escolhido com base em dados; **painel e relatório de impacto** (horas, estudantes, evolução); voluntariado corporativo estruturado; contrapartidas de marca |
| **Escola pública** | Não tem braço para reforço individual; dificuldade em acompanhar quem está ficando para trás | Reforço extra sem custo, visão agregada de participação (sem expor dados individuais além do autorizado) |
| **ONG / cursinho popular** | Gestão manual de voluntários, planilhas e relatórios para financiadores | Ferramenta gratuita de agenda, presença e relatórios, e mais visibilidade para captar recursos |

### 3.2 Como cada fonte de receita funciona na prática

| Fonte | Quem paga | Paga pelo quê | Contrapartida | Natureza | Entra na receita-base? |
|---|---|---|---|---|---|
| **Plano de patrocínio** (Semente / Território / Rede) | Empresa (área ESG, instituto empresarial) | Operação de 1 a N núcleos escolares por 12 meses | Painel de impacto, relatórios, marca nas trilhas e certificados, território priorizado por dados | Contrato de serviço, recorrente mensal | **Sim** |
| **Voluntariado corporativo** (add-on) | Empresa | Estruturar e operar a participação de funcionários como monitores | Onboarding, agenda, certificados, métricas de engajamento | Recorrente | **Sim** |
| **Trilha patrocinada** | Empresa de tecnologia/serviços | Co-criar uma trilha de inclusão produtiva (ex.: "Primeiros passos em dados") | Marca na trilha, acesso a talentos que **optam** por compartilhar o perfil (opt-in) | Projeto, pontual | Não (upside) |
| **Editais de fomento / inovação social** | Fundações, institutos, agências | Projeto com escopo e prazo | Prestação de contas e relatórios | Não recorrente, **sem garantia** | **Não** (só capital de ponte) |
| **FIA / FUMCAD via OSC parceira** | Empresas (lucro real) e pessoas físicas destinando parte do IR | Projeto aprovado no conselho municipal (CMDCA) e executado pela OSC parceira | Dedução fiscal ao doador, dentro dos limites da lei | Não recorrente, processo burocrático | **Não** |
| **Investimento de impacto / aceleração** | Aceleradoras, investidores de impacto | Participação ou empréstimo para o crescimento | Retorno financeiro e social | Pontual | **Não** (capital) |

**Estrutura jurídica sugerida [HIPÓTESE]:** começar como **negócio de impacto (Ltda / Simples Nacional)** que vende programas a empresas, em parceria com uma **OSC** que acessa editais e fundos (FIA) restritos a organizações sem fins lucrativos. Detalhes simulados em §3.5 [SIMULAÇÃO GERADA POR IA]; confirmar com contador e advogado antes de formalizar.

### 3.3 Estratégia de precificação

Princípio: **o acesso básico do estudante é sempre gratuito.** O preço é cobrado do patrocinador e calculado por **vagas de estudantes × duração × território × recursos de relatório**.

| | **Semente** | **Território** | **Rede** |
|---|---|---|---|
| Escopo | 1 escola | Até 3 escolas no mesmo território | Até 10 escolas / multi-território |
| Vagas de estudantes | até 100 | até 300 | até 1.000 |
| Preço mensal [HIPÓTESE] | **R$ 2.500** | **R$ 6.000** | **R$ 15.000** |
| Preço por vaga/mês | R$ 25 | R$ 20 | R$ 15 |
| Duração mínima | 12 meses | 12 meses | 12 meses |
| Relatórios | Trimestral (PDF) | Painel mensal + trimestral | Painel em tempo real + relatório anual auditável |
| Priorização territorial por dados | Território indicado | Estudo com dados INEP/IBGE | Estudo + recomendação de expansão |
| Marca | Certificados | Certificados + trilha | Trilha co-criada + evento anual |
| Voluntariado corporativo | Add-on (R$ 1.000/mês) | Add-on (R$ 1.000/mês) | Incluído |

**Lógica do preço [PROJEÇÃO]:** o preço por vaga cai com o volume (economia de escala da equipe fixa). Para o patrocinador, o custo por estudante fica abaixo de uma aula particular avulsa, e ainda inclui medição de impacto. A faixa de R$ 15–25/estudante/mês foi considerada dentro do orçamento de ISP por 2 entrevistados de ESG/instituto (P1, P2, §2.2); **ainda é intenção declarada, sem contrato**, e os preços dos planos seguem como hipótese até a primeira proposta formal (§7.3).

### 3.4 Canais de entrada e aquisição

| Público | Como atrair | Custo de aquisição esperado |
|---|---|---|
| **Estudantes** | Via escola parceira (coordenação apresenta em sala), ONGs e cursinhos populares, grêmio estudantil, link e QR code em grupos de WhatsApp da escola | Baixo: o canal é institucional |
| **Voluntários** | Programas de extensão universitária (horas complementares), FIAP e outras faculdades, voluntariado corporativo dos patrocinadores, LinkedIn | Baixo a médio |
| **Patrocinadores** | Venda consultiva para áreas de ESG/ISP e institutos empresariais; estudo territorial gratuito como isca ("onde seu investimento social rende mais"); eventos de impacto e redes de ISP | Alto: ciclo de 3 a 6 meses |
| **Escolas e ONGs** | Diretoria de ensino e coordenação; ONGs que já atuam no território; proposta "sem custo, com relatório" | Médio: depende de confiança |

**Entrada no mercado:** 1 território piloto escolhido pelo pipeline de Dados (menor IDEB × maior densidade de estudantes) → 1 escola + 1 ONG + 1 patrocinador-âncora → provar métricas em 1 semestre → replicar o modelo de núcleo para territórios vizinhos.

**Expansão:** cada novo núcleo é uma "unidade" replicável (escola + voluntários + patrocinador). A plataforma cresce por território, não por estudante isolado.

### 3.5 Enquadramento fiscal e jurídico [SIMULAÇÃO GERADA POR IA]

> ⚠️ **Aviso: conteúdo gerado por IA e apenas simulado.** Por falta de tempo, o time não consultou contador nem advogado. Esta seção foi gerada com apoio de IA (Claude, Anthropic) a partir da legislação pública citada e **não foi revisada por um profissional**. As alíquotas, os limites e os enquadramentos podem estar desatualizados ou não se aplicar ao caso concreto. Serve para mostrar que o time pensou no tema e para alimentar a simulação financeira, **não é orientação fiscal**. Antes de abrir a empresa ou assinar qualquer contrato, tudo aqui precisa ser validado por contador e advogado.

**1. Duas pessoas jurídicas, papéis diferentes**

| Entidade | Forma | Para quê | Por quê |
|---|---|---|---|
| **Apoio Escolar Periférico Ltda** | Sociedade limitada, optante do **Simples Nacional** | Vende os planos de patrocínio e o voluntariado corporativo (§3.2) | Receita recorrente de serviço; o Simples reduz a carga e a burocracia no início |
| **OSC parceira** (associação já existente no território) | Associação sem fins lucrativos | Recebe editais, doações e recursos de FIA/FUMCAD e executa o projeto social | Esses recursos são, em regra, restritos a organizações sem fins lucrativos (Lei 13.019/2014, o Marco Regulatório das OSCs) |

A Ltda **não recebe doação incentivada**. Ela é paga por um serviço prestado (programa operado + relatório de impacto). A OSC é o veículo dos recursos incentivados, e a Ltda pode prestar serviço de tecnologia a ela por contrato.

**2. Simples Nacional: atividade e alíquota simuladas**

- **Atividade (CNAE) sugerida:** 8550-3/02, *Atividades de apoio à educação*, que em regra é tributada pelo **Anexo III** (serviços). Alternativa: 6311-9/00 (plataformas digitais). Para ela, o anexo depende do **Fator R**.
- **Fator R:** é a folha de pagamento dos últimos 12 meses ÷ a receita dos últimos 12 meses. Se ficar **≥ 28%**, a empresa fica no Anexo III; abaixo disso, vai para o Anexo V, bem mais caro. No cenário intermediário, a folha (coordenação R$ 5.000 + pró-labore R$ 4.000 + coordenador extra R$ 3.500 = R$ 12.500) ÷ receita R$ 30.000 ≈ **42%**, então fica no **Anexo III** em qualquer das duas atividades.
- **Alíquota efetiva** = (receita 12 meses × alíquota nominal − parcela a deduzir) ÷ receita 12 meses. Faixas do Anexo III (LC 123/2006, redação da LC 155/2016):

| Faixa (receita em 12 meses) | Alíquota nominal | Parcela a deduzir |
|---|---|---|
| Até R$ 180 mil | 6,00% | — |
| R$ 180 mil a R$ 360 mil | 11,20% | R$ 9.360 |
| R$ 360 mil a R$ 720 mil | 13,50% | R$ 17.640 |
| R$ 720 mil a R$ 1,8 mi | 16,00% | R$ 35.640 |

| Cenário (§5.2) | Receita anual | Alíquota efetiva simulada | Usada em §5.2 | Efeito no resultado mensal |
|---|---|---|---|---|
| Conservador | R$ 162 mil | **6,0%** | 8% | R$ 270 melhor que o projetado |
| Intermediário | R$ 360 mil | **8,6%** | 8% | R$ 180 pior: o resultado cai de +R$ 1.000 para **+R$ 820** e **continua positivo** |
| Otimista | R$ 666 mil | **10,9%** | 11% | Praticamente igual |

O DAS (guia única do Simples) já inclui IRPJ, CSLL, PIS, Cofins, CPP e **ISS**. A premissa de 8% / 11% da §4.3 continua uma boa aproximação.

**3. Como o patrocinador enxerga o pagamento (argumento de venda)**

| Forma de apoio | Quem pode usar | Benefício fiscal ao patrocinador (simulado) | Base legal |
|---|---|---|---|
| **Contrato de patrocínio com a Ltda** (receita-base) | Qualquer empresa | Em regra, entra como **despesa operacional** quando ligada à atividade (marketing, relacionamento, ESG). **Não é doação**, então não esbarra nos limites abaixo | Regra geral de dedutibilidade de despesas necessárias (RIR/2018). Validar caso a caso |
| **Doação à OSC parceira** | Empresas no **lucro real** | Dedução de até **2% do lucro operacional** | Lei 9.249/1995, art. 13, §2º, III (estendido às OSCs pela Lei 13.019/2014) |
| **FIA/FUMCAD** (projeto da OSC aprovado no CMDCA) | Empresas no **lucro real** | Até **1% do IR devido** | Lei 8.069/1990 (ECA), art. 260 |
| **FIA/FUMCAD** | Pessoas físicas (declaração completa) | Até **6% do IR devido** (somado a outros incentivos), ou até 3% direto na declaração | ECA, arts. 260 e 260-A |

Empresas no **Simples ou no lucro presumido não deduzem** doações nem FIA. Por isso o público-alvo para os recursos incentivados é a empresa média ou grande no lucro real, o mesmo perfil do cliente ESG (§1.4).

**4. Outros pontos jurídicos que o modelo depende**

- **Voluntários:** a **Lei 9.608/1998** (Lei do Voluntariado) exige um **termo de adesão** e garante que não há vínculo empregatício. O cadastro do voluntário no MVP deve incluir esse termo.
- **Dados de menores:** LGPD, art. 14, com consentimento do responsável (já tratado no MVP, ver §1.2, risco R5).
- **Certificado de horas:** a validade como atividade complementar ou de extensão depende de cada universidade. Isso é validado nas entrevistas (roteiro C).

**Próximo passo real:** levar esta seção a um contador (escritórios-modelo de faculdades de Ciências Contábeis costumam atender de graça) e a um advogado do terceiro setor antes de formalizar.

---

## 4. Estrutura de custos

### 4.1 Custos durante a GS [FATO / PROJEÇÃO]
O MVP roda com créditos de estudante na Azure e ferramentas gratuitas. O custo de nuvem exigido pela disciplina de DevOps deve ser **o mesmo número** usado aqui [PREENCHER com a estimativa do PDF de DevOps].

### 4.2 Custos fixos mensais em operação (pós-GS) [PROJEÇÃO]

| Item | Valor/mês | Premissa |
|---|---|---|
| Desenvolvimento e manutenção (1 dev full-stack, PJ) | R$ 7.000 | Manutenção, melhorias, segurança |
| Coordenação pedagógica e de voluntários (1 pessoa) | R$ 5.000 | Curadoria, onboarding de voluntários, suporte a escolas |
| Parcerias e gestão (1 sócio, pró-labore) | R$ 4.000 | Venda B2B, relacionamento com patrocinadores e editais |
| Infraestrutura Azure base (App Service, banco, storage, monitoramento) | R$ 600 | [PREENCHER com a estimativa de DevOps] |
| Ferramentas (domínio, e-mail, RPA, design) | R$ 300 | Usar planos gratuitos/comunitários quando elegíveis |
| Segurança e LGPD (consultoria/DPO terceirizado, backups) | R$ 500 | Dados de menores exigem cuidado redobrado |
| Contabilidade | R$ 500 | Simples Nacional |
| Divulgação e captação (eventos, materiais) | R$ 1.000 | Aquisição de parceiros |
| Jurídico e seguros | R$ 300 | Contratos e termos de consentimento |
| **Total fixo (F)** | **R$ 19.200** | |

### 4.3 Custos variáveis [PROJEÇÃO]

| Item | Valor | Premissa |
|---|---|---|
| IA (tutor) por estudante ativo | R$ 1,50/mês | ~30 perguntas/mês com um modelo de baixo custo |
| Infra escalável por estudante ativo | R$ 0,50/mês | Armazenamento, banda, logs |
| Comunicação (SMS/WhatsApp de lembretes) | R$ 1,00/mês | Lembrete de monitoria reduz faltas |
| Apoio a voluntários (certificados, eventuais deslocamentos) | R$ 1,00/mês | |
| **Variável por estudante ativo (v)** | **R$ 4,00/mês** | |
| Coordenador de território (custo em degrau) | R$ 3.500/mês | +1 a cada 500 estudantes ativos acima dos primeiros 500 |
| Impostos sobre receita (t) | 8% (até ~R$ 360 mil/ano) · 11% (acima) | Alíquota efetiva estimada do Simples Nacional (Anexo III), que varia por faixa. Conferência simulada em §3.5: 6,0% / 8,6% / 10,9% nos três cenários [SIMULAÇÃO GERADA POR IA] |

---

## 5. Simulação financeira

### 5.1 Premissas comuns
- Receita = soma dos planos contratados (preços de §3.3) + add-ons de voluntariado corporativo.
- **Editais, FIA e investimento não entram na receita-base** (não são garantidos); aparecem só como capital de ponte.
- Estudantes ativos = vagas contratadas × taxa de ocupação (70% / 75% / 80%) [HIPÓTESE].
- Custo total = F + v × ativos + coordenadores extras + t × receita.
- Valores **em regime** (mês típico depois que todos os contratos do cenário estão ativos). O ano 1, com rampa, aparece em §5.4.

### 5.2 Os três cenários (mês em regime) [PROJEÇÃO]

| | **Conservador** | **Intermediário** | **Otimista** |
|---|---|---|---|
| Contratos | 3 Semente + 1 Território | 4 Semente + 3 Território | 5 Semente + 4 Território + 1 Rede |
| Empresas patrocinadoras (contratos) | 4 | 7 | 10 |
| Vagas contratadas | 600 | 1.300 | 2.700 |
| Ocupação | 70% | 75% | 80% |
| **Estudantes ativos** | **420** | **975** | **2.160** |
| Receita de planos | R$ 13.500 | R$ 28.000 | R$ 51.500 |
| Add-on voluntariado corporativo | — | 2 × R$ 1.000 = R$ 2.000 | 4 × R$ 1.000 = R$ 4.000 |
| **Receita mensal** | **R$ 13.500** | **R$ 30.000** | **R$ 55.500** |
| **Receita anual (×12)** | **R$ 162.000** | **R$ 360.000** | **R$ 666.000** |
| Custo fixo (F) | R$ 19.200 | R$ 19.200 | R$ 19.200 |
| Variável (v × ativos) | 420 × 4 = R$ 1.680 | 975 × 4 = R$ 3.900 | 2.160 × 4 = R$ 8.640 |
| Coordenadores extras | 0 | 1 × 3.500 = R$ 3.500 | 4 × 3.500 = R$ 14.000 |
| Impostos | 8% = R$ 1.080 | 8% = R$ 2.400 | 11% = R$ 6.105 |
| **Custo operacional mensal** | **R$ 21.960** | **R$ 29.000** | **R$ 47.945** |
| **Custo operacional anual** | **R$ 263.520** | **R$ 348.000** | **R$ 575.340** |
| **Resultado mensal** | **−R$ 8.460** | **+R$ 1.000** | **+R$ 7.555** |
| **Resultado anual** | **−R$ 101.520** | **+R$ 12.000** | **+R$ 90.660** |
| Margem | −63% | +3% | +14% |
| **Custo por estudante ativo/mês** | R$ 52,29 | R$ 29,74 | R$ 22,20 |

**Como os coordenadores extras foram calculados:** ⌈ativos ÷ 500⌉ − 1. Conservador: ⌈420/500⌉ − 1 = 0. Intermediário: ⌈975/500⌉ − 1 = 1. Otimista: ⌈2.160/500⌉ − 1 = 4.

### 5.3 Ponto de equilíbrio

Condição: **Receita × (1 − t) ≥ F + coordenadores extras + v × ativos**

Para o mix do cenário intermediário (975 ativos, 1 coordenador extra):
R ≥ (19.200 + 3.500 + 975 × 4) ÷ (1 − 0,08) = 26.600 ÷ 0,92 = **≈ R$ 28.900/mês de receita recorrente**

Em termos práticos: **cerca de 7 contratos (4 Semente + 3 Território) ou ~1.000 estudantes ativos.** O cenário conservador fica abaixo desse ponto e precisa de edital ou capital de ponte para cobrir um déficit de ≈ R$ 8,5 mil/mês.

**Leitura para a banca:** a sustentabilidade vem da **escala por território**. O custo por estudante cai de R$ 52 para R$ 22 quando a operação passa de 420 para 2.160 estudantes, porque a equipe fixa se dilui.

### 5.4 Ano 1 com rampa (capital de ponte necessário) [PROJEÇÃO]
Premissa: contratos assinados de forma linear ao longo de 12 meses. A receita acumulada no ano ≈ 6,5 × receita em regime. Custos fixos começam no mês 1.

| | Conservador | Intermediário | Otimista |
|---|---|---|---|
| Receita ano 1 (6,5 × mensal) | R$ 87.750 | R$ 195.000 | R$ 360.750 |
| Variáveis + coord. + impostos (6,5 × mensal) | R$ 17.940 | R$ 63.700 | R$ 186.843 |
| Fixos (12 × R$ 19.200) | R$ 230.400 | R$ 230.400 | R$ 230.400 |
| **Resultado ano 1** | **−R$ 160.590** | **−R$ 99.100** | **−R$ 56.493** |

**Conclusão honesta:** mesmo no cenário otimista, o ano 1 precisa de **R$ 60–160 mil de capital de ponte** (editais, aceleração ou investimento de impacto). Nos cenários intermediário e otimista, o negócio passa a cobrir a própria operação **a partir do ano 2**. Isso é o "pedido" do bloco 6 do pitch.

### 5.5 Sensibilidade (o que mais move o resultado)
| Variável | Efeito no intermediário |
|---|---|
| Perder 1 contrato Território (−R$ 6.000) | Resultado vai para ≈ −R$ 3.620/mês (receita 24.000; 750 ativos) |
| Ocupação cai de 75% para 60% | Receita igual (preço por plano), variável cai: resultado melhora um pouco, **mas o impacto entregue cai**, e a renovação fica em risco |
| Custo de IA dobra (R$ 3/estudante) | −R$ 1.460/mês: tutor precisa de limite de uso |
| Renovação de patrocínios < 70% | Sem novos contratos, a operação volta ao déficit no ano seguinte: **renovação é a métrica crítica** |

---

## 6. KPIs de negócio e impacto

Classificação: **A** = atividade (o que fazemos) · **R** = resultado (o que muda no curto prazo) · **I** = impacto de longo prazo.

> Todas as metas são **sugeridas** para o primeiro ano de piloto. **Nenhum valor foi alcançado ainda.**

### 6.1 Indicadores de negócio

| Indicador | Tipo | Objetivo | Cálculo | Periodicidade | Meta sugerida | Relevância / uso com o patrocinador |
|---|---|---|---|---|---|---|
| Estudantes cadastrados | A | Medir alcance | Contagem acumulada de cadastros confirmados | Mensal | ≥ 130% das vagas contratadas | Mostra demanda no território financiado |
| Estudantes ativos mensais (EAM) | R | Medir uso real | Estudantes com ≥ 1 monitoria **ou** ≥ 1 atividade de trilha no mês | Mensal | ≥ 75% das vagas | **Base do preço**: o patrocinador vê quantos usaram de fato |
| Retenção M1→M3 | R | Saber se o estudante volta | Ativos no mês 3 ÷ ativos no mês 1 da mesma coorte | Mensal por coorte | ≥ 50% | Indica valor percebido pelo estudante |
| Conclusão de trilhas | R | Medir entrega de conteúdo | Trilhas concluídas ÷ trilhas iniciadas | Mensal | ≥ 35% | Base do certificado; marca do patrocinador na trilha |
| Voluntários ativos | A | Garantir oferta | Voluntários com ≥ 1 monitoria no mês | Mensal | ≥ 1 voluntário para cada 15 estudantes ativos | Sem oferta, não há serviço |
| Permanência de voluntários | R | Reduzir rotatividade | Voluntários ativos há ≥ 3 meses ÷ voluntários ativos | Trimestral | ≥ 60% | Mostra engajamento (inclusive dos funcionários do patrocinador) |
| Empresas parceiras | A | Diversificar receita | Contratos ativos | Mensal | 7 no fim do ano 1 (cenário intermediário) | Concentração de receita = risco |
| Renovação de patrocínios | R | Garantir continuidade | Contratos renovados ÷ contratos vencidos | Anual | ≥ 70% | **Métrica crítica da sustentabilidade** (§5.5) |
| Custo por estudante ativo | R | Eficiência | Custo operacional mensal ÷ EAM | Mensal | ≤ R$ 30 (intermediário) | Transparência no uso do recurso |
| Receita recorrente contratada (MRR) e meses de caixa | R | Previsibilidade | Soma dos contratos ativos; caixa ÷ queima mensal | Mensal | MRR ≥ R$ 28,9 mil (equilíbrio); ≥ 6 meses de caixa | Mostra que o programa não para no meio |

### 6.2 Indicadores de impacto social

| Indicador | Tipo | Objetivo | Cálculo | Periodicidade | Meta sugerida | Relevância / uso com o patrocinador |
|---|---|---|---|---|---|---|
| Monitorias realizadas | A | Medir entrega | Sessões com presença confirmada de estudante e monitor | Semanal/Mensal | ≥ 2 por estudante ativo/mês | Número principal do relatório de impacto |
| Horas de reforço entregues | A | Dimensionar o serviço | Σ duração das monitorias realizadas | Mensal | ≥ 1,5 h por estudante ativo/mês | Fácil de comunicar ("X horas de aula doadas") |
| Taxa de presença | R | Qualidade operacional | Monitorias realizadas ÷ agendadas | Semanal | ≥ 80% | Faltas desperdiçam voluntários; lembretes automáticos atacam isso |
| Evolução no diagnóstico (pré/pós) | R | Medir aprendizagem | (acertos no diagnóstico final − inicial) ÷ inicial, no mesmo conteúdo, dentro da plataforma | Por ciclo (bimestral) | +20% de acertos médios | **Métrica antes/depois** que a rubrica pede. Não é prova causal |
| Aprovação dos acompanhados | I | Efeito escolar | Aprovados ÷ acompanhados, com dado informado **pela escola parceira** sob convênio e consentimento | Anual | Aprovação acima da média da própria escola (linha de base: ~78% nas séries atendidas no último ano, informada pela escola C1 de forma agregada) | Depende de convênio; só agregado, nunca individual |
| Acesso a trilhas de inclusão digital | A/R | Inclusão produtiva | Estudantes que iniciaram ÷ estudantes ativos | Mensal | ≥ 40% | Conecta com ODS 4.4 |
| Estudantes de territórios vulneráveis | A | Foco no público certo | Estudantes cujo endereço (extraído por Visão) está em território priorizado ÷ total | Mensal | ≥ 80% | Prova que o recurso chegou a quem precisa (ODS 10) |
| Oportunidades educacionais disponibilizadas | A | Medir oferta | Vagas de monitoria + trilhas + materiais publicados | Mensal | Crescente | Mostra a capacidade da rede |
| Continuidade nos estudos | I | Longo prazo | % de egressos do Ensino Médio matriculados em ensino técnico/superior (pesquisa opt-in) | Anual | Linha de base no ano 1 | Impacto de longo prazo; requer acompanhamento |

### 6.3 Como os KPIs viram argumento de venda
O **relatório de impacto** do patrocinador (gerado automaticamente pelo RPA, ver §10) traz: EAM, monitorias, horas, presença, evolução pré/pós, % em territórios vulneráveis e custo por estudante. Cada número tem a fórmula ao lado. Isso é a "prova" que a área de ESG precisa para o relatório de sustentabilidade dela.

---

## 7. Estratégia de parcerias e posicionamento

### 7.1 Posicionamento
**Para empresas que precisam de impacto social comprovado, o Apoio Escolar Periférico é o programa de reforço escolar que escolhe o território com dados, entrega monitoria real a estudantes da periferia e mede o resultado mês a mês.**

Diferenciais que devemos destacar: (1) território escolhido por dados públicos; (2) pessoa real como monitor, com IA de apoio; (3) impacto medido e reportado automaticamente; (4) gratuito e acessível para o estudante.

### 7.2 Estratégia ESG
- **Conexão:** o programa entra no pilar "S" (Social) e no investimento social privado da empresa; mapeia em ODS 4 e ODS 10.
- **Relatório:** painel mensal + relatório trimestral com metodologia explícita (fórmulas da §6). O formato deve ser fácil de colar no relatório de sustentabilidade do patrocinador [HIPÓTESE: validar o formato com 1 área de ESG].
- **Médio e longo prazo:** contratos de 12 meses com renovação; o segundo ano oferece expansão de território com base nos dados do primeiro.

### 7.3 Proposta comercial (estrutura de 1 página)
1. O problema no território X (dados INEP/IBGE do pipeline).
2. O programa: núcleo, número de estudantes, duração.
3. O que a empresa recebe: painel, relatórios, marca, voluntariado.
4. **Uso do recurso** (transparência), a partir dos custos de §4: ~42% coordenação pedagógica, de território e parcerias · ~35% tecnologia, IA e segurança · ~10% comunicação e apoio a voluntários · ~10% impostos e administração · ~3% reserva [PROJEÇÃO sobre a receita do cenário intermediário, R$ 30 mil].
5. Metas do ano (KPIs §6) e quando serão reportadas.
6. Preço e prazo.

### 7.4 Alternativas existentes e diferenciação
> Só cito tipos de alternativa e exemplos públicos conhecidos. Antes de colocar nomes no PDF, **conferir o modelo atual de cada um no site oficial**. Nenhuma parceria com essas organizações existe.

| Alternativa | Como funciona | Limitação para o nosso cidadão | Onde nos diferenciamos |
|---|---|---|---|
| Aula particular / reforço pago | Professor cobra por hora | Custo inviável para a maioria das famílias da periferia | Gratuito para o estudante |
| Plataformas de conteúdo gratuito (ex.: Khan Academy em português) | Vídeos e exercícios autodirigidos | Sem pessoa acompanhando; exige autonomia | Monitor real + agendamento |
| Plataformas de vestibular pagas/freemium (ex.: Descomplica, Me Salva!) | Assinatura | Pagas e focadas em vestibular | Gratuito, Fundamental II e EM, inclusão produtiva |
| Cursinhos populares e ONGs (ex.: Rede Emancipa, Educafro) | Aulas presenciais com voluntários | Vagas limitadas, gestão manual | **Parceiros, não concorrentes:** damos ferramenta e relatório |
| Recuperação / reforço da própria escola | Professor da rede | Turma grande, tempo limitado | Complementar, com atendimento individual |

**Limitações nossas (assumidas):** dependemos de voluntários; ainda não temos piloto nem marca; ciclo de venda B2B longo; não substituímos a escola.

**Por que uma empresa apoiaria:** custo por estudante transparente, território escolhido por dados, relatório pronto e funcionários engajados como monitores.

---

## 8. Roteiro do vídeo-pitch (5:00)

O roteiro completo, com falas, elenco, tempos, telas e transições, está em um arquivo separado para enviar ao grupo:
**[Roteiro_Video_Pitch.md](Roteiro_Video_Pitch.md)**

| Bloco | Quem fala (sugestão) | Tempo |
|---|---|---|
| 1. Problema e cidadão | Edson Leonardo | 0:00–0:45 |
| 2. Solução e proposta de valor | Jó Sales | 0:45–1:30 |
| 3. Demonstração do MVP | Miguel Garcez de Carvalho | 1:30–3:00 |
| 4. Modelo de negócio e Lean Canvas | Eduardo Mazelli | 3:00–4:00 |
| 5. Impacto e ODS | Vinicius Souza e Silva | 4:00–4:30 |
| 6. Time e próximos passos | Vinicius Souza e Silva | 4:30–5:00 |

---

## 9. Plano de gravação e demonstração do MVP

A sequência de cenas, as dicas de gravação e o checklist de publicação estão no [roteiro](Roteiro_Video_Pitch.md#plano-de-gravação).

### 9.1 Fluxo central a congelar até a gravação
1. Abrir URL pública → 2. cadastro → 3. busca de monitoria por matéria → 4. agendamento confirmado → 5. (opcional) tutor de IA → 6. relatório de impacto gerado.
O **mínimo** para a nota de demo é 1→4 funcionando de verdade. Os passos 5 e 6 só entram se estiverem no ar.

### 9.2 Evidência de valor (rubrica: 3,5 pontos) — teste de usabilidade em 2 dias
Esta é a ação de maior retorno até 19/11.
1. **Quem:** 5 a 8 pessoas do público (estudantes de escola pública, ou irmãos e conhecidos na faixa etária, com consentimento do responsável se forem menores) e 2 a 3 voluntários.
2. **Tarefa:** "Agende uma monitoria de matemática para esta semana."
3. **Medir:** taxa de sucesso sem ajuda; tempo até a confirmação; nº de erros; nota de facilidade (1–5); 1 frase espontânea.
4. **Antes/depois:** pergunte "como você conseguiria esse reforço hoje, e quanto tempo levaria?" e compare com o tempo medido na plataforma.
5. **Documentar:** planilha + prints (sem rostos/dados pessoais) num anexo do PDF. **Usar no pitch apenas os números reais obtidos.**

**Resultado (14/11/2026, 5 estudantes de escola pública, E1–E5):** 5 de 5 agendaram uma monitoria **sozinhos** no MVP; tempo até a confirmação entre **55 s e 1m45s** (média ≈ 1m14s). Único ponto de atrito: E1 hesitou na escolha das tags de matéria. Sugestões: manter a plataforma leve para celular compartilhado e internet instável (E4). Antes/depois: hoje, 4 dos 5 nunca conseguiram reforço e 1 procurou cursinho popular sem vaga. Detalhes na [planilha de validação](Roteiro_Entrevistas_Validacao.md#6-planilha-de-registro-consolidada). Ainda faltam a nota de facilidade (1–5) e o teste com voluntários na tela de horários.

---

## 10. Integração entre Business e as demais disciplinas

| Disciplina | O que o PDF oficial exige [FATO] | Ideia original do time | Divergência? | Integração coerente proposta | Contribuição para o negócio |
|---|---|---|---|---|---|
| **Dados** (Ana Machado) | Pipeline orquestrado (Airflow) ETL/ELT que alimenta o MVP; diagrama e dicionário de dados | Indicadores educacionais para priorizar regiões | **Não** | DAG que ingere IDEB/Censo Escolar (INEP) + dados IBGE e gera tabela de "prioridade territorial", consumida pelo MVP e pelo painel de impacto | Escolha do território piloto; argumento de venda ("onde o investimento rende mais"); KPI de % em territórios vulneráveis |
| **IA Generativa** (Reinaldo Ramos) | Enunciado enviado pelo professor: aplicação que integra um LLM via API (ex.: OpenRouter) com escolha e configuração do modelo; engenharia de prompts com contexto; **saída estruturada (JSON)** e tratamento de falhas; README com problema, arquitetura, exemplos de prompts/saídas, limitações e ética; evidências de execução. Sugestão do professor: um *helper* que tira dúvidas sobre o software da equipe | Tutor virtual | **Parcial**: a sugestão é um assistente sobre o uso do software, não um tutor de matérias | **Assistente da plataforma**: responde, em linguagem simples, dúvidas sobre como se cadastrar, agendar, cancelar, privacidade e erros comuns, usando a documentação do MVP como contexto. Devolve JSON (`resposta`, `categoria`, `encaminhar_humano`). Dúvida de matéria → orienta a agendar com um monitor ("pessoa no circuito", slide 21) | Menos suporte manual para coordenação e voluntários; custo variável de §4.3 |
| **Visão Computacional** (Wilians Souza) | Extração automática de **endereço** em fotos de faturas de 3 empresas (ex.: Enel, Sabesp, Claro), com confirmação pelo usuário; documentos sintéticos | "Processamento de documentos no cadastro" | **Parcial**: o escopo é especificamente endereço em contas de consumo | Usar a extração no **cadastro do estudante** (comprovante de residência) → endereço alimenta a verificação de território prioritário | Cadastro mais rápido; comprova que o recurso chega ao território financiado |
| **RPA** (Cibele Ribeiro) | Analisar gargalo, decidir RPA vs. API, BPM As-Is/To-Be, robô UiPath integrado ao MVP, vídeo de até 3 min | Automatizar processos administrativos | **Não** | Processo sugerido: **consolidação de presenças + geração e envio do relatório de impacto ao patrocinador + emissão de certificados de voluntários**, que hoje seria manual (planilhas de ONG/escola sem API). Justificar no assessment se é RPA ou API | Reduz custo de operação (coordenação); é a "entrega" que o patrocinador paga para receber |
| **DevOps & Cloud** (Gabriel Arcanjo) | Azure App Service, HTTPS, GitHub Actions, segredos fora do código, acesso por papel, monitoramento com alerta, **estimativa de custo** | Disponibilidade, segurança, escalabilidade | **Não** | Papéis: estudante, voluntário, coordenação, patrocinador (painel). **Usar a mesma estimativa de custo de nuvem em §4.2** | Confiabilidade para patrocinadores; LGPD; custo de infra do modelo financeiro |
| **Maker Lab** (Caio Sousa) | Redesign de um **objeto real do espaço público** que funciona mal (ex.: botão do semáforo, bebedouro, corrimão, assento do ponto); CAD, laser + 3D, publicação no MakerWorld | "Solução física integrada à plataforma" | **Sim**: o escopo é redesign de mobiliário urbano, não um dispositivo da plataforma | Escolher um objeto **do trajeto do estudante até a escola**, por exemplo o assento ou abrigo do ponto de ônibus em frente a uma escola pública, ou o bebedouro do pátio, e incluir uma placa com QR code para a plataforma | Conecta a CitizenTech física ao mesmo cidadão; canal de aquisição local (QR code); reforça a narrativa de território |

> **Não afirmar no pitch ou no PDF** que alguma dessas integrações foi feita até que esteja no repositório e funcionando.

### 10.1 Ficha Técnica do MVP
A ficha (slide 20) está em um arquivo separado, pronta para abrir o README do repositório principal:
**[FICHA_TECNICA_MVP.md](../FICHA_TECNICA_MVP.md)**

---

## 11. Checklist final de conformidade com a rubrica

| # | Item | Critério / fonte | Status |
|---|---|---|---|
| 1 | Lean Canvas com os 9 blocos coerentes | Lean Canvas 2,0 | ✅ §2 |
| 2 | Status "validado vs. hipótese" + "o que mudou" preenchidos com evidências reais | Lean Canvas 2,0 | ✅ §2.2 (10 entrevistas, [planilha](Roteiro_Entrevistas_Validacao.md)) |
| 3 | Proposta de valor por participante | Modelo 2,5 | ✅ §3.1 |
| 4 | Fontes de receita, preço e canais de entrada | Modelo 2,5 | ✅ §3.2–3.4 |
| 5 | Métricas-chave + "a conta fecha" (equilíbrio e capital de ponte) | Modelo 2,5 | ✅ §5, §6 |
| 6 | Custo de nuvem igual ao do PDF de DevOps | Coerência | ⬜ |
| 6b | Enquadramento fiscal e jurídico, com aviso de "gerado por IA / simulado" | Modelo 2,5 | ✅ §3.5 (sem revisão de contador) |
| 7 | Pitch com começo, meio e fim, ≤ 5:00, **5 integrantes falando** | Narrativa 2,5 | ✅ [roteiro](Roteiro_Video_Pitch.md) · ⬜ gravar e cronometrar |
| 8 | Dado do problema verificado com fonte (bloco 1) | Narrativa | ⬜ |
| 9 | Demo **na URL pública**, fluxo do primeiro clique ao resultado, sem telas falsas | Demo 3,5 | ⬜ depende do MVP |
| 10 | Falas da demo ajustadas ao que existe | Demo 3,5 | ⬜ |
| 11 | Evidência: teste documentado ou métrica antes/depois | Valor 3,5 | 🟡 §9.2: teste com 5 estudantes documentado · ⬜ anexar planilha e prints ao PDF |
| 12 | ODS identificados e contribuição explicada | Slide 14 (obrigatório) | ✅ roteiro bloco 5, ficha técnica |
| 13 | LGPD e acessibilidade mencionadas (menores, consentimento, legendas) | Slide 21 | ✅ §1.2, ficha técnica, roteiro |
| 14 | Ficha Técnica do MVP no README | Entregável | 🟡 [ficha criada](../FICHA_TECNICA_MVP.md) · ⬜ preencher URL/repo e colocar no README |
| 15 | **PDF único** com Lean Canvas + modelo + links clicáveis (vídeo, MVP, repo) | Formato | ⬜ |
| 16 | Links públicos funcionando durante a correção (até 1 semana após 19/11) | Regras da GS | ⬜ |
| 17 | Envio por **um** integrante no portal até 19/11, 23h55 | Regras da GS | ⬜ envio de Business: Eduardo Mazelli |

---

### Fontes e observações
- PDF oficial: *Desafio FIAP — GS CitizenTech 4ESPR (Preenchido v3)*, slides 3–34 e páginas das disciplinas.
- Vídeo da equipe (Google Drive): **não foi acessado** (conector sem autenticação). Este roteiro não presume nada sobre o que foi apresentado nele.
- Dados educacionais sugeridos: INEP (IDEB, SAEB, Censo Escolar), QEdu, IBGE. Inserir números apenas depois de conferidos.
- Regras fiscais citadas (Simples Nacional, FIA/FUMCAD, doações a OSC): por falta de tempo, foram **geradas por IA e apenas simuladas** (§3.5), sem revisão de contador. O aviso precisa aparecer no PDF final.

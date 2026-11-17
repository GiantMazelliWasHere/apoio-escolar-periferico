# Roteiro da entrega de Maker Lab (prazo: quinta, 19/11, 23h55)

Responsável: Vinicius Souza e Silva. Tudo o que dá para preparar sem a peça física já está pronto nesta pasta; falta o que só quem tem o protótipo e a conta consegue fazer.

| # | Passo | Quem | Pronto? |
|---|---|---|---|
| 0 | Fotografar o protótipo montado | Vinicius | ⬜ |
| 1 | Publicar no MakerWorld | Vinicius | ⬜ textos prontos abaixo |
| 2 | Pasta de arquivos com link público | Equipe | 🟡 arquivos organizados em `maker/`; falta liberar o acesso |
| 3 | PDF único no portal | Vinicius | 🟡 gerado por script; falta preencher os links e as fotos |

---

## 0. Fotos do protótipo (antes de tudo)

- 4 a 6 fotos, em boa luz, fundo liso: frente com um tablet ou celular apoiado, perfil (mostra a inclinação), as duas placas separadas, detalhe da etiqueta QR e alguém usando o suporte com o caderno ao lado.
- Salve os originais em alta qualidade em `maker/imagens/fotos/` com nomes que definem a ordem: `01_frente.jpg`, `02_perfil.jpg`, `03_pecas.jpg`, `04_qr.jpg`…
- A etiqueta QR do protótipo pode ser provisória. Quando o MVP for publicado, gerem a definitiva em `/maker` (o QR depende da URL pública).

## 1. MakerWorld (1,5 pt)

1. Entre em https://makerworld.com com a sua conta → **Upload** → **Upload Model**.
2. **Arquivos** (pasta `maker/fabricacao/`):
   - `suporte_tablet_impressao3d.3mf` (as duas placas)
   - `suporte_tablet_placa_frente.stl` e `suporte_tablet_apoio_traseiro.stl` (já deitados na mesa, gerados a partir do 3MF)
   - `apoio_traseiro_corte_laser.dxf` (se o site não aceitar `.dxf` como arquivo de modelo, anexe em **Other files / Attachments**)
3. **Fotos:** as fotos reais do passo 0 primeiro; os renders de `maker/imagens/` depois.
4. **Título, descrição e lista de materiais:** copie os blocos abaixo.
5. **Licença:** CC BY (ou a que o professor pedir).
6. **Crédito (bônus):** se usaram alguma peça baixada, cole o link dela em **Remix / Credits**.
7. Publique como **público** e copie o link (algo como `https://makerworld.com/pt/models/123456`).

### Título
```
Suporte de tablet para estudo com QR code | Apoio Escolar Periférico
```

### Descrição
```
O problema
Estudantes de escolas públicas da periferia fazem monitoria online pelo celular ou por um tablet emprestado. Sem apoio, seguram o aparelho com uma mão ou o encostam em pilhas de livros, e ficam sem as mãos livres para escrever no caderno, que é justamente o que a monitoria pede.

A solução
Um suporte de mesa simples e barato, feito de duas placas planas de 220 x 140 mm: a placa da frente tem uma aba na base que segura o tablet ou o celular inclinado, e o apoio traseiro dá a inclinação. Na placa da frente vai uma etiqueta com QR code que leva direto para a plataforma de monitorias gratuitas Apoio Escolar Periférico, onde o estudante se cadastra e agenda com um monitor voluntário. Cada cadastro feito pelo QR aparece no painel de impacto da plataforma.

Projeto da Global Solution FIAP 2026.2 (CitizenTech), disciplina Project-Based Maker Lab, Engenharia de Software, turma 4ESPR.

Arquivos
- suporte_tablet_impressao3d.3mf: as duas placas, para impressão 3D
- suporte_tablet_placa_frente.stl / suporte_tablet_apoio_traseiro.stl: as placas separadas, já deitadas na mesa
- apoio_traseiro_corte_laser.dxf: apoio traseiro para corte a laser em chapa de 3 mm

Impressão
PLA, 0,2 mm de camada, 3 perímetros, 15% de preenchimento, sem suporte (as placas já estão deitadas). Cabe em mesa de 220 x 220 mm.
```

### Lista de materiais
```
- Placa da frente: impressão 3D em PLA (220 x 140 mm, 3 mm, aba de 27 mm)
- Apoio traseiro: chapa de MDF ou acrílico de 3 mm em corte a laser (220 x 140 mm), ou impressão 3D em PLA
- Etiqueta QR code de 40 x 40 mm em papel adesivo (ou gravada a laser na placa da frente)
- Montagem: [COMPLETAR: cola / encaixe / fita dupla face]
- Parafusos: nenhum
```

> Ajustem os parâmetros de impressão e a montagem ao que vocês realmente usaram no protótipo.

## 2. Pasta de arquivos com link público

Os arquivos já estão organizados no repositório, em `maker/`:

```
maker/
├── cad/          suporte_tablet.f3d · .step · .fbx
├── fabricacao/   .3mf · 2 × .stl · .dxf
├── imagens/      renders + fotos/ (alta qualidade)
└── entrega/      script do PDF, PDF gerado e este roteiro
```

**Atenção: o repositório do GitHub está privado.** O professor não consegue abrir o link assim. Escolham uma das opções:

- **A. Tornar o repositório público** (recomendado, porque o PDF de Business e a Ficha Técnica também apontam para ele): GitHub → Settings → General → Danger Zone → Change visibility → Public. Antes, confiram que nenhum `.env` ou chave foi commitado. O link fica `https://github.com/GiantMazelliWasHere/apoio-escolar-periferico/tree/main/maker` (depois do merge na `main`).
- **B. Pasta no Google Drive:** criar a pasta "Maker Lab - Suporte de tablet", subir o conteúdo de `maker/cad`, `maker/fabricacao` e `maker/imagens` mantendo as subpastas, depois Compartilhar → Acesso geral → **Qualquer pessoa com o link** (Leitor) → Copiar link. Colar esse link em `LINKS` no script.

Testem o link numa janela anônima antes de enviar.

## 3. PDF único

O script monta o PDF nesta ordem: capa e identificação (disciplina, título, integrantes) → **links clicáveis em destaque** (MakerWorld e pasta) → problema → solução → lista de materiais → fabricação → fotos do protótipo → integração com a plataforma → arquivos.

1. Abra `maker/entrega/gerar_entrega.py` e preencha no topo:
   - `LINKS["Publicação no MakerWorld"]` = link do passo 1
   - `LINKS["Pasta do repositório (arquivos brutos)"]` = link do passo 2 (já vem com o do GitHub)
   - `MONTAGEM` = como as placas se unem
   - `CREDITO_BONUS` = link da peça baixada, ou `"não se aplica"`
2. Coloque as fotos em `maker/imagens/fotos/`.
3. Rode o script (só precisa do Python e do Edge):

```bash
python maker/entrega/gerar_entrega.py
```

4. Abra `maker/entrega/Entrega_MakerLab_Suporte_Tablet.pdf`: **nada pode estar em amarelo**. O script avisa no final o que ainda falta.
5. Clique nos dois links dentro do PDF para testar.
6. Envie no portal até **19/11 às 23h55**.

> Se o enunciado completo listar mais itens depois dos links (o trecho que temos para na seção de links), avisem que o script é ajustado na ordem pedida.

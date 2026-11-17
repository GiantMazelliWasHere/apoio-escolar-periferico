# Roteiro da entrega de Maker Lab: rev. C (prazo: quinta, 19/11, 23h55)

Responsável: Vinicius Souza e Silva. Peça: **suporte de tablet 3DP-2026-004 rev. C**, uma peça única de chapa dobrada impressa em 3D. Tudo o que dá para preparar sem a peça física e sem a conta já está pronto nesta pasta.

| # | Passo | Quem | Tempo | Pronto? |
|---|---|---|---|---|
| 0 | Imprimir e fotografar o protótipo | Vinicius | — | ✅ 6 fotos da impressão + peça pronta (`07_peca_pronta.jpg`); foto com tablet e QR é opcional |
| 1 | Anotar os dados reais da impressão | Vinicius | 5 min | ✅ PETG, Creality Ender 3, 5 h, 90 g |
| 2 | Publicar no MakerWorld (1,5 pt) | Vinicius | 20 min | ✅ [publicado](https://makerworld.com/en/models/3634500-tablet-stand-for-studying-with-qr-code) |
| 3 | Pasta de arquivos com link público | Equipe | — | ✅ repositório público, `maker/` organizada |
| 4 | PDF único no portal | Vinicius | 10 min | 🟡 gerado com fotos, modelo e link do MakerWorld; falta só o crédito do bônus |

---

## 0. Protótipo e fotos

A impressão já está fotografada (Creality, mesa de 220 × 220 mm, perfil deitado, com brim), e as 6 fotos estão em `maker/imagens/fotos/`. Já entram no PDF e no MakerWorld.

Falta **uma ou duas fotos da peça pronta**, que valem mais que as da impressão, principalmente para a capa do MakerWorld:

- ✅ `07_peca_pronta.jpg`: a peça fora da mesa, sem o brim
- (opcional) `08_com_tablet.jpg`: com um tablet ou celular apoiado, de frente
- (opcional) `09_qr.jpg`: a etiqueta QR definitiva de 30 mm (`maker/fabricacao/etiqueta_qr_30mm.svg`), colada no canto inferior da face de trás da perna traseira

Salvem em `maker/imagens/fotos/` com esses nomes e adicionem a legenda em `LEGENDAS` no topo de `gerar_entrega.py`. Sem legenda, a foto sai com uma genérica.

> A etiqueta definitiva já está pronta: `maker/fabricacao/etiqueta_qr_30mm.svg`, gerada no MVP publicado e apontando para `https://app-apoioescolar-mvp-6e7462.azurewebsites.net/qr`. Imprima em 100% (sem "ajustar à página") em papel adesivo e confira com a câmera do celular antes de colar.

## 1. Dados reais da impressão

✅ Já preenchido: **PETG, Creality Ender 3, 5 horas, 90 g**. Está em `IMPRESSAO` no PDF e na descrição do MakerWorld abaixo.

Os parâmetros recomendados, para quem for imprimir de novo:

| Campo | Valor |
|---|---|
| Orientação | A dos arquivos: perfil deitado, 110 mm na altura. **Não gire a peça** |
| Altura de camada | 0,20 mm |
| Paredes (perímetros) | 5 (a chapa de 2 mm sai maciça) |
| Suporte | **Desligado** |
| Adesão | **Brim**, 5 mm (a base é só o contorno fino da chapa) |

> **Sobre o perfil de impressão do MakerWorld:** o "perfil de impressão" (3MF fatiado com botão Print) é pensado para as impressoras Bambu Lab e pede prova de impressão naquela máquina. Sem uma Bambu, o caminho é publicar o **modelo bruto** (3MF/STL/STEP) **com fotos da impressão real**, o que o site aceita e o que estas fotos cobrem. Se alguém do grupo tiver acesso a uma Bambu, dá para acrescentar o perfil depois pelo Bambu Studio (**Publicar**), sem refazer a publicação.

## 2. MakerWorld (1,5 pt)

1. https://makerworld.com → entrar → **Upload** → envie como **modelo bruto / Raw model files** (sem perfil de impressão).
2. **Arquivos do modelo** (pasta `maker/`):
   - `fabricacao/suporte_tablet_3DP-2026-004_revC_impressao.3mf` e `.stl`
   - `cad/suporte_tablet_3DP-2026-004_revC.step`
   - `cad/..._desenho_tecnico.pdf` e `..._desenho_2d.dxf`: se o site não aceitar como arquivo de modelo, use **Outros arquivos / Attachments**
3. **Imagens:** primeiro as fotos reais (`imagens/fotos/`; capa = `07_peca_pronta.jpg`, senão `01_perfil_na_mesa.jpg`), depois as capturas do CAD (`imagens/modelo/01_cad_perspectiva.jpg`, `02_cad_frontal.jpg`) e os renders. O site remove publicações sem foto de impressão real, então as fotos são obrigatórias.
4. **Título, descrição, categoria e tags:** copie os blocos abaixo.
5. **Lista de materiais (BOM):** bloco abaixo.
6. **Licença:** CC BY (ou a que o professor pedir).
7. **Remix / crédito (bônus):** se partiram de alguma peça baixada, marque como **Remix** e cole o link original.
8. Publique como **público**, abra o link numa janela anônima e copie a URL (algo como `https://makerworld.com/pt/models/123456`).

### Título
```
Suporte de tablet para estudo com QR code | Apoio Escolar Periférico
```

### Categoria e tags
```
Categoria (sugestão; use a mais próxima que o site oferecer): Casa / Escritório → Suportes
Tags: tablet stand, suporte tablet, phone stand, education, estudo, no supports, QR code
```

### Descrição
```
O problema
Estudantes de escolas públicas da periferia fazem monitoria online pelo celular ou por um tablet emprestado. Sem apoio, seguram o aparelho com uma mão ou o encostam em pilhas de livros, e ficam sem as mãos livres para escrever no caderno, que é justamente o que a monitoria pede.

A solução
Um suporte de mesa feito de uma única chapa dobrada de 2 mm, impresso de uma vez, sem montagem, cola ou parafusos.
- Painel de leitura a 65° e perna traseira a 80° para não tombar
- Encaixe de 15 mm na base: segura o tablet mesmo com capa (até ~14 mm)
- Janelas em losango de 80 x 80 mm para economizar material
- 110 x 125 x 104 mm. Feito para o Galaxy Tab A 8.0; serve de 7" a 11" e celulares, deitados ou em pé

Na face de trás vai uma etiqueta com QR code que leva para a plataforma de monitorias gratuitas Apoio Escolar Periférico, onde o estudante se cadastra e agenda com um monitor voluntário. Cada cadastro feito pelo QR aparece no painel de impacto da plataforma.

Como imprimir
O arquivo já vem na orientação certa: o perfil dobrado deitado na mesa. Não precisa de suporte.
PETG (usado no protótipo) ou PLA, camada 0,2 mm, 5 paredes, brim de 5 mm. O protótipo levou 5 horas e 90 g de PETG numa Creality Ender 3.

Projeto da Global Solution FIAP 2026.2 (CitizenTech), disciplina Project-Based Maker Lab, Engenharia de Software, turma 4ESPR. Desenho técnico 3DP-2026-004 rev. C nos anexos.
```

### Lista de materiais
```
- 1 peça impressa em 3D em PETG (ou PLA), 90 g com o brim
- 1 etiqueta adesiva com QR code de 30 x 30 mm
- Parafusos, cola, montagem: nenhum
```


## 3. Pasta de arquivos com link público ✅

O repositório já é público:
`https://github.com/GiantMazelliWasHere/apoio-escolar-periferico/tree/main/maker`

```
maker/
├── cad/          .step · desenho técnico .pdf · desenho 2D .dxf
├── fabricacao/   .3mf · .stl
├── imagens/      renders · modelo/ (CAD) · fotos/ (impressão)
└── entrega/      scripts, PDF gerado e este roteiro
```

Depois de subir as fotos e o perfil, façam o merge na `main` e testem o link numa janela anônima.

## 4. PDF único

Ordem do PDF: capa (disciplina, título, integrantes) → **links clicáveis em destaque** (MakerWorld e pasta) → problema → solução → lista de materiais → fabricação → fotos → integração com a plataforma → arquivos.

1. Abra `maker/entrega/gerar_entrega.py` e preencha no topo:
   - `LINKS["Publicação no MakerWorld"]`: link do passo 2
   - `IMPRESSAO`: ✅ já preenchido (PETG, Ender 3, 5 h, 90 g)
   - `CREDITO_BONUS`: link da peça de origem, ou `"não se aplica"`
2. Fotos em `maker/imagens/fotos/`.
3. Rode (só precisa do Python e do Edge):

```bash
python maker/entrega/gerar_entrega.py
```

4. Abra `maker/entrega/Entrega_MakerLab_Suporte_Tablet.pdf`: **nada pode estar em amarelo**. O script lista no final o que falta.
5. Clique nos dois links dentro do PDF para testar.
6. Envie no portal até **19/11 às 23h55**.

> Se o STL mudar (rev. D…), rode `mvp/.venv/Scripts/python maker/entrega/renderizar_stl.py` para refazer os renders antes do PDF.

"""Gera o PDF único da entrega de Maker Lab (suporte de tablet 3DP-2026-004 rev. C).

Só biblioteca padrão + Microsoft Edge (ou Chrome) para imprimir o HTML em PDF.

    python maker/entrega/gerar_entrega.py

Antes de gerar a versão final:
  1. preencha LINKS abaixo (MakerWorld e pasta/repositório);
  2. coloque as fotos reais do protótipo em maker/imagens/fotos/ (jpg ou png; a ordem é a do nome);
  3. preencha IMPRESSAO e CREDITO_BONUS;
  4. o croqui do original fica em maker/imagens/original/croqui/ (fotos do original impresso,
     se houver, em maker/imagens/original/fotos/; sem elas, o PDF usa as fotos no local).
Campos vazios saem em destaque amarelo no PDF, para ninguém enviar sem perceber.
Os renders de maker/imagens/ saem de renderizar_stl.py (rode de novo se o STL mudar).
"""
from __future__ import annotations

import html
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MAKER = AQUI.parent
IMAGENS = MAKER / "imagens"
FOTOS = IMAGENS / "fotos"
MODELO = IMAGENS / "modelo"
ORIGINAL = IMAGENS / "original"              # capturas do CAD do modelo original (MakerWorld, CC0)
ORIGINAL_FOTOS = ORIGINAL / "fotos"           # fotos do original impresso de verdade
CROQUI = ORIGINAL / "croqui"                  # croqui com as medidas tiradas do original impresso
SAIDA_PDF = AQUI / "Entrega_MakerLab_Suporte_Tablet.pdf"
BASE = "suporte_tablet_3DP-2026-004_revC"
ETIQUETA = MAKER / "fabricacao" / "etiqueta_qr_30mm.svg"  # baixada de /maker do MVP publicado

# ----------------------------------------------------------------- preencher
ORIGINAL_URL = "https://makerworld.com/en/models/3631249-modular-ergonomic-tablet-stand"
ORIGINAL_AUTOR = "user_1365996764"
LINKS = {
    "Publicação no MakerWorld (redesign da equipe)": "https://makerworld.com/en/models/3634500-tablet-stand-for-studying-with-qr-code",
    "Plataforma (MVP publicado)": "https://app-apoioescolar-mvp-6e7462.azurewebsites.net/",
    "Pasta do repositório (arquivos brutos)": "https://github.com/GiantMazelliWasHere/apoio-escolar-periferico/tree/main/maker",
    "Modelo original redesenhado (MakerWorld, crédito)": ORIGINAL_URL,
    "Vídeo da peça, até 2 min (bônus)": "https://www.youtube.com/shorts/Tv9ENceZyYM",
}
# Como o protótipo foi impresso de verdade.
IMPRESSAO = "PETG, Creality Ender 3 (mesa 220 × 220 mm), perfil deitado, sem suporte, com brim: 5 horas e 90 g de filamento"
# Link de crédito da peça baixada usada no bônus (o modelo original que a rev. C redesenha).
CREDITO_BONUS = ORIGINAL_URL
# ---------------------------------------------------------------------------

# Legendas pelo nome do arquivo (sem extensão). Arquivo sem legenda aqui sai com uma genérica.
LEGENDAS = {
    "07_peca_pronta": "Protótipo pronto, fora da mesa e sem o brim: encaixe da base, painel de leitura com a janela em losango e, ao fundo, a perna traseira",
    "croqui_original": "Croqui do original com as medidas tiradas dos arquivos publicados (STEP, 3MF e DXF)",
    "08_uso_mesa_redonda": "Em uso no local: o suporte numa mesa de um espaço de convivência e estudo",
    "09_uso_mesa_quadrada": "Na mesa de estudo: a peça ocupa pouco espaço e deixa a frente livre para o caderno",
    "10_frente_de_perto": "De perto: painel de leitura, janela em losango e o encaixe da base",
    "11_na_bancada": "Numa bancada de trabalho: a mesma peça serve em qualquer mesa",
    "12_tablet_em_pe_frente": "Com o tablet em pé (Galaxy Tab com capa emborrachada): o encaixe segura a capa",
    "13_tablet_em_pe_lateral": "De lado: a perna traseira a 80° apoia o tablet sem tombar",
    "14_tablet_em_pe_tras": "Por trás: o tablet apoiado no painel de 65°",
    "15_tablet_deitado_lateral": "Tablet deitado: o mesmo suporte funciona na horizontal",
    "16_tablet_deitado_frente": "Tablet deitado, de frente: tela na altura de leitura e as mãos livres",
    "01_perfil_na_mesa": "Impressão em andamento: o perfil em A deitado na mesa, com encaixe, painel a 65° e perna a 80°",
    "02_vista_de_cima": "Vista de cima da mesa de 220 × 220 mm: a peça cabe com folga",
    "03_encaixe": "Encaixe de 15 mm da base, já com as primeiras camadas",
    "04_paineis_subindo": "Os dois painéis subindo juntos, sem suporte",
    "05_brim_perna_traseira": "Brim em volta da perna traseira, que é só o contorno fino da chapa",
    "06_lateral": "Lateral: as janelas em losango começando a aparecer",
    "01_cad_perspectiva": "Perspectiva: peça única dobrada, janelas em losango nos dois painéis",
    "02_cad_frontal": "Vista frontal: 110 × 125 mm com o encaixe embaixo",
    "03_cad_lateral": "Vista lateral: perfil em A com o encaixe à esquerda",
    "04_cad_de_cima": "Vista de cima: orientação de impressão, perfil deitado na mesa",
    "05_cad_perfil_e_frente_2d": "Desenho 2D: perfil da chapa dobrada e vista frontal com a janela",
    "01_original_perspectiva": "Original: o painel frontal com a aba (3D) e a chapa traseira (laser), maciços",
    "02_original_perfil": "Original, de perfil: as duas chapas de 3 mm soltas, sem dobradiça entre elas",
    "03_original_frente": "Original, de frente: chapas lisas de 220 × 140 mm, sem janelas",
}

DISCIPLINA = "Project-Based Maker Lab"
PROFESSOR = "Prof. Caio Sousa"
TITULO = "Suporte de tablet para estudo com QR code"
PROJETO = "Apoio Escolar Periférico · CitizenTech · FIAP Global Solution 2026.2"
EQUIPE = [
    ("Edson Leonardo", "553737"),
    ("Eduardo Mazelli", "553236"),
    ("Jó Sales", "552679"),
    ("Miguel Garcez de Carvalho", "553768"),
    ("Vinicius Souza e Silva", "552781"),
]
RESPONSAVEL = "Vinicius Souza e Silva"
TURMA = "Engenharia de Software · 4º ano · Turma 4ESPR"


def pendente(texto: str) -> str:
    return f'<span class="pendente">{html.escape(texto)}</span>'


def link_ou_pendente(url: str) -> str:
    if not url:
        return pendente("[PREENCHER: colar o link público]")
    u = html.escape(url)
    return f'<a href="{u}">{u}</a>'


def figura(caminho: Path, legenda: str) -> str:
    return f'<figure><img src="{caminho.as_uri()}" alt="{html.escape(legenda)}"><figcaption>{html.escape(legenda)}</figcaption></figure>'


def imagens_de(pasta: Path) -> list[Path]:
    return sorted(p for p in pasta.glob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".svg"}) if pasta.exists() else []


def galeria_de(arquivos: list[Path], generica: str, classe: str = "duas") -> str:
    return f'<div class="{classe}">' + "".join(
        figura(p, LEGENDAS.get(p.stem, f"{generica} ({i}/{len(arquivos)})")) for i, p in enumerate(arquivos, 1)
    ) + "</div>"


def montar_html() -> str:
    fotos = imagens_de(FOTOS)
    modelo = imagens_de(MODELO)
    original = imagens_de(ORIGINAL)
    fotos_orig = imagens_de(ORIGINAL_FOTOS)
    # Só entram aqui fotos do original. As fotos da rev. C ficam na seção 6.
    fotos_original = galeria_de(fotos_orig, "Original") if fotos_orig else ""
    croquis = imagens_de(CROQUI)
    croqui = "".join(figura(p, LEGENDAS.get(p.stem, "Croqui do original com as medidas")) for p in croquis) if croquis else (
        f'<p>{pendente("[PREENCHER: croqui com as medidas do original (altura, largura, ângulo, aba), em maker/imagens/original/croqui/]")}</p>')
    equipe = "".join(
        f"<tr><td>{html.escape(n)}</td><td>RM {rm}</td><td>{'Responsável pela disciplina' if n == RESPONSAVEL else ''}</td></tr>" for n, rm in EQUIPE
    )
    links = "".join(f'<div class="link"><p class="rotulo">{html.escape(k)}</p><p class="url">{link_ou_pendente(v)}</p></div>' for k, v in LINKS.items())
    def numero(p: Path) -> int:
        return int(p.stem.split("_")[0]) if p.stem.split("_")[0].isdigit() else 0
    fotos_impressao = [p for p in fotos if numero(p) <= 7]
    fotos_uso = [p for p in fotos if numero(p) >= 8]
    if fotos:
        galeria = galeria_de(fotos_impressao, "Protótipo") + (
            ('<h3>A peça em uso, com o tablet</h3>' + galeria_de(fotos_uso, "Em uso", "tres uso")) if fotos_uso else "")
    else:
        galeria = f'<p>{pendente("[PREENCHER: colocar as fotos reais do protótipo em maker/imagens/fotos/ e gerar de novo]")}</p>'
    impressao = html.escape(IMPRESSAO) if IMPRESSAO else pendente("[PREENCHER: material, impressora, camada, tempo e peso reais]")
    credito = link_ou_pendente(CREDITO_BONUS) if CREDITO_BONUS.startswith("http") else (html.escape(CREDITO_BONUS) if CREDITO_BONUS else pendente("[PREENCHER: link de crédito ou \"não se aplica\"]"))

    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>{TITULO}</title>
<style>
@page {{ size: A4; margin: 18mm 16mm; }}
body {{ font-family: "Segoe UI", Arial, sans-serif; color: #1c1b19; font-size: 10.5pt; line-height: 1.45; }}
h1 {{ font-size: 24pt; margin: 0 0 4mm; color: #0b6e4f; }}
h2 {{ font-size: 14pt; color: #0b6e4f; border-bottom: 2px solid #e4e0d8; padding-bottom: 1.5mm; margin: 8mm 0 3mm; break-after: avoid; }}
.capa {{ height: 250mm; display: flex; flex-direction: column; justify-content: center; break-after: page; }}
.capa .disc {{ font-size: 13pt; font-weight: 700; color: #b5470b; margin: 0 0 6mm; text-transform: uppercase; letter-spacing: .5pt; }}
.capa .proj {{ font-size: 12pt; color: #5a5750; margin: 0 0 8mm; }}
.capa img {{ width: 110mm; margin: 0 0 8mm; }}
table {{ border-collapse: collapse; width: 100%; }}
td, th {{ border-bottom: 1px solid #e4e0d8; padding: 1.8mm 2mm; text-align: left; vertical-align: top; }}
th {{ width: 38mm; color: #5a5750; }}
.links {{ break-after: page; }}
.link {{ border: 2px solid #0b6e4f; border-radius: 3mm; padding: 5mm 6mm; margin: 0 0 6mm; background: #e3f2ec; }}
.link .rotulo {{ margin: 0 0 2mm; font-weight: 700; font-size: 12pt; }}
.link .url {{ margin: 0; font-size: 12pt; word-break: break-all; }}
a {{ color: #0b5bd3; }}
.pendente {{ background: #ffe066; padding: 0 1mm; font-weight: 700; }}
figure {{ margin: 3mm 0; break-inside: avoid; }}
figure img {{ max-width: 100%; max-height: 95mm; object-fit: contain; border-radius: 2mm; display: block; }}
figcaption {{ font-size: 9pt; color: #5a5750; margin-top: 1mm; }}
.duas {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4mm; }}
.tres {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 3mm; }}
.tres figure img {{ max-height: 60mm; }}
.uso figure img {{ height: 68mm; width: 100%; object-fit: cover; }}
.fonte {{ font-size: 8.5pt; color: #5a5750; margin-top: 0; }}
.compara th {{ width: 32mm; }}
.compara thead th {{ width: auto; color: #0b6e4f; }}
.compara td {{ width: 50%; }}
.nova-pagina {{ break-before: page; }}
.lado figure img {{ height: 62mm; width: 100%; object-fit: contain; background: #2e3440; }}
.fluxo {{ background: #f4f2ee; border-radius: 2mm; padding: 3mm 4mm; font-family: Consolas, monospace; font-size: 9pt; white-space: pre-wrap; }}
h3 {{ font-size: 11.5pt; margin: 6mm 0 2mm; break-after: avoid; }}
code {{ font-family: Consolas, monospace; font-size: 9.5pt; }}
</style></head><body>

<section class="capa">
  <p class="disc">{DISCIPLINA} · {PROFESSOR}</p>
  <h1>{TITULO}</h1>
  <p class="proj">{PROJETO}<br>{TURMA}</p>
  <img src="{(IMAGENS / 'render_perspectiva.png').as_uri()}" alt="Render do suporte">
  <table><thead><tr><th colspan="3">Integrantes da equipe</th></tr></thead><tbody>{equipe}</tbody></table>
</section>

<section class="links">
  <h2>Links da entrega</h2>
  {links}
</section>

<h2>1. Diagnóstico do original</h2>
<h3>Quem é afetado</h3>
<p>O estudante de escola pública da periferia faz a monitoria online do Apoio Escolar Periférico pelo celular ou por um tablet emprestado, em casa, na biblioteca ou no espaço comunitário onde estuda. Sem apoio, ele segura o aparelho com uma mão ou o encosta em pilhas de livros, e fica sem as mãos livres para escrever no caderno, que é justamente o que a monitoria pede.</p>
<h3>O objeto original</h3>
<p>O ponto de partida é o suporte de tablet publicado no MakerWorld como <a href="{html.escape(ORIGINAL_URL)}">Modular Ergonomic Tablet Stand</a>, de {html.escape(ORIGINAL_AUTOR)} (licença Creative Commons Domínio Público). Ele tem duas peças: uma <strong>chapa traseira cortada a laser</strong> em MDF ou acrílico de 3 mm e um <strong>painel frontal impresso em 3D</strong> com uma aba de apoio na base, as duas com 220 × 140 mm. A publicação promete ajuste de ângulo por catraca, base larga, dobradiças e clipes impressos e um recorte para o cabo de carga.</p>
<p>Abrimos os arquivos publicados (STEP, 3MF e DXF) e medimos as peças. Foi isto que encontramos:</p>
<table><tbody>
<tr><th>Peças soltas</th><td>Os arquivos trazem só as duas chapas lisas. A dobradiça, a catraca de ângulo, os clipes e o recorte para o cabo descritos na publicação não estão neles. Sem nada que una as peças, o ângulo e a estabilidade dependem de como o estudante as apoia</td></tr>
<tr><th>Aba que não segura</th><td>A aba de apoio é uma cunha a 45° que termina em ponta, sem borda: nada impede o tablet com capa de escorregar para fora</td></tr>
<tr><th>Tamanho</th><td>As chapas de 220 × 140 mm ocupam boa parte de uma mesa pequena, que já divide espaço com o caderno</td></tr>
<tr><th>Material</th><td>Chapas maciças de 3 mm: cerca de 99 cm³ impressos mais 92 cm³ de chapa a laser (calculado do 3MF e do DXF)</td></tr>
<tr><th>Fabricação</th><td>Precisa de duas máquinas (cortadora a laser e impressora 3D) e de montagem</td></tr>
</tbody></table>
<div class="tres">
  {"".join(figura(p, LEGENDAS.get(p.stem, "Modelo original")) for p in original)}
</div>
<p class="fonte">Capturas do CAD do modelo original, reproduzidas da publicação no MakerWorld (domínio público).</p>
<h3>O local e as medidas</h3>
<p>O local de uso é o espaço de convivência e estudo onde a equipe testou a peça: mesas pequenas, redondas ou quadradas, divididas entre o aparelho, o caderno e o material. Numa mesa assim, as duas chapas soltas de 220 × 140 mm do original ocupam espaço e não ficam firmes quando o estudante toca na tela. O croqui abaixo traz as medidas do original, tiradas dos arquivos publicados. As fotos desse espaço, já com o redesign, estão na seção 6.</p>
{fotos_original}
{croqui}

<h2>2. O redesign</h2>
<p>Um suporte de mesa feito de <strong>uma única chapa dobrada de 2 mm</strong>, impresso em 3D de uma vez, sem montagem e sem parafusos. O painel da frente fica a 65° (boa inclinação de leitura), a perna traseira a 80° para não tombar, e um encaixe de 15 mm na base segura o tablet mesmo com capa. Janelas em losango de 80 × 80 mm nos dois painéis economizam material. Serve para tablets de 7" a 11" e celulares, deitados ou em pé (projetado em cima do Galaxy Tab A 8.0).</p>
<p>Na face de trás da perna traseira vai uma <strong>etiqueta com QR code</strong> que leva direto para a plataforma de monitorias.</p>
<div class="duas">
  {figura(IMAGENS / 'render_lateral.png', 'Vista lateral: encaixe de 15 mm, painel a 65° e perna a 80°')}
  {figura(IMAGENS / 'render_frontal.png', 'Vista frontal: 110 × 125 mm, janela em losango de 80 × 80 mm')}
</div>

{('<h3>Modelo 3D</h3>' + galeria_de(modelo, 'Modelo 3D')) if modelo else ''}

<h2 class="nova-pagina">3. Original × redesign, lado a lado</h2>
<div class="duas lado">
  {figura(ORIGINAL / '02_original_perfil.jpg', 'Antes: perfil do original, duas chapas de 3 mm soltas')}
  {figura(IMAGENS / 'render_lateral.png', 'Depois: perfil da rev. C, painel a 65° e perna a 80°')}
  {figura(ORIGINAL / '03_original_frente.jpg', 'Antes: frente do original, chapas lisas de 220 × 140 mm')}
  {figura(IMAGENS / 'render_frontal.png', 'Depois: frente da rev. C, janela em losango de 80 × 80 mm')}
</div>
<table class="compara"><thead><tr><th></th><th>Original</th><th>Redesign rev. C (da equipe)</th></tr></thead><tbody>
<tr><th>Forma</th><td>Duas peças planas de 3 mm: chapa traseira (laser) e painel frontal com aba (3D)</td><td>Uma chapa única de 2 mm dobrada em "A", com encaixe de 15 mm na base</td></tr>
<tr><th>Tamanho</th><td>220 × 140 mm</td><td>110 × 125 × 104 mm</td></tr>
<tr><th>Inclinação</th><td>Não definida nos arquivos: não há dobradiça nem trava entre as peças</td><td>Painel de leitura a 65°, fixo pela própria dobra</td></tr>
<tr><th>Estabilidade</th><td>Depende de como as duas peças soltas são apoiadas</td><td>Perna traseira a 80° e pegada de 104 × 125 mm na mesa</td></tr>
<tr><th>Fixação do aparelho</th><td>Aba em cunha a 45° que termina em ponta, sem borda</td><td>Encaixe de 15 mm: segura o tablet mesmo com capa (até ~14 mm)</td></tr>
<tr><th>Material</th><td>Maciço: ~99 cm³ impressos + ~92 cm³ de chapa a laser</td><td>51 cm³, com janelas em losango de 80 × 80 mm (90 g de PETG com brim)</td></tr>
<tr><th>Fabricação</th><td>Corte a laser, impressão 3D e montagem</td><td>Uma impressão, sem suporte e sem montagem, dobras com raio (R3 int. / R5 ext.)</td></tr>
<tr><th>Ligação com o cidadão</th><td>Nenhuma</td><td>Etiqueta QR que leva para a plataforma de monitorias gratuitas</td></tr>
</tbody></table>

<h2>4. Lista de materiais</h2>
<table><tbody>
<tr><th>Peça</th><td>1 peça impressa em 3D, 110 × 125 × 104 mm (largura × altura × fundo), chapa de 2 mm, dobras R3 int. / R5 ext.</td></tr>
<tr><th>Material</th><td>Filamento PETG: 90 g no protótipo, incluindo o brim (a peça em si tem 51 cm³, calculado do STL). PLA também serve</td></tr>
<tr><th>Etiqueta</th><td>QR code de 30 × 30 mm em papel adesivo, no canto inferior da face de trás da perna traseira</td></tr>
<tr><th>Montagem</th><td>Nenhuma: a peça sai pronta da impressora</td></tr>
<tr><th>Parafusos e cola</th><td>Nenhum</td></tr>
<tr><th>Crédito (bônus)</th><td>Redesign do modelo original de {html.escape(ORIGINAL_AUTOR)} no MakerWorld (domínio público): {credito}. O perfil em "A", o encaixe, as janelas, o QR e todo o CAD da rev. C são da equipe</td></tr>
</tbody></table>

<h2>5. Fabricação</h2>
<table><tbody>
<tr><th>Desenho técnico</th><td>Nº 3DP-2026-004 rev. C (17/11/2026): vistas lateral e frontal cotadas, perspectiva e especificações, tolerância ± 0,5 mm (<code>{BASE}_desenho_tecnico.pdf</code> e <code>_desenho_2d.dxf</code>)</td></tr>
<tr><th>Modelo 3D</th><td><code>{BASE}.step</code> (abre em qualquer CAD)</td></tr>
<tr><th>Impressão 3D</th><td><code>{BASE}_impressao.3mf</code> e <code>.stl</code>, já na orientação de impressão: o perfil dobrado deitado na mesa e a largura de 110 mm na altura. Assim as dobras saem sem suporte e as janelas em losango ficam com bordas a 45°. Pegada de 104 × 125 mm, cabe em qualquer impressora</td></tr>
<tr><th>Parâmetros recomendados</th><td>Bico 0,4 mm, camada 0,2 mm, 5 perímetros (parede de 2 mm maciça), sem suporte, brim de 5 mm (a base é só o contorno fino da chapa)</td></tr>
<tr><th>Impressão do protótipo</th><td>{impressao}</td></tr>
</tbody></table>

<h2>6. Fotos do protótipo</h2>
<p>Impressão do protótipo em PETG numa Creality Ender 3 (mesa de 220 × 220 mm), em 5 horas, na orientação dos arquivos: perfil deitado, sem suporte, com brim.</p>
{galeria}

<h2 class="nova-pagina">7. Antes e depois, e os ODS</h2>
<div class="duas lado">
  {figura(ORIGINAL / '03_original_frente.jpg', 'Antes: o original, duas chapas maciças soltas')}
  {figura(FOTOS / '12_tablet_em_pe_frente.jpg', 'Depois: a rev. C impressa, segurando o tablet com capa')}
</div>
<table class="compara"><thead><tr><th></th><th>Antes</th><th>Depois</th></tr></thead><tbody>
<tr><th>O que falhava</th><td>O aparelho na mão ou encostado em livros. O original promete ajuste de ângulo, mas os arquivos só trazem duas chapas soltas e uma aba que não segura a capa</td><td>O aparelho fica parado a 65°, preso pelo encaixe, mesmo quando o estudante toca na tela</td></tr>
<tr><th>O que mudou</th><td>Duas peças maciças de 3 mm, 220 × 140 mm, ângulo indefinido</td><td>Uma peça única com dobras de raio, perna a 80°, janelas que economizam material, sem montagem</td></tr>
<tr><th>Ganho para o cidadão</th><td>Uma mão ocupada segurando o aparelho e a postura ruim durante a aula</td><td>As duas mãos livres para escrever no caderno durante a monitoria, e um QR que leva direto para a plataforma gratuita</td></tr>
<tr><th>Quem consegue fabricar</th><td>Quem tem cortadora a laser e impressora 3D e monta as peças</td><td>Qualquer Fab Lab ou escola com uma impressora 3D de mesa: 5 h e 90 g de filamento, arquivos abertos no MakerWorld</td></tr>
</tbody></table>
<h3>ODS conectados</h3>
<table><tbody>
<tr><th>ODS 4: Educação de qualidade</th><td>Meta 4.1 (ensino fundamental e médio de qualidade) e meta 4.a (ambientes de aprendizagem adequados): o suporte melhora as condições de estudo de quem faz monitoria online por um aparelho emprestado</td></tr>
<tr><th>ODS 10: Redução das desigualdades</th><td>Meta 10.2 (inclusão de todos): a peça é barata, sai de qualquer impressora de Fab Lab e leva o estudante da periferia até uma plataforma de monitoria gratuita</td></tr>
</tbody></table>

<h2>8. Integração com a plataforma</h2>
<p>A peça não é um objeto isolado: o QR code é o contrato entre ela e o MVP. Quem lê o QR cai na plataforma com a origem marcada; se fizer o cadastro, o painel de impacto conta mais um "cadastro vindo da peça Maker Lab". Assim a peça vira um canal de aquisição local que o patrocinador consegue medir.</p>
<div class="fluxo">Etiqueta QR na peça → GET /qr (marca a origem "peca_maker")
→ página inicial: "Você chegou pelo QR code do suporte de estudo"
→ cadastro do estudante grava origem = peca_maker
→ /impacto: "Cadastros vindos da peça Maker Lab"</div>
<p>A página <code>/maker</code> do MVP mostra a peça e gera o QR em SVG no tamanho exato da etiqueta (30 mm), pronto para imprimir. A etiqueta definitiva, gerada no MVP publicado, aponta para <code>https://app-apoioescolar-mvp-6e7462.azurewebsites.net/qr</code>:</p>
<img src="{ETIQUETA.as_uri()}" alt="Etiqueta QR definitiva" style="width:30mm;height:30mm;display:block;margin:3mm 0">

<h2>9. Arquivos</h2>
<table><tbody>
<tr><th>Original</th><td><code>maker/imagens/original/</code>: capturas do CAD do modelo original e <code>croqui/</code> com as medidas; <code>maker/cad/original/</code>: os arquivos do original (.step, .3mf e o .dxf da chapa a laser), em domínio público. Arquivos-fonte no <a href="{html.escape(ORIGINAL_URL)}">MakerWorld</a></td></tr>
<tr><th>CAD e desenho</th><td><code>maker/cad/</code>: .step · desenho técnico .pdf · desenho 2D .dxf</td></tr>
<tr><th>Fabricação</th><td><code>maker/fabricacao/</code>: .3mf · .stl · etiqueta QR de 30 mm (.svg)</td></tr>
<tr><th>Imagens</th><td><code>maker/imagens/</code>: renders gerados do STL, <code>modelo/</code> (capturas do CAD) e <code>fotos/</code> (impressão do protótipo)</td></tr>
</tbody></table>
</body></html>"""


def navegador() -> str:
    for c in (
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        shutil.which("msedge") or "",
        shutil.which("chrome") or "",
        shutil.which("google-chrome") or "",
    ):
        if c and Path(c).exists():
            return c
    sys.exit("Edge/Chrome não encontrado.")


def main() -> None:
    # Perfil próprio do navegador: sem ele, o Edge pode entregar o trabalho a outra instância
    # e sair sem gravar o PDF. Ele também pode terminar de gravar depois de sair, por isso a espera.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        pagina = Path(tmp) / "entrega_maker.html"
        pagina.write_text(montar_html(), encoding="utf8")
        provisorio = Path(tmp) / "entrega_maker.pdf"
        subprocess.run(
            [navegador(), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
             f"--user-data-dir={Path(tmp) / 'perfil'}", "--allow-file-access-from-files",
             f"--print-to-pdf={provisorio}", pagina.as_uri()],
            check=True, timeout=120,
        )
        for _ in range(120):
            if provisorio.exists() and provisorio.stat().st_size > 0:
                tamanho = provisorio.stat().st_size
                time.sleep(1)
                if provisorio.stat().st_size == tamanho:
                    break
            time.sleep(0.5)
        else:
            sys.exit("O navegador não gravou o PDF.")
        shutil.copyfile(provisorio, SAIDA_PDF)
    print("PDF:", SAIDA_PDF.relative_to(MAKER.parent))
    faltando = [k for k, v in LINKS.items() if not v]
    if not IMPRESSAO:
        faltando.append("IMPRESSAO")
    if not CREDITO_BONUS:
        faltando.append("CREDITO_BONUS")
    if not (FOTOS.exists() and any(FOTOS.iterdir())):
        faltando.append("fotos em maker/imagens/fotos/")
    if not imagens_de(CROQUI):
        faltando.append("croqui do original em maker/imagens/original/croqui/")
    if faltando:
        print("Ainda em amarelo no PDF:", ", ".join(faltando))


if __name__ == "__main__":
    main()

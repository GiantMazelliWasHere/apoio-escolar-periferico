"""Gera os arquivos da entrega de Maker Lab: STLs (a partir do 3MF) e o PDF único do portal.

Só biblioteca padrão + Microsoft Edge (ou Chrome) para imprimir o HTML em PDF.

    python maker/entrega/gerar_entrega.py

Antes de gerar a versão final:
  1. preencha LINKS abaixo (MakerWorld e pasta/repositório);
  2. coloque as fotos reais do protótipo em maker/imagens/fotos/ (jpg ou png; a ordem é a do nome);
  3. confira MONTAGEM e CREDITO_BONUS.
Campos vazios saem em destaque amarelo no PDF, para ninguém enviar sem perceber.
"""
from __future__ import annotations

import html
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MAKER = AQUI.parent
FAB = MAKER / "fabricacao"
IMAGENS = MAKER / "imagens"
FOTOS = IMAGENS / "fotos"
ARQ_3MF = FAB / "suporte_tablet_impressao3d.3mf"
SAIDA_PDF = AQUI / "Entrega_MakerLab_Suporte_Tablet.pdf"

# ----------------------------------------------------------------- preencher
LINKS = {
    "Publicação no MakerWorld": "",
    "Pasta do repositório (arquivos brutos)": "https://github.com/GiantMazelliWasHere/apoio-escolar-periferico/tree/main/maker",
}
# Como as duas placas se unem (ex.: "colagem com cola de contato na aresta superior", "encaixe por pressão").
MONTAGEM = ""
# Link de crédito da peça baixada usada no bônus (deixe "não se aplica" se não usou nenhuma).
CREDITO_BONUS = ""
# ---------------------------------------------------------------------------

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


# ------------------------------------------------------------------ 3MF → STL

def ler_3mf(caminho: Path) -> dict[str, tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]]:
    xml = zipfile.ZipFile(caminho).read("3D/3dmodel.model").decode("utf8")
    corpos = {}
    for bloco in re.split(r"<object ", xml)[1:]:
        nome = re.search(r'name="([^"]*)"', bloco).group(1)
        vs = [tuple(map(float, v)) for v in re.findall(r'<vertex x="([-\d.eE+]+)" y="([-\d.eE+]+)" z="([-\d.eE+]+)"', bloco)]
        ts = [tuple(map(int, t)) for t in re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', bloco)]
        if vs and ts:
            corpos[nome] = (vs, ts)
    return corpos


def deitar(vs):
    """Placas modeladas em pé (220 mm de altura) → deitadas na mesa da impressora.
    Rotação própria (x, y, z) → (z, −y, x − x_mín): a face traseira da placa fica apoiada em z = 0."""
    xmin = min(v[0] for v in vs)
    return [(z, -y, x - xmin) for x, y, z in vs]


def escrever_stl(caminho: Path, vs, ts, nome: str) -> None:
    def sub(a, b):
        return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

    with open(caminho, "wb") as f:
        f.write(nome.encode("ascii", "replace")[:80].ljust(80, b" "))
        f.write(struct.pack("<I", len(ts)))
        for i, j, k in ts:
            a, b, c = vs[i], vs[j], vs[k]
            u, w = sub(b, a), sub(c, a)
            n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
            m = sum(x * x for x in n) ** 0.5 or 1.0
            f.write(struct.pack("<12fH", *(x / m for x in n), *a, *b, *c, 0))


def gerar_stls() -> list[Path]:
    nomes = {"Body1": "suporte_tablet_placa_frente.stl", "Body3": "suporte_tablet_apoio_traseiro.stl"}
    saidas = []
    for corpo, (vs, ts) in ler_3mf(ARQ_3MF).items():
        destino = FAB / nomes.get(corpo, f"suporte_tablet_{corpo.lower()}.stl")
        escrever_stl(destino, deitar(vs), ts, f"Apoio Escolar Periferico - {corpo}")
        saidas.append(destino)
    return saidas


# ------------------------------------------------------------------------ PDF

def pendente(texto: str) -> str:
    return f'<span class="pendente">{html.escape(texto)}</span>'


def link_ou_pendente(url: str) -> str:
    if not url:
        return pendente("[PREENCHER: colar o link público]")
    u = html.escape(url)
    return f'<a href="{u}">{u}</a>'


def figura(caminho: Path, legenda: str) -> str:
    return f'<figure><img src="{caminho.as_uri()}" alt="{html.escape(legenda)}"><figcaption>{html.escape(legenda)}</figcaption></figure>'


def montar_html() -> str:
    fotos = sorted(p for p in FOTOS.glob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}) if FOTOS.exists() else []
    equipe = "".join(
        f"<tr><td>{html.escape(n)}</td><td>RM {rm}</td><td>{'Responsável pela disciplina' if n == RESPONSAVEL else ''}</td></tr>" for n, rm in EQUIPE
    )
    links = "".join(f'<div class="link"><p class="rotulo">{html.escape(k)}</p><p class="url">{link_ou_pendente(v)}</p></div>' for k, v in LINKS.items())
    if fotos:
        galeria = "".join(figura(p, f"Protótipo montado ({i}/{len(fotos)})") for i, p in enumerate(fotos, 1))
    else:
        galeria = f'<p>{pendente("[PREENCHER: colocar as fotos reais do protótipo montado em maker/imagens/fotos/ e gerar de novo]")}</p>'
    montagem = html.escape(MONTAGEM) if MONTAGEM else pendente("[PREENCHER: como as duas placas se unem]")
    credito = link_ou_pendente(CREDITO_BONUS) if CREDITO_BONUS.startswith("http") else (html.escape(CREDITO_BONUS) if CREDITO_BONUS else pendente("[PREENCHER: link de crédito ou \"não se aplica\"]"))

    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>{TITULO}</title>
<style>
@page {{ size: A4; margin: 18mm 16mm; }}
body {{ font-family: "Segoe UI", Arial, sans-serif; color: #1c1b19; font-size: 10.5pt; line-height: 1.45; }}
h1 {{ font-size: 24pt; margin: 0 0 4mm; color: #0b6e4f; }}
h2 {{ font-size: 14pt; color: #0b6e4f; border-bottom: 2px solid #e4e0d8; padding-bottom: 1.5mm; margin: 8mm 0 3mm; break-after: avoid; }}
.capa {{ height: 250mm; display: flex; flex-direction: column; justify-content: center; break-after: page; }}
.capa .disc {{ font-size: 13pt; font-weight: 700; color: #b5470b; margin: 0 0 6mm; text-transform: uppercase; letter-spacing: .5pt; }}
.capa .proj {{ font-size: 12pt; color: #5a5750; margin: 0 0 10mm; }}
.capa img {{ width: 120mm; border-radius: 3mm; margin: 0 0 10mm; }}
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
figure img {{ max-width: 100%; max-height: 110mm; border-radius: 2mm; display: block; }}
figcaption {{ font-size: 9pt; color: #5a5750; margin-top: 1mm; }}
.duas {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4mm; }}
.fluxo {{ background: #f4f2ee; border-radius: 2mm; padding: 3mm 4mm; font-family: Consolas, monospace; font-size: 9pt; white-space: pre-wrap; }}
code {{ font-family: Consolas, monospace; font-size: 9.5pt; }}
</style></head><body>

<section class="capa">
  <p class="disc">{DISCIPLINA} · {PROFESSOR}</p>
  <h1>{TITULO}</h1>
  <p class="proj">{PROJETO}<br>{TURMA}</p>
  <img src="{(IMAGENS / 'render_frente_proximo.png').as_uri()}" alt="Render do suporte">
  <table><thead><tr><th colspan="3">Integrantes da equipe</th></tr></thead><tbody>{equipe}</tbody></table>
</section>

<section class="links">
  <h2>Links da entrega</h2>
  {links}
</section>

<h2>1. O problema</h2>
<p>O estudante de escola pública da periferia faz a monitoria online do Apoio Escolar Periférico pelo celular ou por um tablet emprestado. Sem apoio, ele segura o aparelho com uma mão ou o encosta em pilhas de livros, e fica sem as mãos livres para escrever no caderno, que é justamente o que a monitoria pede.</p>

<h2>2. A solução</h2>
<p>Um suporte de mesa simples e barato, feito de duas placas planas: a placa da frente tem uma aba na base que segura o tablet ou o celular inclinado; o apoio traseiro dá a inclinação. Na placa da frente vai uma <strong>etiqueta com QR code</strong> que leva direto para a plataforma de monitorias.</p>
<div class="duas">
  {figura(IMAGENS / 'render_frente.png', 'Modelo 3D montado (Fusion 360)')}
  {figura(IMAGENS / 'render_perfil.png', 'Vista de perfil das duas placas')}
</div>

<h2>3. Lista de materiais</h2>
<table><tbody>
<tr><th>Placa da frente</th><td>220 × 140 mm, 3 mm de espessura, com aba de 27 mm na base. Impressão 3D em PLA</td></tr>
<tr><th>Apoio traseiro</th><td>220 × 140 mm, chapa de 3 mm (MDF ou acrílico) em corte a laser, ou impressão 3D em PLA</td></tr>
<tr><th>Etiqueta</th><td>QR code de 40 × 40 mm, impresso em papel adesivo ou gravado a laser na placa da frente</td></tr>
<tr><th>Montagem</th><td>{montagem}</td></tr>
<tr><th>Parafusos</th><td>Nenhum</td></tr>
<tr><th>Crédito (bônus)</th><td>{credito}</td></tr>
</tbody></table>

<h2>4. Fabricação</h2>
<table><tbody>
<tr><th>Modelagem</th><td>Autodesk Fusion 360 (<code>suporte_tablet.f3d</code>), exportado em STEP e FBX</td></tr>
<tr><th>Impressão 3D</th><td><code>suporte_tablet_impressao3d.3mf</code> (as duas placas) e STLs separados, já deitados na mesa: <code>suporte_tablet_placa_frente.stl</code> e <code>suporte_tablet_apoio_traseiro.stl</code>. Cabem em mesa de 220 × 220 mm</td></tr>
<tr><th>Corte a laser</th><td><code>apoio_traseiro_corte_laser.dxf</code>: contorno de 220 × 140 mm para chapa de 3 mm</td></tr>
</tbody></table>

<h2>5. Fotos do protótipo montado</h2>
{galeria}

<h2>6. Integração com a plataforma</h2>
<p>A peça não é um objeto isolado: o QR code é o contrato entre ela e o MVP. Quem lê o QR cai na plataforma com a origem marcada; se fizer o cadastro, o painel de impacto conta mais um "cadastro vindo da peça Maker Lab". Assim a peça vira um canal de aquisição local que o patrocinador consegue medir.</p>
<div class="fluxo">Etiqueta QR na peça → GET /qr (marca a origem "peca_maker")
→ página inicial: "Você chegou pelo QR code do suporte de estudo"
→ cadastro do estudante grava origem = peca_maker
→ /impacto: "Cadastros vindos da peça Maker Lab"</div>
<p>A página <code>/maker</code> do MVP mostra a peça e gera o QR em SVG no tamanho da etiqueta, pronto para imprimir ou gravar a laser.</p>

<h2>7. Arquivos</h2>
<table><tbody>
<tr><th>CAD</th><td><code>maker/cad/</code>: suporte_tablet.f3d · suporte_tablet.step · suporte_tablet.fbx</td></tr>
<tr><th>Fabricação</th><td><code>maker/fabricacao/</code>: .3mf · 2 × .stl · .dxf</td></tr>
<tr><th>Imagens</th><td><code>maker/imagens/</code>: renders e fotos do protótipo</td></tr>
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
    for p in gerar_stls():
        print("STL:", p.relative_to(MAKER.parent))
    with tempfile.TemporaryDirectory() as tmp:
        pagina = Path(tmp) / "entrega_maker.html"
        pagina.write_text(montar_html(), encoding="utf8")
        subprocess.run(
            [navegador(), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
             "--allow-file-access-from-files", f"--print-to-pdf={SAIDA_PDF}", pagina.as_uri()],
            check=True, timeout=120,
        )
    print("PDF:", SAIDA_PDF.relative_to(MAKER.parent))
    faltando = [k for k, v in LINKS.items() if not v]
    if not MONTAGEM:
        faltando.append("MONTAGEM")
    if not CREDITO_BONUS:
        faltando.append("CREDITO_BONUS")
    if not (FOTOS.exists() and any(FOTOS.iterdir())):
        faltando.append("fotos em maker/imagens/fotos/")
    if faltando:
        print("Ainda em amarelo no PDF:", ", ".join(faltando))


if __name__ == "__main__":
    main()

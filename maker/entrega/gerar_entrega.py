"""Gera o PDF único da entrega de Maker Lab (suporte de tablet 3DP-2026-004 rev. C).

Só biblioteca padrão + Microsoft Edge (ou Chrome) para imprimir o HTML em PDF.

    python maker/entrega/gerar_entrega.py

Antes de gerar a versão final:
  1. preencha LINKS abaixo (MakerWorld e pasta/repositório);
  2. coloque as fotos reais do protótipo em maker/imagens/fotos/ (jpg ou png; a ordem é a do nome);
  3. preencha IMPRESSAO e CREDITO_BONUS.
Campos vazios saem em destaque amarelo no PDF, para ninguém enviar sem perceber.
Os renders de maker/imagens/ saem de renderizar_stl.py (rode de novo se o STL mudar).
"""
from __future__ import annotations

import html
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MAKER = AQUI.parent
IMAGENS = MAKER / "imagens"
FOTOS = IMAGENS / "fotos"
MODELO = IMAGENS / "modelo"
SAIDA_PDF = AQUI / "Entrega_MakerLab_Suporte_Tablet.pdf"
BASE = "suporte_tablet_3DP-2026-004_revC"
ETIQUETA = MAKER / "fabricacao" / "etiqueta_qr_30mm.svg"  # baixada de /maker do MVP publicado

# ----------------------------------------------------------------- preencher
LINKS = {
    "Publicação no MakerWorld": "https://makerworld.com/en/models/3634500-tablet-stand-for-studying-with-qr-code",
    "Plataforma (MVP publicado)": "https://app-apoioescolar-mvp-6e7462.azurewebsites.net/",
    "Pasta do repositório (arquivos brutos)": "https://github.com/GiantMazelliWasHere/apoio-escolar-periferico/tree/main/maker",
}
# Como o protótipo foi impresso de verdade.
IMPRESSAO = "PETG, Creality Ender 3 (mesa 220 × 220 mm), perfil deitado, sem suporte, com brim: 5 horas e 90 g de filamento"
# Link de crédito da peça baixada usada no bônus (deixe "não se aplica" se não usou nenhuma).
CREDITO_BONUS = ""
# ---------------------------------------------------------------------------

# Legendas pelo nome do arquivo (sem extensão). Arquivo sem legenda aqui sai com uma genérica.
LEGENDAS = {
    "07_peca_pronta": "Protótipo pronto, fora da mesa e sem o brim: encaixe da base, painel de leitura com a janela em losango e, ao fundo, a perna traseira",
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
    return sorted(p for p in pasta.glob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}) if pasta.exists() else []


def galeria_de(arquivos: list[Path], generica: str) -> str:
    return '<div class="duas">' + "".join(
        figura(p, LEGENDAS.get(p.stem, f"{generica} ({i}/{len(arquivos)})")) for i, p in enumerate(arquivos, 1)
    ) + "</div>"


def montar_html() -> str:
    fotos = imagens_de(FOTOS)
    modelo = imagens_de(MODELO)
    equipe = "".join(
        f"<tr><td>{html.escape(n)}</td><td>RM {rm}</td><td>{'Responsável pela disciplina' if n == RESPONSAVEL else ''}</td></tr>" for n, rm in EQUIPE
    )
    links = "".join(f'<div class="link"><p class="rotulo">{html.escape(k)}</p><p class="url">{link_ou_pendente(v)}</p></div>' for k, v in LINKS.items())
    if fotos:
        galeria = galeria_de(fotos, "Protótipo")
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

<h2>1. O problema</h2>
<p>O estudante de escola pública da periferia faz a monitoria online do Apoio Escolar Periférico pelo celular ou por um tablet emprestado. Sem apoio, ele segura o aparelho com uma mão ou o encosta em pilhas de livros, e fica sem as mãos livres para escrever no caderno, que é justamente o que a monitoria pede.</p>

<h2>2. A solução</h2>
<p>Um suporte de mesa feito de <strong>uma única chapa dobrada de 2 mm</strong>, impresso em 3D de uma vez, sem montagem e sem parafusos. O painel da frente fica a 65° (boa inclinação de leitura), a perna traseira a 80° para não tombar, e um encaixe de 15 mm na base segura o tablet mesmo com capa. Janelas em losango de 80 × 80 mm nos dois painéis economizam material. Serve para tablets de 7" a 11" e celulares, deitados ou em pé (projetado em cima do Galaxy Tab A 8.0).</p>
<p>Na face de trás da perna traseira vai uma <strong>etiqueta com QR code</strong> que leva direto para a plataforma de monitorias.</p>
<div class="duas">
  {figura(IMAGENS / 'render_lateral.png', 'Vista lateral: encaixe de 15 mm, painel a 65° e perna a 80°')}
  {figura(IMAGENS / 'render_frontal.png', 'Vista frontal: 110 × 125 mm, janela em losango de 80 × 80 mm')}
</div>

{('<h3>Modelo 3D</h3>' + galeria_de(modelo, 'Modelo 3D')) if modelo else ''}

<h2>3. Lista de materiais</h2>
<table><tbody>
<tr><th>Peça</th><td>1 peça impressa em 3D, 110 × 125 × 104 mm (largura × altura × fundo), chapa de 2 mm, dobras R3 int. / R5 ext.</td></tr>
<tr><th>Material</th><td>Filamento PETG: 90 g no protótipo, incluindo o brim (a peça em si tem 51 cm³, calculado do STL). PLA também serve</td></tr>
<tr><th>Etiqueta</th><td>QR code de 30 × 30 mm em papel adesivo, no canto inferior da face de trás da perna traseira</td></tr>
<tr><th>Montagem</th><td>Nenhuma: a peça sai pronta da impressora</td></tr>
<tr><th>Parafusos e cola</th><td>Nenhum</td></tr>
<tr><th>Crédito (bônus)</th><td>{credito}</td></tr>
</tbody></table>

<h2>4. Fabricação</h2>
<table><tbody>
<tr><th>Desenho técnico</th><td>Nº 3DP-2026-004 rev. C (17/11/2026): vistas lateral e frontal cotadas, perspectiva e especificações, tolerância ± 0,5 mm (<code>{BASE}_desenho_tecnico.pdf</code> e <code>_desenho_2d.dxf</code>)</td></tr>
<tr><th>Modelo 3D</th><td><code>{BASE}.step</code> (abre em qualquer CAD)</td></tr>
<tr><th>Impressão 3D</th><td><code>{BASE}_impressao.3mf</code> e <code>.stl</code>, já na orientação de impressão: o perfil dobrado deitado na mesa e a largura de 110 mm na altura. Assim as dobras saem sem suporte e as janelas em losango ficam com bordas a 45°. Pegada de 104 × 125 mm, cabe em qualquer impressora</td></tr>
<tr><th>Parâmetros recomendados</th><td>Bico 0,4 mm, camada 0,2 mm, 5 perímetros (parede de 2 mm maciça), sem suporte, brim de 5 mm (a base é só o contorno fino da chapa)</td></tr>
<tr><th>Impressão do protótipo</th><td>{impressao}</td></tr>
</tbody></table>

<h2>5. Fotos do protótipo</h2>
<p>Impressão do protótipo em PETG numa Creality Ender 3 (mesa de 220 × 220 mm), em 5 horas, na orientação dos arquivos: perfil deitado, sem suporte, com brim.</p>
{galeria}

<h2>6. Integração com a plataforma</h2>
<p>A peça não é um objeto isolado: o QR code é o contrato entre ela e o MVP. Quem lê o QR cai na plataforma com a origem marcada; se fizer o cadastro, o painel de impacto conta mais um "cadastro vindo da peça Maker Lab". Assim a peça vira um canal de aquisição local que o patrocinador consegue medir.</p>
<div class="fluxo">Etiqueta QR na peça → GET /qr (marca a origem "peca_maker")
→ página inicial: "Você chegou pelo QR code do suporte de estudo"
→ cadastro do estudante grava origem = peca_maker
→ /impacto: "Cadastros vindos da peça Maker Lab"</div>
<p>A página <code>/maker</code> do MVP mostra a peça e gera o QR em SVG no tamanho exato da etiqueta (30 mm), pronto para imprimir. A etiqueta definitiva, gerada no MVP publicado, aponta para <code>https://app-apoioescolar-mvp-6e7462.azurewebsites.net/qr</code>:</p>
<img src="{ETIQUETA.as_uri()}" alt="Etiqueta QR definitiva" style="width:30mm;height:30mm;display:block;margin:3mm 0">

<h2>7. Arquivos</h2>
<table><tbody>
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
    if not IMPRESSAO:
        faltando.append("IMPRESSAO")
    if not CREDITO_BONUS:
        faltando.append("CREDITO_BONUS")
    if not (FOTOS.exists() and any(FOTOS.iterdir())):
        faltando.append("fotos em maker/imagens/fotos/")
    if faltando:
        print("Ainda em amarelo no PDF:", ", ".join(faltando))


if __name__ == "__main__":
    main()

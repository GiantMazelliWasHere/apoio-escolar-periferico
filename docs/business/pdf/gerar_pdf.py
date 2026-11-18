"""Gera o PDF único de Business a partir dos documentos em Markdown.

Fonte da verdade: Entrega_Business_Apoio_Escolar_Periferico.md (seções 1 a 10)
e Roteiro_Entrevistas_Validacao.md (planilha, testes e critérios, como anexo).
Edite os .md, ajuste LINKS abaixo e rode de novo:

    python -m pip install -r docs/business/pdf/requirements.txt
    python docs/business/pdf/gerar_pdf.py

Gera duas versões:
- Business_Apoio_Escolar_Periferico.pdf (entrega): sem a legenda "Como ler este
  documento" e sem a nota "o que foi validado" do Lean Canvas.
- Business_Apoio_Escolar_Periferico_Documentacao.pdf: completo, com as duas notas.

Requer o Microsoft Edge (ou Chrome) instalado para imprimir o HTML em PDF.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import markdown

AQUI = Path(__file__).resolve().parent
BUSINESS = AQUI.parent
REPO_URL = "https://github.com/GiantMazelliWasHere/apoio-escolar-periferico"
BLOB = f"{REPO_URL}/blob/main/docs/business/"

# Preencha quando existirem. Ficam em destaque amarelo enquanto estiverem vazios.
LINKS = {
    "Vídeo-pitch (YouTube, não listado)": "",
    "MVP (URL pública)": "https://app-apoioescolar-mvp-6e7462.azurewebsites.net",
    "Repositório": REPO_URL,
    "Peça Maker Lab no MakerWorld": "https://makerworld.com/en/models/3634500-tablet-stand-for-studying-with-qr-code",
    "Ficha Técnica do MVP": f"{REPO_URL}/blob/main/docs/FICHA_TECNICA_MVP.md",
}

VERSOES = {
    # nome do arquivo (sem extensão): manter as notas de leitura e de validação?
    "Business_Apoio_Escolar_Periferico": False,
    "Business_Apoio_Escolar_Periferico_Documentacao": True,
}

COMO_LER = re.compile(r"(?m)^> \*\*Como ler este documento\.\*\*.*\n(?:>.*\n?)*")
NOTA_VALIDADO = re.compile(r'(?m)^> \*\*Nota sobre "o que foi validado".*\n?')


def secoes(texto: str) -> tuple[str, dict[str, str]]:
    """Separa o cabeçalho e as seções de nível 2, indexadas pelo número ("1", "2"…)."""
    partes = re.split(r"(?m)^## ", texto)
    cabecalho, resto = partes[0], partes[1:]
    out = {}
    for p in resto:
        m = re.match(r"(\d+)\.", p)
        out[m.group(1) if m else p.split("\n", 1)[0]] = "## " + p
    return cabecalho, out


def ajustar_links(md: str) -> str:
    md = re.sub(r"\]\(\.\./([^)]+)\)", lambda m: f"]({REPO_URL}/blob/main/docs/{m.group(1)})", md)
    md = re.sub(r"\]\(((?:Roteiro|Entrega)_[^)]+)\)", lambda m: f"]({BLOB}{m.group(1)})", md)
    return md


def limpar_secao(md: str) -> str:
    md = md.rstrip().removesuffix("---").rstrip()
    # Notas internas da equipe não vão para o PDF.
    md = re.sub(r"(?m)^> \*\*Não afirmar no pitch.*\n?", "", md)
    return md


def montar_markdown(com_notas: bool) -> str:
    entrega = (BUSINESS / "Entrega_Business_Apoio_Escolar_Periferico.md").read_text(encoding="utf-8")
    if not com_notas:
        entrega = NOTA_VALIDADO.sub("", COMO_LER.sub("", entrega))
    roteiro = (BUSINESS / "Roteiro_Entrevistas_Validacao.md").read_text(encoding="utf-8")

    cab, sec = secoes(entrega)
    cab = re.sub(r"(?m)^\*\*Prazo:\*\*.*\n", "", cab).rstrip().removesuffix("---").rstrip()

    links = "\n".join(
        f"| {nome} | {f'[{url}]({url})' if url else '**[PREENCHER]**'} |" for nome, url in LINKS.items()
    )
    capa = f"{cab}\n\n### Links da entrega\n\n| Item | Link |\n|---|---|\n{links}\n"

    corpo = [limpar_secao(sec[str(n)]) for n in range(1, 11)]

    fontes = entrega.split("### Fontes e observações", 1)[1]
    fontes = "\n".join(l for l in fontes.splitlines() if "Google Drive" not in l)
    corpo.append("## Fontes e observações\n" + fontes.strip())

    _, sec_r = secoes(roteiro)
    anexo_planilha = sec_r["6"].replace("## 6. Planilha de registro (consolidada)", "### A.1 Planilha de registro das entrevistas", 1)
    anexo_planilha = anexo_planilha.replace("### Teste de usabilidade: tempos e notas", "### A.2 Teste de usabilidade: tempos e notas")
    anexo_criterios = sec_r["7"].replace("## 7. Critérios para marcar um bloco como **Validado**", "### A.3 Critérios de validação e resultado", 1)
    anexo = (
        "## Anexo A · Validação qualitativa (14/11/2026)\n\n"
        "10 entrevistas (5 estudantes, 1 coordenação, 2 voluntários, 2 ESG/instituto) e teste de usabilidade no MVP. "
        "Participantes identificados só por código (LGPD). Roteiro completo e respostas: "
        f"[Roteiro_Entrevistas_Validacao.md]({BLOB}Roteiro_Entrevistas_Validacao.md).\n\n"
        + limpar_secao(anexo_planilha) + "\n\n" + limpar_secao(anexo_criterios)
    )
    corpo.append(anexo)

    return ajustar_links(capa + "\n\n" + "\n\n".join(corpo))


CSS = """
@page { size: A4; margin: 16mm 14mm 18mm; }
* { box-sizing: border-box; }
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 10pt; line-height: 1.45; color: #1d2421; }
h1 { font-size: 20pt; color: #1f5c46; margin: 0 0 6pt; }
h2 { font-size: 15pt; color: #1f5c46; border-bottom: 2px solid #4cc79a; padding-bottom: 3pt; margin-top: 0; break-before: page; }
h3 { font-size: 11.5pt; color: #24493c; margin: 14pt 0 5pt; break-after: avoid; }
p, li { orphans: 3; widows: 3; }
a { color: #1a6b8f; word-break: break-all; }
table { width: 100%; border-collapse: collapse; margin: 6pt 0 10pt; font-size: 8pt; line-height: 1.35; }
th { background: #e3f3ec; text-align: left; }
th, td { border: 1px solid #b9cfc5; padding: 3pt 4pt; vertical-align: top; }
tr { break-inside: avoid; }
blockquote { margin: 8pt 0; padding: 6pt 10pt; background: #f4f8f6; border-left: 4px solid #4cc79a; }
code { font-size: 8.5pt; background: #eef2f0; padding: 0 2pt; }
.preencher { background: #fff1a8; padding: 0 2pt; }
"""


LISTA = re.compile(r"^(> )?(- |\d+\. )")


def separar_blocos(md: str) -> str:
    """O Python-Markdown exige linha em branco antes de listas e entre linhas soltas
    do cabeçalho (o GitHub não). Insere essas linhas sem mudar o conteúdo."""
    out: list[str] = []
    for linha in md.splitlines():
        ant = out[-1] if out else ""
        if ant.strip() and ant.strip() != ">" and not ant.startswith("|"):
            eh_lista, ant_lista = LISTA.match(linha), LISTA.match(ant)
            cabecalho = linha.startswith("**") and ant.startswith("**")
            if (eh_lista and not ant_lista) or cabecalho:
                out.append(">" if linha.startswith(">") else "")
        out.append(linha)
    return "\n".join(out)


def gerar_html(md_texto: str) -> str:
    html = markdown.markdown(separar_blocos(md_texto), extensions=["tables", "sane_lists"])
    html = re.sub(r"\[PREENCHER[^\]]*\]", lambda m: f'<span class="preencher">{m.group(0)}</span>', html)
    return (
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        "<title>Apoio Escolar Periférico · Business</title>"
        f"<style>{CSS}</style></head><body>{html}</body></html>"
    )


def navegador() -> str:
    candidatos = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        shutil.which("msedge") or "",
        shutil.which("google-chrome") or "",
        shutil.which("chromium") or "",
    ]
    for c in candidatos:
        if c and Path(c).exists():
            return c
    sys.exit("Edge/Chrome não encontrado: abra o HTML gerado e imprima em PDF.")


def main() -> None:
    nav = navegador()
    for nome, com_notas in VERSOES.items():
        html, pdf = AQUI / f"{nome}.html", AQUI / f"{nome}.pdf"
        html.write_text(gerar_html(montar_markdown(com_notas)), encoding="utf-8")
        subprocess.run(
            [nav, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
             f"--print-to-pdf={pdf}", html.as_uri()],
            check=True, capture_output=True, timeout=120,
        )
        print(f"HTML: {html}\nPDF:  {pdf}")


if __name__ == "__main__":
    main()

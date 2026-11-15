"""Monta o PDF de Big Data com o diagrama e os prints do Airflow.

Entrada: o PDF original do Jó (dados/Entrega_BigData_ApoioEscolar.pdf), sem alterar.
Saída:   dados/Entrega_BigData_ApoioEscolar_com_evidencias.pdf

- As duas caixas "Substitua esta caixa..." da página 2 passam a apontar para os anexos.
- Anexos novos: A (diagrama de arquitetura) e B (prints da execução no Airflow e
  do resultado no MVP), a partir das imagens em evidencias/recortes/.
- O rodapé "Page X of Y" é refeito com o novo total de páginas.

Uso (na pasta dados/): .venv/Scripts/python evidencias/montar_pdf.py
Requer: pymupdf.
"""
from pathlib import Path

import pymupdf as fitz

BASE = Path(__file__).resolve().parent
ENTRADA = BASE.parent / "Entrega_BigData_ApoioEscolar.pdf"
SAIDA = BASE.parent / "Entrega_BigData_ApoioEscolar_com_evidencias.pdf"
REC = BASE / "recortes"

CINZA = (0x64 / 255, 0x74 / 255, 0x8B / 255)
ESCURO = (0x0F / 255, 0x17 / 255, 0x2A / 255)
FUNDO_CAIXA = (0.9725, 0.9804, 0.9882)
MARGEM = 51
LARGURA = 595 - 2 * MARGEM


def substituir_caixa(page: fitz.Page, caixa: fitz.Rect, texto: str) -> None:
    page.add_redact_annot(caixa + (3, 3, -3, -3), fill=FUNDO_CAIXA)
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE)
    page.insert_textbox(caixa + (10, 0, -10, 0), texto, fontname="helv", fontsize=10, color=CINZA, align=fitz.TEXT_ALIGN_CENTER)


def centralizar_vertical(caixa: fitz.Rect, linhas: int, tamanho: float = 10) -> fitz.Rect:
    altura = linhas * tamanho * 1.25
    topo = caixa.y0 + (caixa.height - altura) / 2
    return fitz.Rect(caixa.x0, topo, caixa.x1, caixa.y1)


def titulo(page: fitz.Page, y: float, texto: str, tamanho: float = 13) -> float:
    page.insert_text((MARGEM, y + tamanho), texto, fontname="hebo", fontsize=tamanho, color=ESCURO)
    return y + tamanho + 10


def imagem(page: fitz.Page, y: float, arquivo: str, legenda: str) -> float:
    pix = fitz.Pixmap(str(REC / arquivo))
    altura = LARGURA * pix.height / pix.width
    rect = fitz.Rect(MARGEM, y, MARGEM + LARGURA, y + altura)
    page.insert_image(rect, filename=str(REC / arquivo))
    page.draw_rect(rect, color=(0.8, 0.84, 0.88), width=0.6)
    y = rect.y1 + 4
    usado = page.insert_textbox(fitz.Rect(MARGEM, y, MARGEM + LARGURA, y + 40), legenda, fontname="helv", fontsize=8.5, color=CINZA)
    return y + (40 - usado) + 12


def main() -> None:
    doc = fitz.open(ENTRADA)
    p2 = doc[1]
    W, H = p2.rect.width, p2.rect.height

    caixa_diagrama = fitz.Rect(51, 164, 544, 227)
    caixa_prints = fitz.Rect(51, 660, 544, 750)
    substituir_caixa(p2, caixa_diagrama, "")
    p2.insert_textbox(centralizar_vertical(caixa_diagrama, 2) + (10, 0, -10, 0),
                      "Diagrama de Arquitetura do Pipeline: ver Anexo A (página 3).\n"
                      "Origem INEP/IBGE -> Airflow (extract -> transform -> load) -> API do MVP -> painel /impacto",
                      fontname="helv", fontsize=10, color=CINZA, align=fitz.TEXT_ALIGN_CENTER)
    substituir_caixa(p2, caixa_prints, "")
    p2.insert_textbox(centralizar_vertical(caixa_prints, 3) + (10, 0, -10, 0),
                      "Prints da execução no Airflow: ver Anexo B (páginas 3 e 4).\n"
                      "DAG etl_apoio_escolar_periferico com as 3 tarefas em \"success\", logs da transformação\n"
                      "e da carga ({'atualizadas': 4}) e as escolas priorizadas no painel /impacto do MVP.",
                      fontname="helv", fontsize=10, color=CINZA, align=fitz.TEXT_ALIGN_CENTER)

    # Anexo A + início do Anexo B
    p3 = doc.new_page(width=W, height=H)
    y = titulo(p3, 50, "Anexo A. Diagrama de Arquitetura do Pipeline")
    y = imagem(p3, y, "00_diagrama_pipeline.png",
               "Fluxo de ponta a ponta: a DAG roda diariamente no Airflow, grava as camadas Raw e Trusted em CSV e "
               "envia a priorização ao núcleo do MVP pela API (PUT /api/v1/escolas/prioridade, com X-API-Key).")
    y = titulo(p3, y + 6, "Anexo B. Evidências de Execução")
    y = imagem(p3, y, "01_airflow_grid.png",
               "B1. Airflow 2.10.5 (Docker): execução manual da DAG etl_apoio_escolar_periferico em 15/11/2026, status "
               "success, com as tarefas extract_inep_ibge, transform_data e load_to_azure concluídas (quadrados verdes).")

    p4 = doc.new_page(width=W, height=H)
    y = 50
    y = imagem(p4, y, "02_airflow_graph.png", "B2. Visão Graph: dependências extract -> transform -> load, todas em success.")
    y = imagem(p4, y, "04_airflow_log_transform.png",
               "B3. Log de transform_data: camada Trusted com as 4 escolas do recorte periférico, ordenadas pelo Índice "
               "de Prioridade Educacional (IDEB faltante imputado pela média do recorte).")
    y = imagem(p4, y, "03_airflow_log_load.png",
               "B4. Log de load_to_azure: o núcleo do MVP confirmou a carga ({'atualizadas': 4}).")
    y = imagem(p4, y, "05_mvp_impacto.png",
               "B5. Dados carregados no MVP: painel /impacto com o índice (normalizado de 0 a 1) e a origem "
               "\"Pipeline INEP/IBGE\" das escolas atualizadas. Escolas fictícias; MVP rodando local para a evidência.")

    total = len(doc)
    for i, page in enumerate(doc):
        rodape = fitz.Rect(470, 805, 545, 820)
        if i < 2:
            page.add_redact_annot(rodape, fill=(1, 1, 1))
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE)
        else:
            page.insert_text((MARGEM, 816), "MVP: Apoio Escolar Periférico", fontname="helv", fontsize=8.5, color=CINZA)
        page.insert_textbox(rodape, f"Page {i + 1} of {total}", fontname="helv", fontsize=8.5, color=CINZA, align=fitz.TEXT_ALIGN_RIGHT)

    doc.save(SAIDA, garbage=3, deflate=True)
    print(f"PDF: {SAIDA} ({total} páginas)")


if __name__ == "__main__":
    main()

"""Monta o PDF de Big Data com o diagrama e os prints do Airflow.

Entrada: o PDF original do Jó (dados/Entrega_BigData_ApoioEscolar.pdf), sem alterar.
Saída:   dados/Entrega_BigData_ApoioEscolar_com_evidencias.pdf

- As duas caixas "Substitua esta caixa..." da página 2: a do diagrama recebe o próprio
  diagrama (Figura 1), e a seção 4 (evidências) passa para o topo da página 3.
- Anexos novos: A (diagrama de arquitetura) e B (prints da execução no Airflow e
  do resultado no MVP), a partir das imagens em evidencias/recortes/.
- O rodapé "Page X of Y" é refeito com o novo total de páginas.
- Trechos do original que não batiam com o pipeline são reescritos (ver CORRECOES):
  a linha do RPA e os links da ficha (pág. 1), a etapa Load e o dicionário de
  dados (pág. 2). O dicionário passa a descrever as tabelas que o pipeline
  realmente entrega (Raw, Trusted e a tabela `escolas` do MVP); o modelo
  dimensional do Jó fica citado como modelo-alvo para os dados reais.

Uso (na pasta dados/): .venv/Scripts/python evidencias/montar_pdf.py
Requer: pymupdf.
"""
import os
from pathlib import Path

import pymupdf as fitz

BASE = Path(__file__).resolve().parent
ENTRADA = BASE.parent / "Entrega_BigData_ApoioEscolar.pdf"
SAIDA = BASE.parent / "Entrega_BigData_ApoioEscolar_com_evidencias.pdf"
REC = BASE / "recortes"

URL_REPOSITORIO = "https://github.com/GiantMazelliWasHere/apoio-escolar-periferico"
# URL pública do App Service (Azure), a mesma do README principal. Para trocar:
#   set URL_MVP=https://app-apoioescolar-xxxx.azurewebsites.net
URL_MVP = os.environ.get("URL_MVP", "https://app-apoioescolar-mvp-6e7462.azurewebsites.net").strip()

CSS = """
* { font-family: sans-serif; color: #1E293B; }
body { font-size: 10.5px; line-height: 1.45; }
b { font-weight: bold; }
code { font-family: monospace; font-size: 8.5px; }
h2 { font-size: 14px; font-weight: bold; margin: 0 0 3px 0; padding-bottom: 4px; border-bottom: 1.5px solid #E91E63; }
h3 { font-size: 10px; font-weight: bold; margin: 6px 0 2px 0; }
p { margin: 0 0 3px 0; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 0.5px solid #CBD5E1; padding: 1px 5px; font-size: 8.5px; line-height: 1.3; text-align: left; vertical-align: top; }
th { background-color: #F1F5F9; font-weight: bold; }
.nota { font-size: 8.5px; color: #64748B; }
"""

CINZA = (0x64 / 255, 0x74 / 255, 0x8B / 255)
ESCURO = (0x0F / 255, 0x17 / 255, 0x2A / 255)
FUNDO_CAIXA = (0.9725, 0.9804, 0.9882)
MARGEM = 51
# Onde começa o dicionário de dados na página 2, logo abaixo do diagrama (Figura 1).
INICIO_DICIONARIO = 318
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


def reescrever(page: fitz.Page, rect: fitz.Rect, html: str, apagar_graficos: bool = False) -> None:
    """Apaga o trecho do original e escreve o texto corrigido no mesmo lugar."""
    page.add_redact_annot(rect, fill=(1, 1, 1))
    graficos = fitz.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED if apagar_graficos else fitz.PDF_REDACT_LINE_ART_NONE
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=graficos)
    sobra, escala = page.insert_htmlbox(rect, html, css=CSS, scale_low=1)
    if sobra < 0:
        raise RuntimeError(f"Texto não coube na página {page.number + 1} em {rect}")


def linha_dicionario(coluna: str, tipo: str, chave: str, descricao: str) -> str:
    return f"<tr><td>{coluna}</td><td>{tipo}</td><td>{chave}</td><td>{descricao}</td></tr>"


def tabela(titulo_tabela: str, linhas: list[tuple[str, str, str, str]]) -> str:
    corpo = "".join(linha_dicionario(*linha) for linha in linhas)
    return (f"<h3>{titulo_tabela}</h3><table><tr><th>Coluna</th><th>Tipo</th><th>Chave</th>"
            f"<th>Descrição / Transformação</th></tr>{corpo}</table>")


def corrigir_pagina1(p1: fitz.Page) -> None:
    # Mesmo corpo do original (11,25 pt), para a linha reescrita não destoar das vizinhas.
    estilo = "style='font-size:11.25px; line-height:1.45; margin:0'"
    reescrever(p1, fitz.Rect(80.5, 417.5, 544, 435),
               f"<p {estilo}><b>Automação:</b> RPA UiPath que credencia voluntários no portal SICREV e envia os boletins.</p>")
    url_mvp = URL_MVP or "[URL do App Service: gerar o PDF com URL_MVP definida]"
    reescrever(p1, fitz.Rect(64.5, 550.5, 544, 586),
               f"<p {estilo}><b>URL do MVP e repositório:</b> {url_mvp}<br>{URL_REPOSITORIO}</p>")


def corrigir_pagina2(p2: fitz.Page) -> None:
    reescrever(p2, fitz.Rect(66, 111, 544, 158),
               "<p><b>Load:</b> a camada Trusted (só escolas de região periférica) é enviada ao núcleo do MVP pela "
               "API <code>PUT /api/v1/escolas/prioridade</code> (com <code>X-API-Key</code>), que grava o índice na "
               "tabela <code>escolas</code> do banco da aplicação e alimenta o painel <code>/impacto</code>.</p>")

    raw = [
        ("cod_municipio", "INT", "-", "Código IBGE do município (7 dígitos)."),
        ("cod_escola", "INT", "PK", "Código INEP da escola. Fictício, com prefixo 99, para nunca coincidir com uma escola real."),
        ("nome_escola", "VARCHAR", "-", "Nome da escola (fictício)."),
        ("regiao_periferica", "INT", "-", "1 = região periférica, 0 = não. Define o recorte da camada Trusted."),
        ("ideb_anos_finais", "FLOAT", "-", "IDEB dos anos finais do fundamental. Pode vir vazio (dado faltante simulado)."),
        ("qtd_alunos", "INT", "-", "Matrículas da escola (Censo Escolar). Não segue para a Trusted."),
        ("lab_informatica", "INT", "-", "1 = tem laboratório de informática, 0 = não."),
        ("acesso_internet", "INT", "-", "1 = tem internet, 0 = não."),
    ]
    trusted = [
        ("cod_municipio", "INT", "-", "Copiado da Raw."),
        ("cod_escola", "INT", "PK", "Copiado da Raw."),
        ("nome_escola", "VARCHAR", "-", "Copiado da Raw."),
        ("ideb_anos_finais", "FLOAT", "-", "IDEB faltante imputado pela média das escolas do recorte periférico."),
        ("indice_prioridade", "FLOAT", "-", "Índice de Prioridade Educacional, de 0 a 14: (10 - IDEB) + 2 se não tem "
         "laboratório + 2 se não tem internet. Quanto maior, mais prioritária. A tabela sai ordenada por ele."),
    ]
    mvp = [
        ("codigo_inep", "VARCHAR(20)", "busca", "Recebe cod_escola. É por ele que o núcleo encontra a escola; "
         "códigos que não existem no núcleo são ignorados."),
        ("territorio_prioritario", "BOOLEAN", "-", "true para toda escola da Trusted (região periférica)."),
        ("indice_prioridade", "FLOAT", "-", "indice_prioridade da Trusted dividido por 14 (de 0 a 1)."),
        ("fonte_prioridade", "VARCHAR(40)", "-", "Passa de \"sintetico\" (seed) para \"pipeline\" quando a carga grava a escola."),
    ]
    html = (
        "<h2>3. Dicionário de Dados</h2>"
        "<p>O pipeline grava duas camadas em CSV e carrega o resultado no banco do MVP. Todos os dados são "
        "sintéticos: escolas fictícias, sem nenhum dado pessoal.</p>"
        + tabela("Camada Raw: <code>raw_inep_ibge.csv</code> (extract_inep_ibge)", raw)
        + tabela("Camada Trusted: <code>trusted_escolas_prioritarias.csv</code> (transform_data)", trusted)
        + tabela("MVP: tabela <code>escolas</code>, colunas gravadas pela carga (load_to_azure)", mvp)
        + "<p class='nota'>Modelo-alvo para os microdados reais do INEP/IBGE: dimensão <code>dim_municipios_ibge</code> "
        "(cod_municipio_ibge, nome_municipio, uf) e fato <code>fact_escolas_vulnerabilidade</code>, ligadas pelo código "
        "do município. Ainda não implementado no protótipo.</p>"
    )
    reescrever(p2, fitz.Rect(51, INICIO_DICIONARIO, 545, 790), html, apagar_graficos=True)


def main() -> None:
    doc = fitz.open(ENTRADA)
    corrigir_pagina1(doc[0])
    p2 = doc[1]
    W, H = p2.rect.width, p2.rect.height
    corrigir_pagina2(p2)

    # A caixa tracejada do original vira o próprio diagrama, em vez de só apontar para o anexo.
    p2.add_redact_annot(fitz.Rect(51, 160, 545, INICIO_DICIONARIO), fill=(1, 1, 1))
    p2.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED)
    y = imagem(p2, 164, "00_diagrama_pipeline.png",
               "Figura 1. Diagrama de arquitetura do pipeline: Origem INEP/IBGE -> Airflow (extract -> transform -> "
               "load) -> API do MVP -> painel /impacto. Detalhes no Anexo A (página 3).")
    if y > INICIO_DICIONARIO + 2:
        raise RuntimeError(f"O diagrama da página 2 invadiu o dicionário (y = {y:.0f})")

    # Seção 4, Anexo A e início do Anexo B
    p3 = doc.new_page(width=W, height=H)
    sobra, _ = p3.insert_htmlbox(
        fitz.Rect(MARGEM, 50, MARGEM + LARGURA, 130),
        "<h2>4. Evidências de Execução</h2>"
        "<p>O pipeline rodou de ponta a ponta no Airflow e os dados carregados aparecem no painel <code>/impacto</code> "
        "do MVP. Prints da DAG, dos logs e do painel no Anexo B (páginas 3 e 4).</p>",
        css=CSS, scale_low=1)
    if sobra < 0:
        raise RuntimeError("A seção 4 não coube no topo da página 3")
    y = titulo(p3, 130 - sobra + 8, "Anexo A. Diagrama de Arquitetura do Pipeline")
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
            # O rodapé do original ("Page X of 2") não fica na mesma altura nas duas páginas.
            antigo = page.search_for(f"Page {i + 1} of 2")
            if antigo:
                rodape = fitz.Rect(470, antigo[0].y0 - 2.5, 545, antigo[0].y0 + 14)
            page.add_redact_annot(rodape, fill=(1, 1, 1))
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE)
        else:
            page.insert_text((MARGEM, 816), "MVP: Apoio Escolar Periférico", fontname="helv", fontsize=8.5, color=CINZA)
        page.insert_textbox(rodape, f"Page {i + 1} of {total}", fontname="helv", fontsize=8.5, color=CINZA, align=fitz.TEXT_ALIGN_RIGHT)

    doc.save(SAIDA, garbage=3, deflate=True)
    print(f"PDF: {SAIDA} ({total} páginas)")


if __name__ == "__main__":
    main()

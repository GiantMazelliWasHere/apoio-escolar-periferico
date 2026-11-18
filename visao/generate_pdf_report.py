"""
Gera o PDF de entrega de Applied Computer Vision (Prof. Wilians Douglas Conde Souza, slide 36, 14 pontos).

As métricas da seção 6 não são digitadas aqui: vêm de resultados/metricas.json, gerado por
avaliar_dataset.py (EasyOCR de verdade sobre as 15 contas sintéticas e as 15 fotos simuladas).

Uso (na pasta visao/): python generate_pdf_report.py    Requer: reportlab.
"""
import json
import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

BASE = Path(__file__).resolve().parent
PDF = BASE / "Relatorio_Tecnico_Visao_Computacional_BitsNBytes.pdf"
METRICAS = BASE / "resultados" / "metricas.json"

PRODUTO = "Apoio Escolar Periférico"
URL_REPOSITORIO = "https://github.com/GiantMazelliWasHere/apoio-escolar-periferico"
URL_MVP = "https://app-apoioescolar-mvp-6e7462.azurewebsites.net"
CAMPOS = [("empresa", "Empresa (concessionária)"), ("cep", "CEP"), ("numero", "Número"),
          ("bairro", "Bairro"), ("logradouro", "Logradouro"), ("uf", "UF")]
EMPRESAS = ("ENEL", "SABESP", "CLARO")


def build_pdf():
    m = json.loads(METRICAS.read_text(encoding="utf-8"))
    plana, foto = m["cenarios"]["plana"], m["cenarios"]["foto"]

    doc = SimpleDocTemplate(str(PDF), pagesize=A4, rightMargin=1.8 * cm, leftMargin=1.8 * cm,
                            topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                            title="Relatório Técnico: Extração Automática de Endereços", author="Equipe Bits N' Bytes")
    styles = getSampleStyleSheet()
    primary_color = colors.HexColor("#1A365D")
    secondary_color = colors.HexColor("#2B6CB0")
    dark_text = colors.HexColor("#2D3748")
    light_bg = colors.HexColor("#EDF2F7")

    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=20,
                                 leading=24, textColor=primary_color, alignment=1, spaceAfter=6)
    subtitle_style = ParagraphStyle('DocSubTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12,
                                    leading=16, textColor=secondary_color, alignment=1, spaceAfter=12)
    h1_style = ParagraphStyle('SectionH1', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=13,
                              leading=17, textColor=primary_color, spaceBefore=12, spaceAfter=6, keepWithNext=True)
    body_style = ParagraphStyle('DocBody', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5,
                                leading=13.5, textColor=dark_text, spaceAfter=6)
    bullet_style = ParagraphStyle('DocBullet', parent=body_style, leftIndent=14, firstLineIndent=-10, spaceAfter=4)
    cell_style = ParagraphStyle('Cell', parent=body_style, fontSize=8, leading=10.5, spaceAfter=0)
    code_style = ParagraphStyle('DocCode', parent=styles['Code'], fontName='Courier', fontSize=8, leading=10.5,
                                textColor=colors.HexColor("#1A202C"), backColor=colors.HexColor("#F7FAFC"), spaceAfter=6)

    def tabela(dados, larguras):
        t = Table([[Paragraph(str(c), cell_style) for c in linha] for linha in dados], colWidths=larguras, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), light_bg),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        return t

    def frac(r, k):
        return f"{r[k]}/{r['total']}"

    def pct(r, k):
        return f"{100 * r[k] / r['total']:.0f}% ({r[k]}/{r['total']})"

    story = []
    story.append(Paragraph("FIAP — GLOBAL SOLUTION 2026.2", ParagraphStyle('TopHeader', fontName='Helvetica-Bold', fontSize=10, textColor=secondary_color, alignment=1)))
    story.append(Paragraph("DISCIPLINA: APPLIED COMPUTER VISION", ParagraphStyle('TopSub', fontName='Helvetica', fontSize=9, textColor=colors.gray, alignment=1)))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Relatório Técnico: Extração Automática de Endereços", title_style))
    story.append(Paragraph(f"MVP CitizenTech: {PRODUTO} | ODS 4 e 10", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=secondary_color, spaceAfter=10))

    info = Table([[
        Paragraph("<b>Professor:</b> Wilians Douglas Conde Souza<br/><b>Turma:</b> Engenharia de Software 4ESPR<br/>"
                  f"<b>MVP:</b> {URL_MVP}<br/><b>Repositório:</b> {URL_REPOSITORIO} (pasta <font face='Courier'>visao/</font>)", body_style),
        Paragraph("<b>Equipe: Bits N’ Bytes</b><br/>• Jó Sales — RM 552679<br/>• Miguel Garcez de Carvalho — RM 553768<br/>• Vinicius Souza e Silva — RM 552781<br/>• Edson Leonardo — RM 553737<br/>• Eduardo Mazelli — RM 553236", body_style),
    ]], colWidths=[10 * cm, 7 * cm])
    info.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), light_bg), ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E0")),
                              ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('PADDING', (0, 0), (-1, -1), 8)]))
    story.append(info)
    story.append(Spacer(1, 6))

    # 1. Papel no MVP
    story.append(Paragraph("1. Conceito da Atividade e Papel no MVP", h1_style))
    story.append(Paragraph(
        f"O <b>{PRODUTO}</b> conecta estudantes de escolas públicas da periferia a monitorias voluntárias. No cadastro, o "
        "estudante pode informar bairro e CEP, que localizam onde ele mora. Digitar endereço no celular "
        "gera erro e desistência, então o cadastro aceita a <b>foto de uma conta de consumo</b> de três concessionárias "
        "(<b>Enel, Sabesp e Claro</b>): o componente de Visão identifica a empresa, corrige a perspectiva, lê o endereço por "
        "OCR, separa o endereço do cliente do endereço da sede e devolve os campos para o estudante <b>conferir e corrigir</b> "
        "antes de enviar.", body_style))

    # 2. Rubrica → onde está
    story.append(Paragraph("2. Rubrica (14 pontos) e onde cada item está no repositório", h1_style))
    story.append(tabela([
        ["Critério", "Pts", "O que foi feito", "Onde está"],
        ["Processamento", "3", "Cantos do papel (Canny + aproximação poligonal), correção de perspectiva (warpPerspective), "
         "ampliação para OCR, recorte de regiões, filtro bilateral + Otsu como 2ª tentativa.", "mvp/app/visao.py, visao/scanner.py"],
        ["Extração", "4", "Identificação da concessionária, OCR (EasyOCR) e regras que descartam o endereço e o CEP das sedes.",
         "mvp/app/visao.py, visao/ocr_engine.py"],
        ["Integração", "3", "API POST /api/v1/visao/endereco chamada pela tela de cadastro, que pré-preenche bairro e CEP para conferência.",
         "mvp/app/main.py, cadastro_estudante.html"],
        ["Testes", "3", "Gabarito das 15 contas, 15 fotos simuladas, medição com OCR real (seção 6) e testes automáticos no CI.",
         "visao/avaliar_dataset.py, mvp/tests/test_visao.py, visao/test_cv.py"],
        ["Documentação", "1", "Este relatório, o README de visao/ e o contrato em docs/INTEGRACAO.md.", "visao/README.md"],
    ], [2.6 * cm, 1 * cm, 8.6 * cm, 4.8 * cm]))

    # 3. Pipeline
    story.append(Paragraph("3. Técnicas: o pipeline", h1_style))
    story.append(Paragraph("O núcleo do MVP roda o pipeline da entrega (código em <font face='Courier'>mvp/app/visao.py</font>), "
                           "tudo em memória:", body_style))
    for item in [
        "<b>Entrada:</b> foto JPG, PNG ou WebP ou a 1ª página de um PDF (pypdfium2), com no máximo 8 MB; o maior lado é limitado a 3000 px.",
        "<b>Cantos do papel:</b> a foto é reduzida para 600 px de altura, convertida para cinza, suavizada (Gaussiano 5×5) e passa pelo "
        "detector de bordas Canny (limiares 75 e 200). Dos 5 maiores contornos, o primeiro que a aproximação poligonal de "
        "Douglas-Peucker (<font face='Courier'>approxPolyDP</font>, epsilon = 2% do perímetro) reduz a 4 vértices e que cobre pelo menos 15% da "
        "imagem é o papel. Sem quadrilátero, a foto inteira é usada.",
        "<b>Correção de perspectiva:</b> os vértices são ordenados (soma e diferença das coordenadas), e "
        "<font face='Courier'>getPerspectiveTransform</font> + <font face='Courier'>warpPerspective</font> planificam o papel no tamanho dos seus lados.",
        "<b>Pré-processamento para OCR:</b> o papel corrigido é redimensionado para 2400 px de largura (a letra miúda da conta fica com ~20 px). "
        "São recortados o cabeçalho (0–22% da altura, para a empresa) e a região do endereço do cliente (10–55% da altura).",
        "<b>OCR:</b> EasyOCR (detector CRAFT + reconhecedor CRNN, modelos pt e en, em CPU). Se a região não tiver CEP nem logradouro, a página "
        "inteira é binarizada (filtro bilateral + limiar de Otsu) e lida de novo.",
        "<b>Extração dos campos:</b> expressões regulares para logradouro e número (aceitando leituras erradas do “Nº”, como NE ou NI, "
        "e o O trocado por 0), bairro (rótulo “BAIRRO:” ou linha abaixo do logradouro), CEP no formato 00000-000 e UF.",
    ]:
        story.append(Paragraph("• " + item, bullet_style))

    # 4. Segregação
    story.append(Paragraph("4. Endereço do cliente × endereço da concessionária", h1_style))
    story.append(Paragraph("As três contas trazem o endereço da sede da empresa. O pipeline evita confundi-lo com o do estudante assim:", body_style))
    for item in [
        "<b>Região:</b> o endereço do cliente é lido na faixa de 10–55% da altura; o rodapé institucional fica de fora.",
        "<b>CEPs das sedes ignorados:</b> 04794-000 (Enel, Av. das Nações Unidas), 05429-900 (Sabesp, R. Costa Carvalho) e 04711-130 (Claro, R. Henri Dunant).",
        "<b>Contexto do logradouro:</b> um “RUA/AV ... número” é descartado se aparece perto de palavras como SEDE, CORPORATIVA, NAÇÕES UNIDAS, CNPJ, FATURA ou NOTA FISCAL.",
        "<b>Bairro por layout:</b> Enel tem o rótulo “BAIRRO:”; na Sabesp (“BAIRRO - CIDADE/UF”) e na Claro (envelope postal) o bairro é a linha abaixo do logradouro.",
    ]:
        story.append(Paragraph("• " + item, bullet_style))

    # 5. Dataset
    story.append(Paragraph("5. Documentos sintéticos de teste com gabarito (LGPD)", h1_style))
    for item in [
        "<b>15 contas sintéticas</b> (5 Enel, 5 Sabesp, 5 Claro) geradas por <font face='Courier'>generate_dataset.py</font>, com nomes e endereços "
        "fictícios (Faker), em <font face='Courier'>visao/dataset_sintetico/</font>.",
        "<b>Gabarito:</b> <font face='Courier'>ground_truth.json</font> com empresa, logradouro, número, bairro, cidade, UF e CEP de cada conta.",
        "<b>15 fotos simuladas</b>, geradas por <font face='Courier'>avaliar_dataset.py</font> em <font face='Courier'>dataset_sintetico/fotos_simuladas/</font> "
        "(sempre iguais, com semente fixa; fora do git por tamanho): a mesma conta em resolução de celular, inclinada sobre uma mesa "
        "escura, com sombra lateral, desfoque, ruído e compressão JPEG.",
        "<b>Sem dados reais:</b> nenhuma conta real está no repositório (o <font face='Courier'>.gitignore</font> bloqueia boletos e faturas reais), e "
        "o MVP não grava a imagem: só o bairro e o CEP que o estudante confirmar.",
    ]:
        story.append(Paragraph("• " + item, bullet_style))

    # 6. Métricas
    story.append(Paragraph("6. Métricas (medidas com EasyOCR real)", h1_style))
    story.append(Paragraph(
        f"Acerto por campo contra o gabarito, comparando sem acento, caixa e pontuação. Medido em {m['data']} por "
        f"<font face='Courier'>avaliar_dataset.py</font>, num PC comum (CPU AMD, sem GPU). Resultado completo, conta por conta, em "
        "<font face='Courier'>visao/resultados/metricas.md</font>.", body_style))
    linhas = [["Campo", "Imagem plana", "Foto simulada"]]
    for k, nome in CAMPOS:
        linhas.append([nome, pct(plana["geral"], k), pct(foto["geral"], k)])
    linhas.append(["Endereço completo certo (logradouro, número, bairro e CEP)",
                   f"{plana['contas_com_endereco_completo']}/15", f"{foto['contas_com_endereco_completo']}/15"])
    linhas.append(["Tempo médio por conta (CPU)", f"{plana['tempo_medio_s']:.1f} s".replace(".", ","), f"{foto['tempo_medio_s']:.1f} s".replace(".", ",")])
    story.append(tabela(linhas, [8 * cm, 4.5 * cm, 4.5 * cm]))
    story.append(Spacer(1, 6))
    por_empresa = [["Campo"] + [f"{e.title()} plana" for e in EMPRESAS] + [f"{e.title()} foto" for e in EMPRESAS]]
    for k, nome in CAMPOS:
        por_empresa.append([nome] + [frac(plana["por_empresa"][e], k) for e in EMPRESAS] + [frac(foto["por_empresa"][e], k) for e in EMPRESAS])
    story.append(KeepTogether([tabela(por_empresa, [4.4 * cm] + [2.1 * cm] * 6)]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<b>Logradouro:</b> o gerador imprime o tipo duas vezes (“AVENIDA RUA BOA VISTA” para o gabarito “RUA BOA VISTA”), por isso a "
        "comparação ignora as palavras de tipo do começo. Os erros que sobram são palavras coladas ou letras trocadas pelo OCR "
        "(“RUADOSPALHARES”). <b>Testes automáticos:</b> as regras de extração, a geometria e a API (formatos, limites, CSRF, OCR ausente ou com "
        "falha) são testadas com OCR simulado no CI a cada pull request.", body_style))

    # 7. Limitações
    story.append(Paragraph("7. Limitações", h1_style))
    for item in [
        "<b>Logradouro e bairro erram mais que CEP e número:</b> o OCR cola palavras (“RUABOAVISTA”) e troca letras (“CAPPOREDONDO”), e "
        "a foto inclinada com sombra derruba ainda mais o acerto do número. Por isso o MVP usa só bairro e CEP, e sempre como sugestão: "
        "a tela mostra o que foi lido e o estudante confere ou digita.",
        f"<b>Lento em CPU:</b> cerca de {round((plana['tempo_medio_s'] + foto['tempo_medio_s']) / 2):.0f} s por conta, porque o EasyOCR lê duas ou três regiões. "
        "O núcleo limita a 6 leituras por minuto por cliente e 120 por hora no total.",
        "<b>Desligado na URL pública:</b> o EasyOCR com PyTorch precisa de ~1 GB de disco e mais RAM do que o plano B1 do App Service (1,75 GB). "
        "No ar, a tela de cadastro pede bairro e CEP digitados; a leitura da foto roda no MVP local com "
        "<font face='Courier'>mvp/requirements-visao.txt</font> instalado.",
        "<b>Layouts fixos:</b> as regiões e as regras valem para os modelos de conta das três empresas; outro layout ou outra empresa "
        "precisa de ajuste. Papel dobrado ou com canto fora da foto cai no modo “foto inteira”, sem correção de perspectiva.",
        "<b>Avaliado só com dados sintéticos:</b> 15 contas e 15 fotos simuladas. Contas reais variam mais (papel amassado, flash, carimbos).",
    ]:
        story.append(Paragraph("• " + item, bullet_style))

    # 8. Integração
    story.append(Paragraph("8. Utilização do endereço no MVP", h1_style))
    story.append(Paragraph(
        "Na tela <font face='Courier'>/cadastro/estudante</font>, o botão “Tirar foto ou escolher arquivo” envia a imagem para "
        "<font face='Courier'>POST /api/v1/visao/endereco</font> (multipart, campo <font face='Courier'>arquivo</font>, com o token CSRF da sessão). "
        "A resposta traz os campos lidos e a confiança (fração dos 4 campos de endereço encontrados):", body_style))
    exemplo = next((l for l in m["detalhe"]["plana"] if all(l["acertos"].values())), m["detalhe"]["plana"][0])
    lido = exemplo["lido"]
    encontrados = sum(1 for k in ("logradouro", "numero", "bairro", "cep") if lido.get(k))
    json_exemplo = json.dumps({**{k: lido.get(k) for k in ("logradouro", "numero", "bairro", "cep", "uf")}, "empresa": lido.get("empresa"),
                               "confianca": round(encontrados / 4, 2), "fonte": "ocr"}, ensure_ascii=False, indent=2)
    story.append(Paragraph(f"<pre>{json_exemplo}</pre>", code_style))
    for item in [
        "A tela pré-preenche <b>bairro e CEP</b> e mostra a empresa e o endereço lido; o estudante confere, corrige e só então envia o cadastro.",
        "O núcleo valida o CEP (8 dígitos) e grava só bairro e CEP no cadastro do estudante (ambos opcionais). "
        "A imagem, o logradouro e o número não são guardados.",
        "Erros viram mensagens simples: arquivo acima de 8 MB (413), formato não aceito (415), arquivo ilegível (422), excesso de leituras (429). "
        "Sem OCR instalado, <font face='Courier'>fonte</font> vem <font face='Courier'>indisponivel</font> e a tela esconde o botão da foto.",
    ]:
        story.append(Paragraph("• " + item, bullet_style))

    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E0"), spaceAfter=6))
    story.append(Paragraph(f"FIAP 2026.2 — Global Solution CitizenTech | Equipe Bits N’ Bytes (4ESPR) | {URL_REPOSITORIO}",
                           ParagraphStyle('FooterText', fontName='Helvetica-Oblique', fontSize=7.5, textColor=colors.gray, alignment=1)))

    doc.build(story)
    print(f"PDF gerado: {PDF}")


if __name__ == "__main__":
    build_pdf()

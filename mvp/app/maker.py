"""Integração com a peça do Maker Lab (suporte de tablet para estudo).

A peça física leva uma etiqueta com QR code. O QR aponta para `/qr` do MVP,
que marca a sessão com a origem "peca_maker" e leva à página inicial. Se a
pessoa se cadastrar nessa mesma visita, a conta guarda essa origem, e o painel
de impacto conta quantos cadastros vieram da peça (canal de aquisição local).

O QR é gerado pelo OpenCV (já usado pela Visão Computacional), sem dependência nova.
"""
from __future__ import annotations

import cv2

ORIGEM_MAKER = "peca_maker"
ORIGENS_VALIDAS = {ORIGEM_MAKER}
CAMINHO_QR = "/qr"

# Medidas da peça (de maker/cad/suporte_tablet.step), em milímetros.
PECA = {
    "nome": "Suporte de tablet para estudo",
    "placas_mm": "220 × 140",
    "espessura_mm": 3,
    "aba_mm": 27,
    "etiqueta_mm": 40,
}


def url_do_qr(base_url: str) -> str:
    """URL gravada no QR: a URL pública do MVP + `/qr`."""
    return base_url.rstrip("/") + CAMINHO_QR


def matriz_qr(texto: str) -> list[list[bool]]:
    """Módulos do QR (True = escuro), já com a margem de silêncio de 4 módulos."""
    img = cv2.QRCodeEncoder.create().encode(texto)
    if img is None or img.size == 0:
        raise ValueError("Não foi possível gerar o QR code.")
    return [[int(v) < 128 for v in linha] for linha in img]


def qr_svg(texto: str, tamanho_mm: int | None = None) -> str:
    """SVG vetorial do QR (bom para corte/gravação a laser e para imprimir em qualquer tamanho).

    Cada sequência de módulos escuros de uma linha vira um retângulo, para o arquivo ficar pequeno.
    """
    m = matriz_qr(texto)
    n = len(m)
    rets = []
    for y, linha in enumerate(m):
        x = 0
        while x < n:
            if linha[x]:
                ini = x
                while x < n and linha[x]:
                    x += 1
                rets.append(f'<rect x="{ini}" y="{y}" width="{x - ini}" height="1"/>')
            else:
                x += 1
    dims = f' width="{tamanho_mm}mm" height="{tamanho_mm}mm"' if tamanho_mm else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n} {n}"{dims} shape-rendering="crispEdges" role="img" aria-label="QR code para {texto}">'
        f'<rect width="{n}" height="{n}" fill="#fff"/><g fill="#000">{"".join(rets)}</g></svg>'
    )

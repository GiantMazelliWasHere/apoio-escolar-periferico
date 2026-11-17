"""Renderiza o STL da peça em PNG (perspectiva, lateral e frontal) para o README, o MVP e o PDF.

Usa numpy + OpenCV, que já estão no ambiente do MVP:

    mvp/.venv/Scripts/python maker/entrega/renderizar_stl.py

Desenho por ordem de profundidade (painter's algorithm) com sombreamento difuso e
supersampling 3x para suavizar as bordas. No STL: x = fundo (0–104 mm),
y = altura (0–125 mm), z = largura (0–110 mm); a frente da peça (encaixe do tablet) fica em x = 0.
"""
from __future__ import annotations

import struct
from pathlib import Path

import cv2
import numpy as np

MAKER = Path(__file__).resolve().parent.parent
STL = MAKER / "fabricacao" / "suporte_tablet_3DP-2026-004_revC_impressao.stl"
SAIDA = MAKER / "imagens"
COR = np.array([0xC9, 0x9A, 0x5B], float)  # BGR: azul-acinzentado do desenho técnico
FUNDO = (250, 248, 246)
SS = 3


def ler_stl(caminho: Path) -> np.ndarray:
    d = caminho.read_bytes()
    n = struct.unpack("<I", d[80:84])[0]
    reg = np.frombuffer(d[84 : 84 + 50 * n], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return reg["v"].reshape(-1, 3, 3).astype(float)


def girar(yaw: float, pitch: float) -> np.ndarray:
    a, b = np.radians(yaw), np.radians(pitch)
    ry = np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])
    rx = np.array([[1, 0, 0], [0, np.cos(b), -np.sin(b)], [0, np.sin(b), np.cos(b)]])
    return rx @ ry


def renderizar(tris: np.ndarray, yaw: float, pitch: float, largura: int, altura: int, perspectiva: bool) -> np.ndarray:
    centro = (tris.reshape(-1, 3).min(0) + tris.reshape(-1, 3).max(0)) / 2
    # Câmera: olhando para -z da câmera; a frente da peça (x = 0) fica voltada para a câmera com yaw = 90.
    p = (tris - centro) @ girar(yaw, pitch).T
    if perspectiva:
        dist = 420.0
        f = dist / (dist - p[..., 2:3])
        xy = p[..., :2] * f
    else:
        xy = p[..., :2].copy()
    W, H = largura * SS, altura * SS
    pts = xy.reshape(-1, 2)
    esc = 0.84 * min(W / np.ptp(pts[:, 0]), H / np.ptp(pts[:, 1]))
    meio = (pts.min(0) + pts.max(0)) / 2
    tela = np.empty_like(xy)
    tela[..., 0] = (xy[..., 0] - meio[0]) * esc + W / 2
    tela[..., 1] = H / 2 - (xy[..., 1] - meio[1]) * esc

    normais = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    normais /= np.linalg.norm(normais, axis=1, keepdims=True) + 1e-12
    luz = np.array([-0.35, 0.6, 0.72])
    luz /= np.linalg.norm(luz)
    brilho = 0.38 + 0.62 * np.abs(normais @ luz)  # malha fina: ilumina os dois lados igual

    img = np.full((H, W, 3), FUNDO, np.uint8)
    for i in np.argsort(p[..., 2].mean(1)):  # do mais distante para o mais próximo
        cor = tuple(int(c) for c in np.clip(COR * brilho[i], 0, 255))
        cv2.fillConvexPoly(img, np.round(tela[i]).astype(np.int32), cor, lineType=cv2.LINE_AA)
    return cv2.resize(img, (largura, altura), interpolation=cv2.INTER_AREA)


def main() -> None:
    tris = ler_stl(STL)
    vistas = {
        "render_perspectiva.png": (125, 20, 1200, 900, True),
        "render_lateral.png": (0, 0, 1000, 900, False),
        "render_frontal.png": (90, 0, 900, 1000, False),
    }
    SAIDA.mkdir(exist_ok=True)
    for nome, (yaw, pitch, w, h, persp) in vistas.items():
        cv2.imwrite(str(SAIDA / nome), renderizar(tris, yaw, pitch, w, h, persp))
        print("PNG:", (SAIDA / nome).relative_to(MAKER.parent))


if __name__ == "__main__":
    main()

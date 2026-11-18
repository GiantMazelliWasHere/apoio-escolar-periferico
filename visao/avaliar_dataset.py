"""Mede o acerto do pipeline de Visão nas 15 contas sintéticas, contra o gabarito.

Roda o mesmo leitor que o MVP usa (`mvp/app/visao.py`, com EasyOCR de verdade) em
dois cenários para cada conta de `dataset_sintetico/`:

- plana: a imagem gerada, como veio do gerador;
- foto: a conta em resolução de celular, torta sobre uma mesa escura, com sombra, desfoque e ruído, como
  uma foto de celular. Essas fotos são geradas aqui, de forma determinística, e
  ficam em `dataset_sintetico/fotos_simuladas/`.

Saída: `resultados/metricas.json` (lida por generate_pdf_report.py) e
`resultados/metricas.md`, com o acerto por campo e por empresa e o tempo médio.

Uso (na raiz do repositório, com o venv do MVP que tem o EasyOCR):
    mvp/.venv/Scripts/python visao/avaliar_dataset.py
Leva alguns minutos em CPU (o EasyOCR lê cada conta duas ou três vezes).
"""
from __future__ import annotations

import json
import platform
import sys
import time
import unicodedata
from datetime import date
from pathlib import Path

import cv2
import numpy as np

BASE = Path(__file__).resolve().parent
RAIZ = BASE.parent
sys.path.insert(0, str(RAIZ / "mvp"))

from app.visao import LeitorEndereco, criar_ocr_easyocr  # noqa: E402

DATASET = BASE / "dataset_sintetico"
FOTOS = DATASET / "fotos_simuladas"
SAIDA = BASE / "resultados"
CAMPOS = ("empresa", "logradouro", "numero", "bairro", "cep", "uf")
EMPRESAS = ("ENEL", "SABESP", "CLARO")


def normalizar(valor: str | None) -> str:
    """Compara sem acento, caixa, pontuação nem espaços repetidos ("Capão Redondo" == "CAPAO REDONDO")."""
    if not valor:
        return ""
    s = unicodedata.normalize("NFKD", str(valor)).encode("ascii", "ignore").decode().upper()
    s = "".join(c if c.isalnum() else " " for c in s)
    return " ".join(s.split())


TIPOS = {"RUA", "R", "AV", "AVENIDA", "ESTRADA", "ESTR", "ALAMEDA", "AL", "TRAVESSA", "TV", "PRACA"}


def sem_tipo(logradouro: str) -> str:
    """O gerador imprime o tipo duas vezes ("AVENIDA RUA BOA VISTA" para o gabarito "RUA BOA VISTA"),
    então o logradouro é comparado sem as palavras de tipo do começo."""
    palavras = logradouro.split()
    while palavras and palavras[0] in TIPOS:
        palavras.pop(0)
    return " ".join(palavras)


def simular_foto(imagem: np.ndarray, semente: int) -> np.ndarray:
    """Conta inclinada sobre mesa escura, com sombra e leve desfoque (parecido com foto de celular)."""
    rng = np.random.default_rng(semente)
    # Resolução de celular: a conta ocupa ~2500 px de largura (o PNG gerado tem 1240 px, com letra de ~11 px,
    # que o desfoque abaixo apagaria). O núcleo depois reduz a foto para no máximo 3000 px no maior lado.
    imagem = cv2.resize(imagem, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    h, w = imagem.shape[:2]
    margem = int(0.12 * max(h, w))
    lw, lh = w + 2 * margem, h + 2 * margem
    jitter = lambda: rng.uniform(-0.06, 0.06) * w  # noqa: E731
    destino = np.float32([
        [margem + jitter(), margem + jitter()],
        [margem + w + jitter(), margem + jitter()],
        [margem + w + jitter(), margem + h + jitter()],
        [margem + jitter(), margem + h + jitter()],
    ])
    origem = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    matriz = cv2.getPerspectiveTransform(origem, destino)
    mesa = np.full((lh, lw, 3), (38, 42, 48), np.uint8)
    foto = cv2.warpPerspective(imagem, matriz, (lw, lh), dst=mesa, borderMode=cv2.BORDER_TRANSPARENT)
    # Sombra suave num dos lados (iluminação não homogênea).
    grad = np.linspace(0.72, 1.0, lw, dtype=np.float32)
    if semente % 2:
        grad = grad[::-1]
    foto = np.clip(foto.astype(np.float32) * grad[None, :, None], 0, 255).astype(np.uint8)
    foto = cv2.GaussianBlur(foto, (3, 3), 0)
    ruido = rng.normal(0, 4, foto.shape).astype(np.float32)
    return np.clip(foto.astype(np.float32) + ruido, 0, 255).astype(np.uint8)


def comparar(lido: dict, esperado: dict, empresa: str) -> dict:
    alvo = {"empresa": empresa, **{k: esperado.get(k) for k in CAMPOS if k != "empresa"}}
    acertos = {k: normalizar(lido.get(k)) == normalizar(alvo[k]) for k in CAMPOS}
    acertos["logradouro"] = bool(lido.get("logradouro")) and sem_tipo(normalizar(lido["logradouro"])) == sem_tipo(normalizar(alvo["logradouro"]))
    return acertos


def resumir(linhas: list[dict]) -> dict:
    def taxa(filtro):
        sel = [l for l in linhas if filtro(l)]
        return {k: sum(l["acertos"][k] for l in sel) for k in CAMPOS} | {"total": len(sel)}

    return {
        "geral": taxa(lambda l: True),
        "por_empresa": {e: taxa(lambda l, e=e: l["empresa"] == e) for e in EMPRESAS},
        "tempo_medio_s": round(sum(l["tempo_s"] for l in linhas) / len(linhas), 1),
        "contas_com_endereco_completo": sum(all(l["acertos"][k] for k in ("logradouro", "numero", "bairro", "cep")) for l in linhas),
    }


def main() -> None:
    ocr = criar_ocr_easyocr()
    if ocr is None:
        sys.exit("EasyOCR não instalado: use o venv do MVP com mvp/requirements-visao.txt.")
    leitor = LeitorEndereco(ocr, por_minuto=10_000, por_hora_total=10_000)
    gabarito = json.loads((DATASET / "ground_truth.json").read_text(encoding="utf-8"))
    FOTOS.mkdir(exist_ok=True)
    SAIDA.mkdir(exist_ok=True)

    leitor.ler(cv2.imencode(".png", np.full((200, 200, 3), 255, np.uint8))[1].tobytes())  # carrega o modelo fora da medição

    resultados: dict[str, list[dict]] = {"plana": [], "foto": []}
    for i, item in enumerate(gabarito):
        imagem = cv2.imread(str(DATASET / item["file_name"]))
        foto = simular_foto(imagem, semente=i)
        cv2.imwrite(str(FOTOS / item["file_name"].replace(".png", ".jpg")), foto, [cv2.IMWRITE_JPEG_QUALITY, 88])
        for cenario, img in (("plana", imagem), ("foto", foto)):
            dados = cv2.imencode(".png" if cenario == "plana" else ".jpg", img)[1].tobytes()
            inicio = time.perf_counter()
            lido = leitor.ler(dados)
            tempo = time.perf_counter() - inicio
            acertos = comparar(lido, item["ground_truth"], item["company"])
            resultados[cenario].append({
                "arquivo": item["file_name"], "empresa": item["company"], "tempo_s": round(tempo, 2),
                "lido": {k: lido.get(k) for k in CAMPOS}, "acertos": acertos,
            })
            erros = [k for k, ok in acertos.items() if not ok]
            print(f"{cenario:5} {item['file_name']:14} {tempo:5.1f}s  erros: {', '.join(erros) or '-'}", flush=True)

    metricas = {
        "data": date.today().isoformat(),
        "maquina": f"{platform.processor() or platform.machine()} (CPU, sem GPU)",
        "ocr": "EasyOCR (pt, en)",
        "cenarios": {c: resumir(l) for c, l in resultados.items()},
        "detalhe": resultados,
    }
    (SAIDA / "metricas.json").write_text(json.dumps(metricas, ensure_ascii=False, indent=2), encoding="utf-8")

    nomes = {"empresa": "Empresa", "logradouro": "Logradouro", "numero": "Número", "bairro": "Bairro", "cep": "CEP", "uf": "UF"}
    md = [f"# Métricas da Visão Computacional ({metricas['data']})", "",
          f"Gerado por `avaliar_dataset.py` com {metricas['ocr']}, em {metricas['maquina']}.", ""]
    for cenario, titulo in (("plana", "Imagem plana"), ("foto", "Foto simulada (inclinada, sombra, desfoque)")):
        r = metricas["cenarios"][cenario]
        md += [f"## {titulo}", "", "| Campo | Geral | Enel | Sabesp | Claro |", "| :--- | :---: | :---: | :---: | :---: |"]
        for k in CAMPOS:
            md.append(f"| {nomes[k]} | {r['geral'][k]}/{r['geral']['total']} | "
                      + " | ".join(f"{r['por_empresa'][e][k]}/{r['por_empresa'][e]['total']}" for e in EMPRESAS) + " |")
        md += ["", f"Endereço completo certo (logradouro, número, bairro e CEP): {r['contas_com_endereco_completo']}/{r['geral']['total']}. "
               f"Tempo médio por conta: {r['tempo_medio_s']} s.", ""]
    (SAIDA / "metricas.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()

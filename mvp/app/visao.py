"""Visão Computacional: lê o endereço na foto de uma conta (Enel, Sabesp ou Claro).

Origem: entrega da disciplina Applied Computer Vision, copiada em `visao/`
(repositório EdLeo0708/Applied-Computer-Vision, commit 9cdac0e). O pipeline é o
mesmo da entrega:

1. decodifica a foto (JPG/PNG/WebP) ou a 1ª página do PDF, só em memória;
2. acha os 4 cantos do papel (Canny + aproximação poligonal) e corrige a
   perspectiva com `cv2.warpPerspective`;
3. recorta a região do cabeçalho (concessionária) e a do endereço do cliente;
4. OCR (EasyOCR) e regras por expressão regular que separam o endereço do
   cliente do endereço da sede da concessionária.

Nada é gravado em disco. O núcleo guarda só bairro e CEP, e só depois que o
estudante confere e envia o cadastro.

O OCR é opcional: sem o pacote `easyocr` (requirements-visao.txt), `ativo` fica
falso e a tela de cadastro continua funcionando com digitação manual.
"""
from __future__ import annotations

import logging
import re
import threading
import time
from collections import defaultdict, deque
from typing import Callable

import cv2
import numpy as np

log = logging.getLogger(__name__)

MAX_BYTES = 8 * 1024 * 1024  # 8 MB por arquivo
MAX_LADO = 3000  # px: limita a memória da foto recebida
LARGURA_OCR = 2400  # px: o papel corrigido é ampliado/reduzido para esta largura (letra pequena de conta → ~20 px)
TIPOS_ACEITOS = {"image/jpeg", "image/png", "image/webp", "application/pdf"}

EMPRESAS = {
    "ENEL": "Enel (energia)",
    "SABESP": "Sabesp (água)",
    "CLARO": "Claro (telefone/internet)",
}

# CEPs das sedes das concessionárias, que aparecem no cabeçalho das contas.
CEPS_CORPORATIVOS = {"04794-000", "05429-900", "04711-130"}

UFS = "AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO"

# Palavras que indicam que um "RUA/AV ... 123" não é o endereço do cliente.
IGNORAR_LOGRADOURO = (
    "PÁGINA", "PAGINA", "NOTA FISCAL", "SERIE", "SÉRIE", "FATURA", "EMISSAO", "EMISSÃO",
    "DATA", "CONSUMIDOR", "NAÇÕES UNIDAS", "NACOES UNIDAS", "NAÇOES", "NACÕES", "SEDE", "CORPORATIVA",
    "RESIDENCIAL", "CONVENCIONAL", "MONOFASICO", "LEITURA", "INFORMACOES", "INFORMAÇÕES",
    "FISCAIS", "ELETRICA", "ELÉTRICA", "TRIBUTÁRIA", "CNPJ",
)


class ArquivoInvalido(ValueError):
    """Arquivo que não é uma imagem/PDF legível (mensagem pode ir para o usuário)."""


class LimiteExcedido(Exception):
    pass


# ---------------- Geometria (scanner.py da entrega) ----------------

def ordenar_cantos(pts: np.ndarray) -> np.ndarray:
    """Ordena 4 vértices: superior-esquerdo, superior-direito, inferior-direito, inferior-esquerdo."""
    pts = np.asarray(pts, dtype="float32")
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1).ravel()
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def corrigir_perspectiva(imagem: np.ndarray, pts: np.ndarray) -> np.ndarray:
    """Planifica o papel fotografado inclinado (cv2.warpPerspective)."""
    tl, tr, br, bl = rect = ordenar_cantos(pts)
    largura = max(int(np.hypot(*(br - bl))), int(np.hypot(*(tr - tl))), 1)
    altura = max(int(np.hypot(*(tr - br))), int(np.hypot(*(tl - bl))), 1)
    destino = np.array([[0, 0], [largura - 1, 0], [largura - 1, altura - 1], [0, altura - 1]], dtype="float32")
    m = cv2.getPerspectiveTransform(rect, destino)
    return cv2.warpPerspective(imagem, m, (largura, altura))


def achar_cantos_do_papel(imagem: np.ndarray) -> np.ndarray:
    """Acha os 4 cantos do maior quadrilátero (≥ 15% da foto). Sem um, usa a foto inteira."""
    h, w = imagem.shape[:2]
    razao = h / 600.0
    pequena = cv2.resize(imagem, (max(int(w / razao), 1), 600))
    cinza = cv2.cvtColor(pequena, cv2.COLOR_BGR2GRAY)
    bordas = cv2.Canny(cv2.GaussianBlur(cinza, (5, 5), 0), 75, 200)
    contornos, _ = cv2.findContours(bordas, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    area_minima = pequena.shape[0] * pequena.shape[1] * 0.15
    for c in sorted(contornos, key=cv2.contourArea, reverse=True)[:5]:
        aprox = cv2.approxPolyDP(c, 0.02 * cv2.arcLength(c, True), True)
        if len(aprox) == 4 and cv2.contourArea(c) > area_minima:
            return (aprox.reshape(4, 2) * razao).astype("float32")
    return np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype="float32")


def binarizar(imagem: np.ndarray) -> np.ndarray:
    """Cinza + filtro bilateral + Otsu (pré-processamento da entrega)."""
    cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY) if imagem.ndim == 3 else imagem
    filtrada = cv2.bilateralFilter(cinza, d=9, sigmaColor=75, sigmaSpace=75)
    _, otsu = cv2.threshold(filtrada, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return otsu


# ---------------- Entrada ----------------

def carregar_imagem(dados: bytes) -> np.ndarray:
    """Decodifica foto ou a 1ª página de um PDF, em memória, e limita o maior lado a MAX_LADO."""
    if not dados:
        raise ArquivoInvalido("O arquivo está vazio.")
    if dados[:5] == b"%PDF-":
        try:
            import pypdfium2 as pdfium

            pdf = pdfium.PdfDocument(dados)
            try:
                if len(pdf) == 0:
                    raise ArquivoInvalido("O PDF não tem páginas.")
                pagina = pdf[0]
                largura_pt = max(pagina.get_width(), 1)
                escala = min(2.0, MAX_LADO / largura_pt)
                bitmap = pagina.render(scale=escala)
                img = np.ascontiguousarray(bitmap.to_numpy())  # sem Pillow: o pdfium já entrega BGR
                modo = bitmap.mode
            finally:
                pdf.close()
        except ArquivoInvalido:
            raise
        except Exception as e:  # PDF corrompido, protegido por senha etc.
            raise ArquivoInvalido("Não consegui abrir este PDF. Tente uma foto da conta.") from e
        if modo in ("BGRA", "BGRX"):
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        elif modo == "L":
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    else:
        img = cv2.imdecode(np.frombuffer(dados, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise ArquivoInvalido("Não consegui abrir a imagem. Envie uma foto JPG ou PNG, ou o PDF da conta.")
    h, w = img.shape[:2]
    if max(h, w) > MAX_LADO:
        f = MAX_LADO / max(h, w)
        img = cv2.resize(img, (max(int(w * f), 1), max(int(h * f), 1)), interpolation=cv2.INTER_AREA)
    return img


# ---------------- Texto → campos (ocr_engine.py da entrega) ----------------

def detectar_empresa(texto: str) -> str | None:
    t = texto.upper()
    if any(k in t for k in ("ENEL", "ELETROPAULO", "ENERGIA ELÉTRICA", "ENERGIA ELETRICA")):
        return "ENEL"
    if any(k in t for k in ("SABESP", "SANEAMENTO", "ÁGUA E ESGOTO", "AGUA E ESGOTO", "LIGAÇÃO DE ÁGUA", "LIGACAO DE AGUA")):
        return "SABESP"
    if any(k in t for k in ("CLARO", "EMBRATEL", "NET SERVIÇOS", "NET SERVICOS")):
        return "CLARO"
    return None


def _cep(texto: str) -> str | None:
    """Primeiro CEP que não é o de uma sede de concessionária, no formato 00000-000."""
    candidatos = [f"{a}-{b}" for a, b in re.findall(r"(?<!\d)(\d{5})\s*[-.\s]?\s*(\d{3})(?!\d)", texto)]
    for c in candidatos:
        if c not in CEPS_CORPORATIVOS:
            return c
    return None


_TIPOS_LOGRADOURO = {
    "R": "Rua", "RUA": "Rua", "AV": "Avenida", "AVENIDA": "Avenida", "ESTRADA": "Estrada", "ESTR": "Estrada",
    "ALAMEDA": "Alameda", "AL": "Alameda", "TRAVESSA": "Travessa", "TV": "Travessa", "PRACA": "Praça", "PRAÇA": "Praça",
}
_RE_LOGRADOURO = re.compile(
    r"\b(RUA|R\.|AVENIDA|AV\.?|ESTRADA|ESTR\.|ALAMEDA|AL\.|TRAVESSA|TV\.|PRA[CÇ]A)\s+"
    # "Nº" costuma sair do OCR como NO, NE, NU, NI, NA: aceita qualquer uma dessas leituras antes do número.
    r"([A-ZÀ-Ú0-9][A-ZÀ-Ú0-9 .'-]*?)\s*(?:,|\s)\s*(?:N[ÚU]MERO\s*|N[º°OEUIA.]?\s*)?(\d{1,5})(?![\d/.,]\d)"
)


def _titulo(s: str) -> str:
    minusculas = {"De", "Da", "Do", "Das", "Dos", "E"}
    palavras = [p.capitalize() for p in s.split()]
    return " ".join(p.lower() if i and p in minusculas else p for i, p in enumerate(palavras))


def _logradouro(texto: str) -> tuple[str | None, str | None]:
    for m in _RE_LOGRADOURO.finditer(texto):
        inicio = texto.rfind("  ", 0, m.start())  # contexto da mesma "linha" do OCR
        contexto = texto[max(0, inicio, m.start() - 40): m.end()]
        if any(p in contexto for p in IGNORAR_LOGRADOURO):
            continue
        tipo = _TIPOS_LOGRADOURO.get(m.group(1).rstrip(".").replace("Ç", "C"), m.group(1).title())
        nome = m.group(2).strip(" .-")
        if len(nome) < 2:
            continue
        # "AVENIDA RUA DOS PALMARES" → mantém o nome como está na conta
        return _titulo(f"{tipo} {nome}"), m.group(3)
    return None, None


_RE_BAIRRO_ROTULO = re.compile(r"\bBAIRRO\s*:?\s*([A-ZÀ-Ú][A-ZÀ-Ú0-9 .'-]{1,60}?)(?=\s{2}|\s*[-,]|\s+(?:MUNIC|CIDADE|CEP|S[ÃA]O PAULO)|$)")
_RE_BAIRRO_CIDADE = re.compile(r"([A-ZÀ-Ú][A-ZÀ-Ú0-9 .'-]{1,60}?)\s*[-–]\s*[A-ZÀ-Ú][A-ZÀ-Ú .'-]{2,40}?\s*/\s*(?:" + UFS + r")\b")


_RE_LINHA_LOGRADOURO = re.compile(r"^([A-ZÀ-Ú][A-ZÀ-Ú0-9 .,'-]{3,}?)[ ,]+(?:N[º°OE.]?\s*)?(\d{1,5})$")
_NAO_E_BAIRRO = ("NOME", "CEP", "CLIENTE", "ENDERE", "DESTINAT", "LIGA", "MUNIC", "PAULO", "CNPJ", "SEDE", "FATURA")


def _limpar_bairro(m: re.Match | None) -> str | None:
    if m is None:
        return None
    bairro = m.group(1).strip(" .-")
    # Fica com o trecho depois do último número (descarta "..., 141" que vem do logradouro).
    bairro = re.split(r"\d+\s*", bairro)[-1].strip(" .-,")
    if len(bairro) < 2 or any(bairro.startswith(p) for p in _NAO_E_BAIRRO):
        return None
    return _titulo(bairro)


def _linhas(texto: str) -> list[str]:
    """O OCR separa as linhas com dois espaços (ver criar_ocr_easyocr)."""
    return [linha.strip(" .,") for linha in re.split(r"\s{2,}", texto) if linha.strip(" .,")]


def _linha_do_logradouro(linhas: list[str]) -> int | None:
    """Índice da linha "LOGRADOURO, NÚMERO", mesmo quando o OCR junta as palavras ("RUADOSPALMARES 141")."""
    for i, linha in enumerate(linhas):
        if _RE_LINHA_LOGRADOURO.match(linha) and not any(p in linha for p in IGNORAR_LOGRADOURO):
            return i
    return None


def _bairro(texto: str, linhas: list[str]) -> str | None:
    # 1. Rótulo explícito: "BAIRRO: BRASILANDIA" (Enel).
    if bairro := _limpar_bairro(_RE_BAIRRO_ROTULO.search(texto)):
        return bairro
    # 2. Linha logo abaixo do logradouro: "GRAJAU" (Claro) ou "GRAJAU - SÃO PAULO/SP" (Sabesp).
    i = _linha_do_logradouro(linhas)
    if i is not None and i + 1 < len(linhas):
        prox = re.split(r"\s*[-–]\s*", linhas[i + 1])[0].strip(" .,-")
        if len(prox) >= 3 and not re.search(r"\d", prox) and not any(p in prox for p in _NAO_E_BAIRRO):
            return _titulo(prox)
    # 3. "BAIRRO - CIDADE/UF" em qualquer posição.
    return _limpar_bairro(_RE_BAIRRO_CIDADE.search(texto))


def _uf(texto: str) -> str | None:
    m = re.search(r"/\s*(" + UFS + r")\b", texto) or re.search(r"\b(" + UFS + r")\b(?=\s*(?:CEP|\d{5}))", texto)
    return m.group(1) if m else None


def extrair_campos(texto_endereco: str) -> dict:
    """Do texto lido na região do endereço, extrai logradouro, número, bairro, CEP e UF."""
    t = " " + re.sub(r"[\r\n]+", "  ", texto_endereco.upper()) + " "
    t = re.sub(r"(?<=\d)O(?=\d)", "0", t)  # "6O3" → "603": o OCR troca zero por O
    linhas = _linhas(t)
    logradouro, numero = _logradouro(t)
    if numero is None and (i := _linha_do_logradouro(linhas)) is not None:
        numero = _RE_LINHA_LOGRADOURO.match(linhas[i]).group(2)
    return {"logradouro": logradouro, "numero": numero, "bairro": _bairro(t, linhas), "cep": _cep(t), "uf": _uf(t)}


# ---------------- Leitor ----------------

Ocr = Callable[[np.ndarray], str]


def criar_ocr_easyocr() -> Ocr | None:
    """OCR da entrega (EasyOCR, CPU). O modelo carrega na 1ª leitura, não na subida do servidor."""
    import importlib.util

    if importlib.util.find_spec("easyocr") is None:  # só confere se está instalado: importar carrega o PyTorch
        return None
    trava = threading.Lock()
    leitor: list = []

    def ler(imagem: np.ndarray) -> str:
        with trava:  # o EasyOCR não é thread-safe e cada leitura já usa todos os núcleos
            if not leitor:
                import easyocr

                leitor.append(easyocr.Reader(["pt", "en"], gpu=False, verbose=False))
            return "  ".join(leitor[0].readtext(imagem, detail=0, paragraph=False))

    return ler


class LeitorEndereco:
    def __init__(self, ocr: Ocr | None, por_minuto: int = 6, por_hora_total: int = 120):
        self.ocr = ocr
        self.por_minuto = por_minuto
        self.por_hora_total = por_hora_total
        self._usos: dict[str, deque] = defaultdict(deque)
        self._total: deque = deque()
        self._trava = threading.Lock()

    @property
    def ativo(self) -> bool:
        return self.ocr is not None

    def registrar_uso(self, cliente: str) -> None:
        agora = time.monotonic()
        with self._trava:
            fila = self._usos[cliente]
            while fila and agora - fila[0] > 60:
                fila.popleft()
            while self._total and agora - self._total[0] > 3600:
                self._total.popleft()
            if len(fila) >= self.por_minuto or len(self._total) >= self.por_hora_total:
                raise LimiteExcedido()
            fila.append(agora)
            self._total.append(agora)
            if len(self._usos) > 5000:  # não deixa o dicionário crescer sem fim
                for k in [k for k, v in self._usos.items() if not v or agora - v[-1] > 60]:
                    del self._usos[k]

    def ler(self, dados: bytes) -> dict:
        """Roda o pipeline. Erro de arquivo vira ArquivoInvalido; falha do OCR vira resposta sem campos."""
        if self.ocr is None:
            return self._resposta({}, None, "indisponivel")
        imagem = carregar_imagem(dados)
        papel = corrigir_perspectiva(imagem, achar_cantos_do_papel(imagem))
        del imagem
        h, w = papel.shape[:2]
        f = min(LARGURA_OCR / w, 2 * LARGURA_OCR / h)  # imagem estreita e comprida não pode explodir de tamanho
        papel = cv2.resize(papel, (max(int(w * f), 1), max(int(h * f), 1)), interpolation=cv2.INTER_CUBIC if f > 1 else cv2.INTER_AREA)
        h, w = papel.shape[:2]
        cabecalho = papel[0: int(h * 0.22), :]
        regiao = papel[int(h * 0.10): int(h * 0.55), int(w * 0.04): int(w * 0.96)]
        try:
            texto_cab = self.ocr(cabecalho)
            texto_end = self.ocr(regiao)
            if not _cep(texto_end.upper()) and not _logradouro(" " + texto_end.upper() + " ")[0]:
                # Foto com outro enquadramento: tenta a versão binarizada da página inteira.
                texto_end = self.ocr(binarizar(papel))
        except Exception:
            log.exception("Falha no OCR do comprovante")
            return self._resposta({}, None, "erro")
        empresa = detectar_empresa(texto_cab) or detectar_empresa(texto_end)
        return self._resposta(extrair_campos(texto_end), empresa, "ocr")

    @staticmethod
    def _resposta(campos: dict, empresa: str | None, fonte: str) -> dict:
        base = {k: campos.get(k) for k in ("logradouro", "numero", "bairro", "cep", "uf")}
        encontrados = sum(1 for k in ("logradouro", "numero", "bairro", "cep") if base[k])
        return {
            **base,
            "empresa": empresa,
            "empresa_nome": EMPRESAS.get(empresa or ""),
            "confianca": round(encontrados / 4, 2),
            "fonte": fonte,
        }

import os
import re
import cv2
import numpy as np

_EASYOCR_READER = None

def get_easyocr_reader():
    """Singleton do leitor EasyOCR em memória para acelerar inferências subsequentes."""
    global _EASYOCR_READER
    if _EASYOCR_READER is None:
        try:
            import easyocr
            _EASYOCR_READER = easyocr.Reader(['pt', 'en'], gpu=False)
        except Exception:
            _EASYOCR_READER = False
    return _EASYOCR_READER

def cv2_to_base64(img, quality=80, max_dim=900):
    """Converte matriz OpenCV diretamente em Data URL Base64 para exibição no navegador (Zero-Storage)."""
    if img is None:
        return ""
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / float(max(h, w))
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    success, buffer = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if success:
        import base64
        return "data:image/jpeg;base64," + base64.b64encode(buffer).decode('utf-8')
    return ""

PATTERNS = {
    "cep": r"\b\d{5}[-\s]?\d{3}\b",
    "uf": r"\b(AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)\b",
    "logradouro": r"(?:LOGRADOURO\s*:?\s*|\b(RUA|R\.|AVENIDA|AV\.|ESTRADA|ALAMEDA|TRAVESSA|PRACA)\b)\s*([A-Z0-9\s]+?)(?:,\s*N[º°OE\.]?\s*|,\s*|\s+N[º°OE\.]?\s*|\s+NUMERO\s*|\s+)(\d+)",
}

def detect_company(raw_text: str) -> str:
    """Identifica se o documento pertence a Enel, Sabesp ou Claro."""
    upper = raw_text.upper()
    if any(k in upper for k in ["ENEL", "CNEL", "ELETROPAULO", "ENERGIA ELÉTRICA", "ENERGIA ELETRICA"]):
        return "ENEL"
    elif any(k in upper for k in ["SABESP", "SANEAMENTO", "ÁGUA E ESGOTO", "AGUA E ESGOTO", "LIGAÇÃO DE ÁGUA", "LIGACAO DE AGUA"]):
        return "SABESP"
    elif any(k in upper for k in ["CLARO", "TELECOM", "EMBRATEL", "NET SERVIÇOS"]):
        return "CLARO"
    return "DESCONHECIDA"

def parse_address_from_text(raw_text: str):
    """Extrai entidades de endereço do texto via expressões regulares, segregando endereços corporativos."""
    clean_text = raw_text.upper().replace("\n", "  ")
    
    # 1. Extração de CEP (segregando CEPs de sedes corporativas)
    CORPORATE_CEPS = ["04794-000", "04794000", "05429-900", "05429900", "04711-130", "04711130"]
    all_ceps = re.findall(PATTERNS["cep"], clean_text)
    cep = None
    for c in all_ceps:
        norm = c.replace(" ", "-")
        if norm not in CORPORATE_CEPS:
            cep = norm
            break
    if not cep and all_ceps:
        cep = all_ceps[0].replace(" ", "-")
        
    if "SAO PAULO" in clean_text or "SÃO PAULO" in clean_text or "PAULOISP" in clean_text or " SP " in clean_text or "/SP" in clean_text:
        uf = "SP"
    else:
        uf_match = re.search(PATTERNS["uf"], clean_text)
        uf = uf_match.group(0) if uf_match else "SP"
    
    # 2. Extração de Logradouro e Número
    logradouro = None
    numero = None
    
    # Procura candidatos de logradouro evitando cabeçalhos fiscais e sedes
    IGNORED_WORDS = [
        "PÁGINA", "PAGINA", "NOTA FISCAL", "SERIE", "SÉRIE", "FATURA", "EMISSAO", "EMISSÃO",
        "DATA", "CONSUMIDOR", "NAÇÕES UNIDAS", "NACOES UNIDAS", "RESIDENCIAL", "RESIDENCIA",
        "RERIDERS", "CONVENCIONAL", "MONOFASICO", "MONOLASICO", "LEITURA", "MESIANO",
        "INFORMACOES", "INFORMAÇÕES", "FISCAIS", "ELETRICA", "ELETRÔNICA", "TRIBUTÁRIA"
    ]
    
    pat_search = r'(?:LOGRADOURO\s*:?\s*|\b(RUA|R\.|AVENIDA|AV\.|ESTRADA|ALAMEDA|TRAVESSA|PRACA|R)\.?\s*|\b(R[BCDFGHJKLMNPQRSTVWXYZ][A-ZÀ-Ú0-9]+))\s*(?:,\s*|\s+)?([A-ZÀ-Ú0-9\s]*?)(?:,\s*|\s+)(?:N[º°OE\.]?|NUMERO|DO|DA)?\s*(\d+)'
    
    for m in re.finditer(pat_search, clean_text):
        cand = (m.group(3) or '').strip()
        cnum = m.group(4)
        prefix1 = m.group(1) or ''
        prefix2 = m.group(2) or ''
        
        # Ignora se o número for na verdade parte de uma data (ex: 05/11/2026)
        end_pos = m.end(4)
        if end_pos < len(clean_text) and clean_text[end_pos] == '/':
            continue
            
        full_cand = f"{prefix1} {prefix2} {cand}".upper()
        if any(ign in full_cand for ign in IGNORED_WORDS):
            continue
            
        if len(cand) >= 2 or prefix2:
            if prefix2: # Ex: RHIPODROMO -> Rua Hipodromo
                nome = prefix2[1:].title()
                logradouro = f"Rua {nome}"
            elif prefix1:
                tipo = prefix1.replace(".", "").title()
                if tipo == "R": tipo = "Rua"
                logradouro = f"{tipo} {cand.title()}".strip()
            else:
                logradouro = cand.title()
            numero = cnum
            break

    # Fallback se não encontrou
    if not logradouro:
        logr_match = re.search(PATTERNS["logradouro"], clean_text)
        if logr_match:
            tipo = logr_match.group(1).title() if logr_match.group(1) else ""
            nome = logr_match.group(2).strip().title()
            logradouro = f"{tipo} {nome}".strip()
            numero = logr_match.group(3)

    # Limpeza e normalização do logradouro
    if logradouro:
        logradouro = re.sub(r'^(Rua|Avenida|Estrada|Alameda|Travessa)(Estrada|Avenida|Rua|Alameda|Travessa)', r'\1 \2', logradouro, flags=re.IGNORECASE)
        logradouro = re.sub(r'^Ruaestrada', 'Rua Estrada', logradouro, flags=re.IGNORECASE)
        logradouro = re.sub(r'\s+(Nd|Ne|Nº|N°|Numero|N)\.?$', '', logradouro, flags=re.IGNORECASE)
        logradouro = logradouro.strip()

    # 3. Extração de Bairro
    bairro = None
    bairro_match = re.search(r'\b(?:BAIRRO|MOOCA|VILA|JARDIM|JD\.|PQ\.|PARQUE)\s*:?\s*([A-Z0-9\s]+?)(?:\s+MUN|\s+CIDADE|\s+S[ÃA0]O|\s+CEP|\s+NOTA|\s+SERIE)', clean_text)
    if bairro_match:
        bairro = bairro_match.group(1).strip().title()
    elif "MOOCA" in clean_text:
        bairro = "Mooca"
        
    return {
        "cep": cep,
        "uf": uf,
        "logradouro": logradouro,
        "numero": numero,
        "bairro": bairro,
        "raw_text": raw_text
    }

def load_image_from_file_or_pdf(file_path: str):
    """Carrega uma imagem a partir de PNG/JPG ou renderiza a primeira página de um PDF."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
    if file_path.lower().endswith(".pdf"):
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(file_path)
        page = pdf[0]
        # Renderiza a 2.0x (aprox. 150-200 DPI) para alta fidelidade no OCR
        pil_img = page.render(scale=2.0).to_pil()
        # Converte PIL para formato OpenCV (BGR)
        img_np = np.array(pil_img)
        img = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        return img
    else:
        img = cv2.imread(file_path)
        if img is None:
            raise ValueError(f"Não foi possível abrir a imagem: {file_path}")
        return img

def extract_address_from_roi(image_path: str):
    """
    Executa o recorte proporcional da ROI do endereço do cliente e OCR.
    Suporta arquivos PNG, JPG e documentos PDF.
    """
    img = load_image_from_file_or_pdf(image_path)
        
    h, w, _ = img.shape
    
    # 1. Região do Cabeçalho (primeiros 22%) -> para identificar a concessionária
    header_roi = img[0:int(h * 0.22), :]
    
    # 2. Região do Endereço do Cliente (de 10% a 55%) -> cobrindo faturas reais e sintéticas
    address_roi = img[int(h * 0.10):int(h * 0.55), int(w * 0.04):int(w * 0.96)]
    
    header_text = ""
    address_text = ""
    reader = get_easyocr_reader()
    if reader:
        try:
            header_results = reader.readtext(header_roi, detail=0)
            header_text = " ".join(header_results)
            
            address_results = reader.readtext(address_roi, detail=0)
            address_text = " ".join(address_results)
        except Exception:
            pass
    
    if not address_text:
        # Fallback para Tesseract
        try:
            import pytesseract
            header_text = pytesseract.image_to_string(header_roi, lang='por')
            address_text = pytesseract.image_to_string(address_roi, lang='por')
        except Exception:
            address_text = "ERRO_OCR_NAO_CONFIGURADO"
            
    parsed = parse_address_from_text(address_text)
    # Detecta a concessionária pelo cabeçalho (ou pelo corpo da fatura como fallback)
    parsed["empresa_detectada"] = detect_company(header_text)
    if parsed["empresa_detectada"] == "DESCONHECIDA":
        parsed["empresa_detectada"] = detect_company(address_text)
        
    return parsed

def load_image_from_bytes(file_bytes: bytes, filename: str):
    """Carrega PDF ou imagem diretamente da memória volátil (Zero-Storage)."""
    if filename.lower().endswith(".pdf"):
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(file_bytes)
        page = pdf[0]
        pil_img = page.render(scale=2).to_pil()
        img_np = np.array(pil_img)
        img = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        return img
    else:
        nparr = np.frombuffer(file_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Não foi possível decodificar os bytes da imagem.")
        return img

def process_image_buffer_zero_storage(file_bytes: bytes, filename: str):
    """
    Executa o pipeline completo de Visão Computacional diretamente na memória volátil (Zero-Storage):
    1. Decodificação do PDF ou Imagem
    2. Detecção dos 4 vértices e retificação de perspectiva (warpPerspective)
    3. Pré-processamento e binarização adaptativa de Otsu
    4. Reconhecimento de caracteres (EasyOCR) e segregação inteligente residencial vs. corporativa
    5. Conversão das transformações para base64 para inspeção visual na interface web
    """
    from scanner import find_document_corners, four_point_transform, preprocess_image_for_ocr

    # 1. Carrega em memória
    original_img = load_image_from_bytes(file_bytes, filename)
    
    # 2. Correção de perspectiva
    corners = find_document_corners(original_img)
    warped_img = four_point_transform(original_img, corners)
    
    # 3. Pré-processamento e Otsu
    otsu_img = preprocess_image_for_ocr(warped_img)
    
    # 4. OCR e extração
    h, w = warped_img.shape[:2]
    header_roi = warped_img[0:int(h * 0.22), :]
    address_roi = warped_img[int(h * 0.10):int(h * 0.55), int(w * 0.04):int(w * 0.96)]
    
    reader = get_easyocr_reader()
    header_text = ""
    address_text = ""
    if reader:
        try:
            header_results = reader.readtext(header_roi, detail=0)
            header_text = " ".join(header_results)
            
            address_results = reader.readtext(address_roi, detail=0)
            address_text = " ".join(address_results)
        except Exception:
            pass
            
    parsed = parse_address_from_text(address_text)
    empresa = detect_company(header_text)
    if empresa == "DESCONHECIDA":
        empresa = detect_company(address_text)
    parsed["empresa_detectada"] = empresa
    
    empresa_nomes = {
        "ENEL": "Enel Distribuição São Paulo",
        "SABESP": "Companhia de Saneamento Básico (Sabesp)",
        "CLARO": "Claro Brasil Telecomunicações",
        "DESCONHECIDA": "Concessionária Residencial"
    }
    parsed["empresa_formal"] = empresa_nomes.get(empresa, empresa)
    
    # Validação e status para o EduConecta
    if parsed.get("cep") and parsed.get("logradouro"):
        parsed["status"] = "Comprovante residencial validado com sucesso. Aluno elegível para o programa EduConecta Periferia."
        parsed["elegivel"] = True
    else:
        parsed["status"] = "Documento em análise: Por favor, confira e complete os campos necessários."
        parsed["elegivel"] = False
        
    # Previews visuais em base64 (em memória)
    previews = {
        "original": cv2_to_base64(original_img),
        "desentortado": cv2_to_base64(warped_img),
        "binarizado": cv2_to_base64(otsu_img)
    }
    
    return {
        "data": parsed,
        "previews": previews,
        "dimensions": {
            "original_width": int(original_img.shape[1]),
            "original_height": int(original_img.shape[0]),
            "warped_width": int(warped_img.shape[1]),
            "warped_height": int(warped_img.shape[0])
        }
    }

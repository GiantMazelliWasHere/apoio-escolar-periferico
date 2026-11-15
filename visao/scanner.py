import cv2
import numpy as np

def order_points(pts):
    """Ordena 4 vértices: top-left, top-right, bottom-right, bottom-left."""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def four_point_transform(image, pts):
    """Executa a transformação de perspectiva plana (warpPerspective)."""
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    max_width = max(int(width_a), int(width_b))

    height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    max_height = max(int(height_a), int(height_b))

    dst = np.array([
        [0, 0],
        [max_width - 1, 0],
        [max_width - 1, max_height - 1],
        [0, max_height - 1]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (max_width, max_height))
    return warped

def preprocess_image_for_ocr(image):
    """Converte para cinza, aplica filtro bilateral e binarização de Otsu."""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # Filtro bilateral para reduzir ruído preservando bordas de texto
    filtered = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)
    
    # Binarização de Otsu
    _, thresh = cv2.threshold(filtered, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

def find_document_corners(image):
    """
    Localiza os 4 vértices do papel na imagem através de detecção de bordas de Canny
    e aproximação poligonal dos maiores contornos.
    Caso não detecte um contorno quadrilátero nítido, retorna os 4 cantos da própria imagem.
    """
    h, w = image.shape[:2]
    # Redimensiona para altura de 600px para acelerar a detecção
    ratio = h / 600.0
    small_w = int(w / ratio)
    small = cv2.resize(image, (small_w, 600))
    
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 75, 200)
    
    # Encontra contornos
    contours, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
    
    doc_contour = None
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        # Se tem 4 vértices e área significativa (pelo menos 15% do frame)
        if len(approx) == 4 and cv2.contourArea(c) > (small_w * 600 * 0.15):
            doc_contour = approx
            break
            
    if doc_contour is not None:
        pts = doc_contour.reshape(4, 2) * ratio
        return pts.astype("float32")
    else:
        # Fallback: utiliza as 4 bordas da imagem inteira
        return np.array([
            [0, 0],
            [w - 1, 0],
            [w - 1, h - 1],
            [0, h - 1]
        ], dtype="float32")

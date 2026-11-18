import os
import sys
import json
import cv2
from scanner import find_document_corners, four_point_transform, preprocess_image_for_ocr
from ocr_engine import extract_address_from_roi, load_image_from_file_or_pdf

def main():
    # Se o usuário passar um arquivo como argumento, usa ele. Senão usa a primeira fatura sintética.
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = os.path.join("dataset_sintetico", "enel_01.png")

    if not os.path.exists(image_path):
        print(f"❌ Erro: Arquivo de comprovante não encontrado: '{image_path}'")
        print("💡 Dica: Passe o caminho de uma imagem ou PDF, ex: py -3.11 process_bill.py enel-boleto.pdf")
        return

    print("=" * 65)
    print("👁️  EDUCONECTA PERIFERIA — PIPELINE DE VISÃO COMPUTACIONAL")
    print(f"📄 Processando comprovante: {image_path}")
    print("=" * 65)

    # 1. Carregar imagem (suporta PNG, JPG e PDF)
    try:
        img = load_image_from_file_or_pdf(image_path)
    except Exception as e:
        print(f"❌ Não foi possível carregar o arquivo: {e}")
        return

    orig_h, orig_w = img.shape[:2]
    print(f"1. [Geometria] Dimensões originais: {orig_w}x{orig_h}px")

    # 2. Localizar vértices e desentortar perspectiva
    corners = find_document_corners(img)
    warped = four_point_transform(img, corners)
    print("2. [Geometria] 4 vértices do papel localizados. Perspectiva retificada (cv2.warpPerspective) ✅")

    # Salva cópia desentortada para inspeção visual
    output_warped = "resultado_desentortado.png"
    cv2.imwrite(output_warped, warped)
    print(f"   ↳ Imagem retificada salva em: {output_warped}")

    # 3. Pré-processamento com Otsu
    thresh = preprocess_image_for_ocr(warped)
    output_thresh = "resultado_binarizado_otsu.png"
    cv2.imwrite(output_thresh, thresh)
    print("3. [Filtros] Escala de cinza, filtro bilateral e binarização de Otsu aplicados ✅")
    print(f"   ↳ Imagem binarizada salva em: {output_thresh}")

    # 4. Extração de Endereço e OCR
    print("4. [OCR] Lendo cabeçalho e recortando ROI do cliente (EasyOCR)...")
    resultado = extract_address_from_roi(image_path)

    print("\n" + "=" * 65)
    print("📋 DADOS EXTRAÍDOS PARA O CADASTRO DO ESTUDANTE (JSON):")
    print("=" * 65)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))

    print("\n" + "-" * 65)
    print(f"🏢 Concessionária:  {resultado.get('empresa_detectada') or 'NÃO IDENTIFICADA'}")
    print(f"📍 Logradouro:       {resultado.get('logradouro') or 'N/A'}")
    print(f"🔢 Número:          {resultado.get('numero') or 'S/N'}")
    print(f"🏘️  Bairro:          {resultado.get('bairro') or 'N/A'}")
    print(f"📮 CEP:             {resultado.get('cep') or 'N/A'}")
    print(f"🗺️  UF:              {resultado.get('uf') or 'SP'}")
    
    if resultado.get("cep") and resultado.get("empresa_detectada") != "DESCONHECIDA":
        print("✅ Status da Validação: COMPROVANTE ACEITO! Aluno elegível para o Apoio Escolar.")
    else:
        print("⚠️ Status da Validação: Necessário reenvio ou auxílio pela AI Bits no suporte.")
    print("=" * 65)

if __name__ == "__main__":
    main()

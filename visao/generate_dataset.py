import os
import json
import random
from PIL import Image, ImageDraw, ImageFont

try:
    from faker import Faker
    fake = Faker('pt_BR')
except ImportError:
    class DummyFake:
        def name(self): 
            return random.choice(["MARIA DA SILVA", "JOSE DOS SANTOS", "ANA PAULA SOUZA", "LUCAS PEREIRA", "JULIANA LIMA"])
        def street_name(self): 
            return random.choice(["RUA DAS FLORES", "AVENIDA PRINCIPAL", "RUA DOS PALMARES", "ESTRADA DO COPO", "RUA BOA VISTA"])
        def bairro(self): 
            return random.choice(["CAPAO REDONDO", "GRAJAU", "BRASILANDIA", "ITAQUERA", "CIDADE TIRADENTES"])
    fake = DummyFake()

COMPANIES = ["ENEL", "SABESP", "CLARO"]
OUTPUT_DIR = "dataset_sintetico"

def generate_bill_image(company: str, index: int, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    width, height = 1240, 1754  # A4 proporcional
    image = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    titular = fake.name().upper()
    logradouro = fake.street_name().upper()
    numero = str(random.randint(10, 3500))
    bairro = fake.bairro().upper()
    cidade = "SÃO PAULO"
    uf = "SP"
    cep = f"{random.randint(1000, 9999):05d}-{random.randint(100, 999):03d}"
    
    # 1. Cabeçalho Institucional (endereço corporativo que deve ser ignorado)
    draw.rectangle([(0, 0), (width, 180)], fill=(240, 240, 240))
    draw.text((60, 40), f"CONCESSIONÁRIA {company} DE SÃO PAULO S.A.", fill=(20, 20, 20))
    draw.text((60, 80), "SEDE CORPORATIVA: AV. DAS NAÇÕES UNIDAS, 14401 - SÃO PAULO/SP - CEP: 04794-000", fill=(100, 100, 100))
    draw.text((60, 110), "CNPJ: 61.695.227/0001-93 - INSCRIÇÃO ESTADUAL: 112.000.111.222", fill=(120, 120, 120))
    
    # 2. Bloco de Endereço do Destinatário
    if company == "ENEL":
        box_y1, box_y2 = 320, 560
        box_x1, box_x2 = 60, 750
        draw.rectangle([(box_x1, box_y1), (box_x2, box_y2)], outline=(0, 102, 204), width=3)
        draw.text((box_x1 + 20, box_y1 + 20), "DADOS DO CLIENTE / ENDEREÇO DE ENTREGA", fill=(0, 102, 204))
        draw.text((box_x1 + 20, box_y1 + 60), f"CLIENTE: {titular}", fill=(0, 0, 0))
        draw.text((box_x1 + 20, box_y1 + 100), f"LOGRADOURO: RUA {logradouro}, Nº {numero}", fill=(0, 0, 0))
        draw.text((box_x1 + 20, box_y1 + 140), f"BAIRRO: {bairro}", fill=(0, 0, 0))
        draw.text((box_x1 + 20, box_y1 + 180), f"MUNICÍPIO: {cidade} - {uf}   CEP: {cep}", fill=(0, 0, 0))

    elif company == "SABESP":
        box_y1, box_y2 = 300, 520
        box_x1, box_x2 = 450, 1180
        draw.rectangle([(box_x1, box_y1), (box_x2, box_y2)], fill=(235, 245, 255), outline=(0, 70, 150), width=2)
        draw.text((box_x1 + 20, box_y1 + 20), "ENDEREÇO DO IMÓVEL / LIGAÇÃO DE ÁGUA", fill=(0, 70, 150))
        draw.text((box_x1 + 20, box_y1 + 60), f"NOME: {titular}", fill=(0, 0, 0))
        draw.text((box_x1 + 20, box_y1 + 95), f"AVENIDA {logradouro}, {numero}", fill=(0, 0, 0))
        draw.text((box_x1 + 20, box_y1 + 130), f"{bairro} - {cidade}/{uf}", fill=(0, 0, 0))
        draw.text((box_x1 + 20, box_y1 + 165), f"CEP: {cep}", fill=(0, 0, 0))

    elif company == "CLARO":
        box_y1, box_y2 = 380, 600
        box_x1, box_x2 = 500, 1150
        draw.rectangle([(box_x1, box_y1), (box_x2, box_y2)], fill=(245, 245, 245), outline=(200, 20, 20), width=2)
        draw.text((box_x1 + 20, box_y1 + 20), "DESTINATÁRIO DA FATURA", fill=(200, 20, 20))
        draw.text((box_x1 + 20, box_y1 + 60), f"{titular}", fill=(0, 0, 0))
        draw.text((box_x1 + 20, box_y1 + 95), f"RUA {logradouro}, {numero}", fill=(0, 0, 0))
        draw.text((box_x1 + 20, box_y1 + 130), f"{bairro}", fill=(0, 0, 0))
        draw.text((box_x1 + 20, box_y1 + 165), f"{cidade} - {uf}   {cep}", fill=(0, 0, 0))

    # 3. Código de barras no rodapé
    draw.rectangle([(60, 1550), (1180, 1650)], fill=(230, 230, 230))
    draw.text((100, 1600), "83610000001-2 45890109202-6 61104101300-8 00001004202-1", fill=(0, 0, 0))
    
    filename = f"{company.lower()}_{index:02d}.png"
    filepath = os.path.join(output_dir, filename)
    image.save(filepath)
    
    return {
        "file_name": filename,
        "company": company,
        "ground_truth": {
            "titular": titular,
            "logradouro": logradouro,
            "numero": numero,
            "bairro": bairro,
            "cidade": cidade,
            "uf": uf,
            "cep": cep
        }
    }

def main():
    dataset_records = []
    print("Gerando dataset sintético de faturas...")
    for comp in COMPANIES:
        for i in range(1, 6):
            gt = generate_bill_image(comp, i, OUTPUT_DIR)
            dataset_records.append(gt)
            
    gt_path = os.path.join(OUTPUT_DIR, "ground_truth.json")
    with open(gt_path, "w", encoding="utf-8") as f:
        json.dump(dataset_records, f, indent=2, ensure_ascii=False)
        
    print(f"Sucesso: 15 faturas e {gt_path} gerados com conformidade LGPD!")

if __name__ == "__main__":
    main()

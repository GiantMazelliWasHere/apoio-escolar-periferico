"""
Hub Web Interativo — Extração Automática de Endereços por Visão Computacional
Projeto: Apoio Escolar Periférico (FIAP Global Solution 2026.2 - Bits N’ Bytes - 4ESPR)
Disciplina: Applied Computer Vision (Prof. Wilians Douglas Conde Souza)

Arquitetura Zero-Storage:
Todo o processamento ocorre 100% em memória volátil (RAM), sem gravação em disco.
Conformidade rigorosa com a LGPD.
"""

import os
import sys
import subprocess

# Auto-detecção e redirecionamento para o ambiente Python 3.11:
# O OpenCV e Torch requerem Python 3.11 no Windows. Caso o comando 'python' padrão
# aponte para outra versão (ex: Python 3.14), este trecho redireciona automaticamente.
try:
    import flask
    import cv2
except ImportError:
    py311_candidates = [
        r"C:\Program Files\Python311\python.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Python\Python311\python.exe"),
    ]
    target_py = None
    for cand in py311_candidates:
        if os.path.exists(cand):
            target_py = cand
            break
            
    if target_py and sys.executable != target_py:
        print(f"[Auto-Redirect] Inicializando via Python 3.11 compatível com OpenCV/Torch ({target_py})...")
        res = subprocess.run([target_py] + sys.argv)
        sys.exit(res.returncode)
    else:
        try:
            print("[Auto-Redirect] Inicializando via 'py -3.11'...")
            res = subprocess.run(["py", "-3.11"] + sys.argv)
            sys.exit(res.returncode)
        except Exception:
            pass

from flask import Flask, render_template, request, jsonify, send_from_directory

# Adiciona o diretório atual ao sys.path para garantir importações locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ocr_engine import process_image_buffer_zero_storage

app = Flask(__name__, template_folder="templates")

# Configuração de limites para upload seguro em memória
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

@app.route("/img/<path:filename>")
def serve_img(filename):
    """Serve imagens estáticas (logos, ícones) da pasta img/."""
    return send_from_directory(os.path.join(os.path.dirname(__file__), "img"), filename)

@app.route("/")
def home():
    """Renderiza a interface do Hub Web de Visão Computacional."""
    return render_template("index.html")

@app.route("/api/v1/health", methods=["GET"])
def health_check():
    """Endpoint de checagem de integridade do pipeline."""
    return jsonify({
        "status": "healthy",
        "service": "Apoio Escolar Vision Hub",
        "version": "1.0.0",
        "supported_companies": ["ENEL", "SABESP", "CLARO"],
        "lgpd_compliance": "Zero-Storage in-memory processing"
    })

@app.route("/api/v1/sample/<company>", methods=["GET"])
def process_sample(company):
    """
    Permite teste com 1 clique usando faturas sintéticas (LGPD).
    Carrega o arquivo sintético em buffer de memória e executa o pipeline.
    """
    company_clean = company.lower().strip()
    sample_file = os.path.join(os.path.dirname(__file__), "dataset_sintetico", f"{company_clean}_01.png")
    
    if not os.path.exists(sample_file):
        return jsonify({
            "success": False,
            "error": f"Fatura sintética para '{company}' não encontrada no dataset."
        }), 404
        
    try:
        with open(sample_file, "rb") as f:
            file_bytes = f.read()
            
        result = process_image_buffer_zero_storage(file_bytes, f"{company_clean}_01.png")
        return jsonify({
            "success": True,
            "data": result["data"],
            "previews": result["previews"],
            "dimensions": result["dimensions"],
            "lgpd_notice": "Documento sintético processado em memória volátil. Zero armazenamento."
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Falha no processamento da amostra: {str(e)}"
        }), 500

@app.route("/api/v1/cv/extract-student-address", methods=["POST"])
def extract_student_address():
    """
    Endpoint REST Oficial de Integração com o MVP:
    Recebe documento (PDF, PNG, JPG), processa em memória RAM e retorna JSON estruturado.
    """
    if "file" not in request.files:
        return jsonify({
            "success": False,
            "error": "Nenhum arquivo enviado. Envie o campo 'file' via multipart/form-data."
        }), 400
        
    file = request.files["file"]
    if not file.filename:
        return jsonify({
            "success": False,
            "error": "Nome de arquivo inválido."
        }), 400
        
    filename = file.filename
    allowed_exts = (".pdf", ".png", ".jpg", ".jpeg")
    if not filename.lower().endswith(allowed_exts):
        return jsonify({
            "success": False,
            "error": f"Formato não suportado. Formatos aceitos: {', '.join(allowed_exts)}"
        }), 400
        
    try:
        # Lê os bytes diretamente do stream HTTP para a memória RAM (sem salvar no disco)
        file_bytes = file.read()
        
        # Executa o pipeline de Visão Computacional
        result = process_image_buffer_zero_storage(file_bytes, filename)
        
        return jsonify({
            "success": True,
            "data": result["data"],
            "previews": result["previews"],
            "dimensions": result["dimensions"],
            "lgpd_notice": "Documento processado 100% em memória volátil e descartado imediatamente. Zero armazenamento persistente."
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erro ao processar comprovante: {str(e)}"
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=" * 65)
    print("🌐 EDUCONECTA PERIFERIA — HUB DE VISÃO COMPUTACIONAL INICIADO")
    print(f"🔗 Abra no navegador: http://127.0.0.1:{port}")
    print("🔒 Arquitetura Zero-Storage ativa: Nenhum arquivo é salvo em disco.")
    print("=" * 65)
    app.run(host="127.0.0.1", port=port, debug=False)

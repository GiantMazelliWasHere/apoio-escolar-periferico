"""Configuração lida de variáveis de ambiente (segredos nunca ficam no código)."""
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

# Desenvolvimento local: lê mvp/.env (fora do git). Em produção valem as variáveis do App Service.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class Settings:
    def __init__(self) -> None:
        self.env = os.getenv("APP_ENV", "development")
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./apoio.db")
        secret = os.getenv("SECRET_KEY")
        if not secret:
            if self.env == "production":
                raise RuntimeError("SECRET_KEY é obrigatória em produção (configure no App Service).")
            secret = secrets.token_hex(32)  # chave efêmera só para desenvolvimento local
        self.secret_key = secret
        # Chave usada por integrações máquina-a-máquina (robô RPA, pipeline de dados).
        self.integration_api_key = os.getenv("INTEGRATION_API_KEY", "")
        # Assistente de IA Generativa (OpenRouter). Sem chave, a tela "Ajuda" mostra só as perguntas frequentes.
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.genai_model = os.getenv("GENAI_MODEL_NAME", "").strip() or "google/gemini-2.5-flash"
        # URL pública do MVP (ex.: https://<app>.azurewebsites.net), usada no QR code da peça do Maker Lab.
        # Vazia: o QR usa o endereço pelo qual a página foi aberta.
        self.public_url = os.getenv("PUBLIC_URL", "").strip().rstrip("/")
        self.seed_demo =os.getenv("SEED_DEMO", "1") == "1"
        self.https_only_cookies = self.env == "production"


settings = Settings()

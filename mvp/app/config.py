"""Configuração lida de variáveis de ambiente (segredos nunca ficam no código)."""
import os
import secrets


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
        self.seed_demo = os.getenv("SEED_DEMO", "1") == "1"
        self.https_only_cookies = self.env == "production"


settings = Settings()

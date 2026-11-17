"""Configuração lida de variáveis de ambiente (segredos nunca ficam no código)."""
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

# Desenvolvimento local: lê mvp/.env (fora do git). Em produção valem as variáveis do App Service.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


# Segredos que a aplicação exige em produção. No Azure vêm do Key Vault por referência
# (@Microsoft.KeyVault(...) nas Configurações de aplicativo), lidos pela identidade gerenciada.
SEGREDOS_OBRIGATORIOS = ("SECRET_KEY", "INTEGRATION_API_KEY", "FERNET_KEY")

# Arquivo gravado pelo pipeline (job "pacote") com o hash do commit publicado.
ARQUIVO_VERSAO = Path(__file__).resolve().parent.parent / "VERSAO"


def ler_versao() -> str:
    try:
        return ARQUIVO_VERSAO.read_text(encoding="utf-8").strip() or "dev"
    except OSError:
        return "dev"


class Settings:
    def __init__(self) -> None:
        self.env = os.getenv("APP_ENV", "development")
        self.versao = ler_versao()
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./apoio.db")
        if self.env == "production":
            faltando = [nome for nome in SEGREDOS_OBRIGATORIOS if not os.getenv(nome, "").strip()]
            if faltando:
                # Falha cedo: o App Service mostra o erro no log e o health check fica vermelho.
                raise RuntimeError(f"Segredos obrigatórios ausentes em produção: {', '.join(faltando)}")
        # Fora de produção, chave efêmera (as sessões caem a cada reinício, o que é aceitável localmente).
        self.secret_key = os.getenv("SECRET_KEY", "").strip() or secrets.token_hex(32)
        # Chave usada por integrações máquina-a-máquina (robô RPA, pipeline de dados).
        self.integration_api_key = os.getenv("INTEGRATION_API_KEY", "")
        # Chave Fernet que cifra o e-mail do responsável. Fora de produção, derivada da SECRET_KEY.
        self.fernet_key = os.getenv("FERNET_KEY", "").strip()
        # Assistente de IA Generativa (OpenRouter). Sem chave, a tela "Ajuda" mostra só as perguntas frequentes.
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.genai_model = os.getenv("GENAI_MODEL_NAME", "").strip() or "google/gemini-2.5-flash"
        # URL pública do MVP (ex.: https://<app>.azurewebsites.net), usada no QR code da peça do Maker Lab.
        # Vazia: o QR usa o endereço pelo qual a página foi aberta.
        self.public_url = os.getenv("PUBLIC_URL", "").strip().rstrip("/")
        self.seed_demo = os.getenv("SEED_DEMO", "1") == "1"
        self.https_only_cookies = self.env == "production"
        # Região do Azure onde o app roda (o App Service define REGION_NAME), exibida no Aviso de Privacidade.
        self.regiao = os.getenv("REGION_NAME", "").strip()


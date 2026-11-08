#!/bin/sh
# Comando de inicialização no Azure App Service (Linux, Python).
# Configure em: App Service > Configuração > Comando de inicialização: "sh startup.sh"
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers --forwarded-allow-ips="*"

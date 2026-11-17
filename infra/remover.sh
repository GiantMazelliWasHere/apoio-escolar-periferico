#!/usr/bin/env bash
# Remove TUDO o que infra/provisionar.sh criou (usar depois da correção, para não gerar custo).
# Irreversível: apaga o banco SQLite do App Service e os segredos do Key Vault (com purge).
#   CONFIRMAR=sim ./infra/remover.sh
set -euo pipefail
[ "${CONFIRMAR:-}" = "sim" ] || { echo "Isto apaga o Resource Group inteiro. Rode com CONFIRMAR=sim."; exit 1; }

ASSINATURA_ID="$(az account show --query id -o tsv)"
SUFIXO="${SUFIXO:-${ASSINATURA_ID:0:6}}"
RG="${RG:-rg-apoioescolar}"
KV="${KV:-kv-apoioescolar-$SUFIXO}"
OIDC_APP_NOME="${OIDC_APP_NOME:-github-apoioescolar-deploy}"

echo "==> Apagando o Resource Group $RG (alguns minutos)"
az group delete -n "$RG" --yes
echo "==> Purge do Key Vault $KV (libera o nome e os segredos de vez)"
az keyvault purge -n "$KV" 2>/dev/null || echo "   (já purgado ou inexistente)"
echo "==> Apagando o app registration do GitHub OIDC ($OIDC_APP_NOME)"
OIDC_APP_ID="$(az ad app list --display-name "$OIDC_APP_NOME" --query '[0].appId' -o tsv)"
[ -n "$OIDC_APP_ID" ] && az ad app delete --id "$OIDC_APP_ID" || echo "   (não encontrado)"
echo "Pronto. As variáveis AZURE_* do GitHub podem ser apagadas; sem AZURE_WEBAPP_NAME o deploy é pulado."

#!/usr/bin/env bash
# Cria (ou atualiza) toda a infraestrutura do MVP na Azure. Idempotente: pode rodar de novo.
#
# Uso (Azure Cloud Shell em Bash, ou Git Bash/WSL com o Azure CLI logado):
#   EMAIL_ALERTA=equipe@exemplo.org ./infra/provisionar.sh
#
# Variáveis opcionais (padrão entre colchetes):
#   LOCAL [westus3]           região. Preferência: brazilsouth (dados de menores no Brasil), se houver cota.
#   SKU [B1]                  plano do App Service (F1 = custo zero, sem Always On).
#   SUFIXO [6 primeiros caracteres do id da assinatura]  nomes globais únicos e estáveis (ex.: app-apoioescolar-6e7462).
#   APP, KV, RG               nomes do Web App, Key Vault e Resource Group (ex.: reaproveitar um Web App existente).
#   GITHUB_REPO [GiantMazelliWasHere/apoio-escolar-periferico]
#   GITHUB_OWNER_ID, GITHUB_REPO_ID  IDs numéricos do GitHub para o subject OIDC com IDs (o script busca com o gh).
#   OPENROUTER_API_KEY        se definida, vai para o Key Vault (assistente de IA). Nunca é impressa.
#   LEITORES                  lista separada por vírgula (e-mails/UPNs ou object ids) que recebem Reader no RG.
#   ORCAMENTO [150]           orçamento mensal do RG, na moeda da conta, com aviso por e-mail em 80%.
#   CONFIGURAR_GITHUB [1]     grava as variáveis do pipeline no repositório com o gh CLI (se estiver logado).
set -euo pipefail

: "${EMAIL_ALERTA:?Defina EMAIL_ALERTA (e-mail que recebe alertas e o aviso de orçamento)}"

az config set extension.use_dynamic_install=yes_without_prompt core.only_show_errors=true >/dev/null

ASSINATURA_ID="$(az account show --query id -o tsv)"
TENANT_ID="$(az account show --query tenantId -o tsv)"
SUFIXO="${SUFIXO:-${ASSINATURA_ID:0:6}}"
LOCAL="${LOCAL:-westus3}"
SKU="${SKU:-B1}"
RG="${RG:-rg-apoioescolar}"
PLANO="${PLANO:-plan-apoioescolar}"
APP="${APP:-app-apoioescolar-$SUFIXO}"
KV="${KV:-kv-apoioescolar-$SUFIXO}"
LAW="${LAW:-log-apoioescolar}"
APPI="${APPI:-appi-apoioescolar}"
AG="${AG:-ag-apoioescolar}"
OIDC_IDENTIDADE="${OIDC_IDENTIDADE:-id-github-deploy}"
GITHUB_REPO="${GITHUB_REPO:-GiantMazelliWasHere/apoio-escolar-periferico}"
ORCAMENTO="${ORCAMENTO:-150}"
CONFIGURAR_GITHUB="${CONFIGURAR_GITHUB:-1}"
TAGS=(projeto=apoio-escolar-periferico disciplina=secure-devops ambiente=producao equipe=bitsnbytes gerenciado-por=infra-provisionar)

passo() { printf '\n==> %s\n' "$*"; }
existe() { "$@" >/dev/null 2>&1; }
# Atribuições de papel logo após criar uma identidade podem falhar até o Entra ID propagar.
com_retentativa() { local i; for i in 1 2 3 4 5 6; do "$@" && return 0; sleep 10; done; return 1; }

passo "Resource Group $RG ($LOCAL)"
az group create -n "$RG" -l "$LOCAL" --tags "${TAGS[@]}" -o none
RG_ID="$(az group show -n "$RG" --query id -o tsv)"

passo "Log Analytics $LAW (retenção 30 dias, teto diário de ingestão 0,5 GB)"
az monitor log-analytics workspace create -g "$RG" -n "$LAW" -l "$LOCAL" \
  --retention-time 30 --quota 0.5 --tags "${TAGS[@]}" -o none
LAW_ID="$(az monitor log-analytics workspace show -g "$RG" -n "$LAW" --query id -o tsv)"

passo "Application Insights $APPI (baseado no workspace)"
if ! existe az monitor app-insights component show -g "$RG" --app "$APPI"; then
  az monitor app-insights component create -g "$RG" --app "$APPI" -l "$LOCAL" \
    --workspace "$LAW_ID" --application-type web --tags "${TAGS[@]}" -o none
fi
APPI_CONEXAO="$(az monitor app-insights component show -g "$RG" --app "$APPI" --query connectionString -o tsv)"

passo "App Service Plan $PLANO (Linux $SKU)"
if ! existe az appservice plan show -g "$RG" -n "$PLANO"; then
  az appservice plan create -g "$RG" -n "$PLANO" -l "$LOCAL" --is-linux --sku "$SKU" --tags "${TAGS[@]}" -o none
fi

passo "Web App $APP (Python 3.12) com identidade gerenciada"
if ! existe az webapp show -g "$RG" -n "$APP"; then
  az webapp create -g "$RG" -p "$PLANO" -n "$APP" --runtime "PYTHON:3.12" --tags "${TAGS[@]}" -o none
fi
APP_ID="$(az webapp show -g "$RG" -n "$APP" --query id -o tsv)"
APP_PRINCIPAL="$(az webapp identity assign -g "$RG" -n "$APP" --query principalId -o tsv)"

passo "Endurecimento: só HTTPS, TLS 1.2, FTP e autenticação básica desligados, health check em /health"
az webapp update -g "$RG" -n "$APP" --https-only true -o none
ALWAYS_ON=true; [ "$SKU" = "F1" ] && ALWAYS_ON=false
az webapp config set -g "$RG" -n "$APP" \
  --min-tls-version 1.2 --ftps-state Disabled --http20-enabled true --always-on "$ALWAYS_ON" \
  --startup-file "sh startup.sh" --generic-configurations '{"healthCheckPath": "/health"}' -o none
for cred in ftp scm; do
  az resource update -g "$RG" --namespace Microsoft.Web --resource-type basicPublishingCredentialsPolicies \
    --parent "sites/$APP" -n "$cred" --set properties.allow=false -o none
done
az webapp log config -g "$RG" -n "$APP" --docker-container-logging filesystem -o none

passo "Key Vault $KV (RBAC, soft delete)"
if ! existe az keyvault show -n "$KV"; then
  az keyvault create -g "$RG" -n "$KV" -l "$LOCAL" --enable-rbac-authorization true \
    --retention-days 7 --tags "${TAGS[@]}" -o none
fi
KV_ID="$(az keyvault show -n "$KV" --query id -o tsv)"
EU_ID="$(az ad signed-in-user show --query id -o tsv)"
az role assignment create --assignee-object-id "$EU_ID" --assignee-principal-type User \
  --role "Key Vault Secrets Officer" --scope "$KV_ID" -o none
com_retentativa az role assignment create --assignee-object-id "$APP_PRINCIPAL" --assignee-principal-type ServicePrincipal \
  --role "Key Vault Secrets User" --scope "$KV_ID" -o none

passo "Segredos gerados direto no Key Vault (nunca impressos)"
gravar_se_faltar() { # nome valor
  if existe az keyvault secret show --vault-name "$KV" -n "$1"; then
    echo "   $1: já existe (mantido)"
  else
    com_retentativa az keyvault secret set --vault-name "$KV" -n "$1" --value "$2" -o none
    echo "   $1: criado"
  fi
}
gravar_se_faltar secret-key "$(openssl rand -hex 32)"
gravar_se_faltar integration-api-key "$(openssl rand -hex 24)"
# Chave Fernet (32 bytes em base64 url-safe): cifra o e-mail do responsável. Trocar a chave torna os e-mails ilegíveis.
gravar_se_faltar fernet-key "$(openssl rand -base64 32 | tr '+/' '-_')"
if [ -n "${OPENROUTER_API_KEY:-}" ]; then
  com_retentativa az keyvault secret set --vault-name "$KV" -n openrouter-api-key --value "$OPENROUTER_API_KEY" -o none
  echo "   openrouter-api-key: gravado"
fi

passo "Configurações do aplicativo (segredos por referência ao Key Vault)"
ref() { printf '@Microsoft.KeyVault(VaultName=%s;SecretName=%s)' "$KV" "$1"; }
CONFIG=(
  "APP_ENV=production"
  "SECRET_KEY=$(ref secret-key)"
  "INTEGRATION_API_KEY=$(ref integration-api-key)"
  "FERNET_KEY=$(ref fernet-key)"
  "DATABASE_URL=sqlite:////home/data/apoio-mvp.db"
  "PUBLIC_URL=https://$APP.azurewebsites.net"
  "SCM_DO_BUILD_DURING_DEPLOYMENT=true"
  "APPLICATIONINSIGHTS_CONNECTION_STRING=$APPI_CONEXAO"
)
if existe az keyvault secret show --vault-name "$KV" -n openrouter-api-key; then
  CONFIG+=("OPENROUTER_API_KEY=$(ref openrouter-api-key)")
fi
az webapp config appsettings set -g "$RG" -n "$APP" --settings "${CONFIG[@]}" -o none

passo "Logs do App Service no Log Analytics"
az monitor diagnostic-settings create -n diag-log-analytics --resource "$APP_ID" --workspace "$LAW_ID" \
  --logs '[{"category":"AppServiceHTTPLogs","enabled":true},{"category":"AppServiceConsoleLogs","enabled":true},{"category":"AppServicePlatformLogs","enabled":true}]' \
  --metrics '[{"category":"AllMetrics","enabled":true}]' -o none

passo "Grupo de ação e alertas"
az monitor action-group create -g "$RG" -n "$AG" --short-name apoioesc \
  --action email equipe "$EMAIL_ALERTA" --tags "${TAGS[@]}" -o none
AG_ID="$(az monitor action-group show -g "$RG" -n "$AG" --query id -o tsv)"
alerta() { # nome severidade condição descrição
  if existe az monitor metrics alert show -g "$RG" -n "$1"; then
    echo "   $1: já existe (mantido)"
  else
    az monitor metrics alert create -g "$RG" -n "$1" --scopes "$APP_ID" --severity "$2" \
      --condition "$3" --window-size 5m --evaluation-frequency 1m --auto-mitigate true \
      --action "$AG_ID" --description "$4" --tags "${TAGS[@]}" -o none
  fi
}
alerta alerta-health-check 0 "avg HealthCheckStatus < 100" "/health falhando por 5 minutos"
alerta alerta-erros-5xx    1 "total Http5xx > 5"          "Mais de 5 respostas 5xx em 5 minutos"
alerta alerta-lentidao     2 "avg HttpResponseTime > 3"   "Tempo médio de resposta acima de 3 s em 5 minutos"

passo "Orçamento mensal de $ORCAMENTO no Resource Group (aviso em 80%)"
INICIO="$(date -u +%Y-%m-01)T00:00:00Z"
FIM="$(date -u -d "$(date -u +%Y-%m-01) +1 year" +%Y-%m-01)T00:00:00Z"
az rest --method put \
  --url "https://management.azure.com${RG_ID}/providers/Microsoft.Consumption/budgets/orcamento-apoioescolar?api-version=2023-05-01" \
  --body "{\"properties\":{\"category\":\"Cost\",\"amount\":$ORCAMENTO,\"timeGrain\":\"Monthly\",
    \"timePeriod\":{\"startDate\":\"$INICIO\",\"endDate\":\"$FIM\"},
    \"notifications\":{\"real80\":{\"enabled\":true,\"operator\":\"GreaterThanOrEqualTo\",\"threshold\":80,
    \"thresholdType\":\"Actual\",\"contactEmails\":[\"$EMAIL_ALERTA\"]}}}}" -o none \
  || echo "   aviso: não foi possível criar o orçamento (algumas assinaturas não suportam); crie em Cost Management."

passo "Identidade do GitHub Actions (OIDC, sem segredo) com Website Contributor só no Web App"
# Identidade gerenciada (user-assigned) em vez de app registration: não exige permissão no Entra ID
# (basta Contributor no RG para criá-la) e não tem segredo nenhum.
if ! existe az identity show -g "$RG" -n "$OIDC_IDENTIDADE"; then
  az identity create -g "$RG" -n "$OIDC_IDENTIDADE" -l "$LOCAL" --tags "${TAGS[@]}" -o none
fi
OIDC_CLIENT_ID="$(az identity show -g "$RG" -n "$OIDC_IDENTIDADE" --query clientId -o tsv)"
OIDC_PRINCIPAL_ID="$(az identity show -g "$RG" -n "$OIDC_IDENTIDADE" --query principalId -o tsv)"

# O GitHub manda o "subject" do token em dois formatos, conforme a configuração da conta:
#   clássico:      repo:<dono>/<repo>:environment:production
#   com IDs fixos: repo:<dono>@<id-do-dono>/<repo>@<id-do-repo>:environment:production
# (o formato com IDs não muda se o repositório ou a conta forem renomeados). Cadastramos os dois.
SUBJECTS=("repo:${GITHUB_REPO}:environment:production")
if [ -z "${GITHUB_OWNER_ID:-}" ] || [ -z "${GITHUB_REPO_ID:-}" ]; then
  if command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then
    read -r GITHUB_OWNER_ID GITHUB_REPO_ID < <(gh api "repos/$GITHUB_REPO" --jq '"\(.owner.id) \(.id)"')
  else
    # Sem o gh: a API pública do GitHub dá os IDs (não são segredo; só funciona com repositório público).
    read -r GITHUB_OWNER_ID GITHUB_REPO_ID < <(curl -fsSL "https://api.github.com/repos/$GITHUB_REPO" \
      | jq -r '"\(.owner.id) \(.id)"' 2>/dev/null) || true
  fi
fi
if [ -n "${GITHUB_OWNER_ID:-}" ] && [ -n "${GITHUB_REPO_ID:-}" ]; then
  SUBJECTS+=("repo:${GITHUB_REPO%%/*}@${GITHUB_OWNER_ID}/${GITHUB_REPO#*/}@${GITHUB_REPO_ID}:environment:production")
else
  echo "   aviso: sem os IDs do repositório (repo privado sem gh?). Defina GITHUB_OWNER_ID e GITHUB_REPO_ID e rode de novo."
fi
EXISTENTES="$(az identity federated-credential list -g "$RG" --identity-name "$OIDC_IDENTIDADE" --query '[].subject' -o tsv)"
n=0
for subject in "${SUBJECTS[@]}"; do
  n=$((n + 1))
  if grep -qxF "$subject" <<< "$EXISTENTES"; then
    echo "   credencial federada já existe: $subject"
  else
    az identity federated-credential create -g "$RG" --identity-name "$OIDC_IDENTIDADE" -n "github-production-$n" \
      --issuer https://token.actions.githubusercontent.com --subject "$subject" \
      --audiences api://AzureADTokenExchange -o none
    echo "   credencial federada criada: $subject"
  fi
done
com_retentativa az role assignment create --assignee-object-id "$OIDC_PRINCIPAL_ID" --assignee-principal-type ServicePrincipal \
  --role "Website Contributor" --scope "$APP_ID" -o none

if [ -n "${LEITORES:-}" ]; then
  passo "Reader no Resource Group para professor e integrantes"
  IFS=',' read -ra LISTA <<< "$LEITORES"
  for quem in "${LISTA[@]}"; do
    az role assignment create --assignee "$(echo "$quem" | xargs)" --role Reader --scope "$RG_ID" -o none \
      && echo "   Reader: $quem" || echo "   aviso: não consegui atribuir Reader a $quem"
  done
fi

passo "Variáveis do pipeline no GitHub"
declare -A VARS=(
  [AZURE_CLIENT_ID]="$OIDC_CLIENT_ID"
  [AZURE_TENANT_ID]="$TENANT_ID"
  [AZURE_SUBSCRIPTION_ID]="$ASSINATURA_ID"
  [AZURE_WEBAPP_NAME]="$APP"
)
if [ "$CONFIGURAR_GITHUB" = "1" ] && command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then
  gh api -X PUT "repos/$GITHUB_REPO/environments/production" >/dev/null
  for nome in "${!VARS[@]}"; do gh variable set "$nome" --repo "$GITHUB_REPO" --body "${VARS[$nome]}"; done
  echo "   gravadas em $GITHUB_REPO (variáveis do repositório) e environment production criado."
else
  echo "   Rode (ou crie em Settings > Secrets and variables > Actions > Variables):"
  for nome in "${!VARS[@]}"; do echo "   gh variable set $nome --repo $GITHUB_REPO --body ${VARS[$nome]}"; done
  echo "   e crie o environment: Settings > Environments > New environment > production"
fi

passo "Pronto"
echo "   URL:          https://$APP.azurewebsites.net (o site sobe no primeiro deploy do pipeline)"
echo "   Health:       https://$APP.azurewebsites.net/health"
echo "   Key Vault:    $KV (segredos: $(az keyvault secret list --vault-name "$KV" --query '[].name' -o tsv | tr '\n' ' '))"
echo "   Para publicar: push na main ou Actions > CI/CD > Run workflow."

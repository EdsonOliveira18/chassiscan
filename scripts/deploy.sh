#!/usr/bin/env bash
set -Eeuo pipefail

ENVIRONMENT="${1:?uso: deploy.sh <staging|production> <tag>}"
TAG="${2:-latest}"
COMPOSE="docker-compose.prod.yml"
STATE_FILE=".deploy_state_${ENVIRONMENT}"

log() { echo "[$(date -u +%H:%M:%S)] $*"; }

log "Iniciando deploy | env=${ENVIRONMENT} tag=${TAG}"

# 1. Salva a versão atual para permitir rollback
CURRENT=$(docker inspect --format '{{index .Config.Image}}' chassiscan-api 2>/dev/null || echo "none")
echo "$CURRENT" > "$STATE_FILE"
log "Versão anterior registrada: ${CURRENT}"

# 2. Baixa a nova imagem antes de derrubar nada
export TAG GH_OWNER="${GITHUB_REPOSITORY_OWNER:-local}"
docker compose -f "$COMPOSE" pull api

# 3. Sobe com recreação controlada
docker compose -f "$COMPOSE" up -d --no-deps --force-recreate api

# 4. Aguarda o healthcheck ficar saudável (máx. 60s)
log "Aguardando health..."
for i in $(seq 1 20); do
  STATUS=$(docker inspect --format '{{.State.Health.Status}}' chassiscan-api 2>/dev/null || echo starting)
  [[ "$STATUS" == "healthy" ]] && { log "Aplicação saudável ✔"; exit 0; }
  sleep 3
done

log "ERRO: health check não passou em 60s"
exit 1

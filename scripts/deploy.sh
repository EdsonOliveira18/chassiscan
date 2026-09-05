#!/usr/bin/env bash
set -Eeuo pipefail

ENVIRONMENT="${1:?uso: deploy.sh <staging|production> [tag]}"
COMPOSE="docker-compose.prod.yml"
ENV_FILE="${ENV_FILE:-.env.prod}"
STATE_FILE=".deploy_state_${ENVIRONMENT}"
SERVICE="${SERVICE:-api}"
CONTAINER="${CONTAINER:-chassiscan-api}"

log() { echo "[$(date -u +%H:%M:%S)] $*"; }
lower() { tr '[:upper:]' '[:lower:]'; }

[[ -f "$ENV_FILE" ]] || { log "ERRO: ${ENV_FILE} não encontrado"; exit 1; }

# Carrega o .env.prod gerado pelo pipeline
set -a; source "$ENV_FILE"; set +a

# Precedência: argumento > .env.prod > latest
IMAGE_TAG="$(echo "${2:-${IMAGE_TAG:-latest}}" | lower)"
IMAGE_NAME="$(echo "${IMAGE_NAME:?IMAGE_NAME não definido}" | lower)"
GH_OWNER="$(echo "${GH_OWNER:-local}" | lower)"
export IMAGE_NAME IMAGE_TAG GH_OWNER TAG="$IMAGE_TAG"

DC=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE")

log "Deploy | env=${ENVIRONMENT} image=${IMAGE_NAME}:${IMAGE_TAG}"

# 1. Registra versão atual (imagem completa) para rollback
CURRENT="$(docker inspect --format '{{.Config.Image}}' "$CONTAINER" 2>/dev/null | lower || true)"
[[ -z "$CURRENT" ]] && CURRENT="none"
echo "$CURRENT" > "$STATE_FILE"
log "Versão anterior registrada: ${CURRENT}"

# 2. Puxa a nova imagem antes de derrubar nada
"${DC[@]}" pull "$SERVICE"

# 3. Recreação controlada
"${DC[@]}" up -d --no-deps --force-recreate "$SERVICE"

# 4. Healthcheck (máx. 60s)
log "Aguardando health..."
for _ in $(seq 1 20); do
  STATUS="$(docker inspect --format '{{.State.Health.Status}}' "$CONTAINER" 2>/dev/null || echo starting)"
  [[ "$STATUS" == "healthy" ]] && { log "Aplicação saudável ✔"; exit 0; }
  [[ "$STATUS" == "unhealthy" ]] && { log "ERRO: container unhealthy"; exit 1; }
  sleep 3
done

log "ERRO: health check não passou em 60s"
"${DC[@]}" logs --tail=50 "$SERVICE" || true
exit 1

#!/usr/bin/env bash
set -Eeuo pipefail

ENVIRONMENT="${1:?uso: rollback.sh <staging|production> [fallback_tag]}"
FALLBACK_TAG="${2:-latest}"
COMPOSE="docker-compose.prod.yml"
ENV_FILE="${ENV_FILE:-.env.prod}"
STATE_FILE=".deploy_state_${ENVIRONMENT}"
SERVICE="${SERVICE:-api}"
CONTAINER="${CONTAINER:-chassiscan-api}"

lower() { tr '[:upper:]' '[:lower:]'; }

[[ -f "$ENV_FILE" ]] || { echo "ERRO: ${ENV_FILE} não encontrado"; exit 1; }
set -a; source "$ENV_FILE"; set +a

IMAGE_NAME="$(echo "${IMAGE_NAME:?IMAGE_NAME não definido}" | lower)"
GH_OWNER="$(echo "${GH_OWNER:-local}" | lower)"

PREV=""
[[ -f "$STATE_FILE" ]] && PREV="$(tr -d '[:space:]' < "$STATE_FILE" | lower)"

# Resolve a tag alvo com fallback seguro
if [[ -z "$PREV" || "$PREV" == "none" || "$PREV" != *:* ]]; then
  echo "⚠ Sem versão anterior válida (valor='${PREV:-vazio}'). Usando fallback: ${FALLBACK_TAG}"
  TARGET_TAG="$(echo "$FALLBACK_TAG" | lower)"
else
  TARGET_TAG="${PREV##*:}"
fi
[[ -z "$TARGET_TAG" ]] && TARGET_TAG="latest"

IMAGE_TAG="$TARGET_TAG"
export IMAGE_NAME IMAGE_TAG GH_OWNER TAG="$IMAGE_TAG"

DC=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE")

echo "↩ Revertendo para: ${IMAGE_NAME}:${IMAGE_TAG}"
"${DC[@]}" pull "$SERVICE" || echo "⚠ pull falhou; tentando imagem local"
"${DC[@]}" up -d --no-deps --force-recreate "$SERVICE"

for _ in $(seq 1 20); do
  STATUS="$(docker inspect --format '{{.State.Health.Status}}' "$CONTAINER" 2>/dev/null || echo starting)"
  [[ "$STATUS" == "healthy" ]] && { echo "Rollback concluído ✔"; exit 0; }
  sleep 3
done

echo "FALHA CRÍTICA: rollback não estabilizou. Intervenção manual necessária."
"${DC[@]}" logs --tail=80 "$SERVICE" || true
exit 1

#!/usr/bin/env bash
set -Eeuo pipefail

ENVIRONMENT="${1:?uso: rollback.sh <staging|production>}"
STATE_FILE=".deploy_state_${ENVIRONMENT}"
COMPOSE="docker-compose.prod.yml"

[[ -f "$STATE_FILE" ]] || { echo "Sem estado anterior. Rollback abortado."; exit 1; }
PREV=$(cat "$STATE_FILE")
[[ "$PREV" == "none" ]] && { echo "Primeiro deploy: nada a reverter."; exit 1; }

echo "↩ Revertendo para: ${PREV}"
export TAG="${PREV##*:}"
docker compose -f "$COMPOSE" up -d --no-deps --force-recreate api

for i in $(seq 1 20); do
  [[ "$(docker inspect --format '{{.State.Health.Status}}' chassiscan-api)" == "healthy" ]] \
    && { echo "Rollback concluído ✔"; exit 0; }
  sleep 3
done

echo "FALHA CRÍTICA: rollback não estabilizou. Intervenção manual necessária."
exit 1

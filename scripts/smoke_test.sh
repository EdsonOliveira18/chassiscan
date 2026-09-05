#!/usr/bin/env bash
set -Eeuo pipefail

BASE="${1:-http://localhost:8000}"
FAILS=0

check() {
  local name="$1" path="$2" expected="$3"
  local code
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "${BASE}${path}" || echo 000)
  if [[ "$code" == "$expected" ]]; then
    echo "  ✔ ${name} (${code})"
  else
    echo "  ✘ ${name} — esperado ${expected}, recebido ${code}"
    FAILS=$((FAILS+1))
  fi
}

echo "== Smoke tests em ${BASE} =="
check "Health"          "/health"          200
check "Métricas"        "/metrics"         200
check "Docs OpenAPI"    "/docs"            200
check "Rota inexistente" "/rota-invalida"  404

echo "-----------------------------"
if (( FAILS > 0 )); then
  echo "RESULTADO: ${FAILS} falha(s) → acionando rollback"
  exit 1
fi
echo "RESULTADO: todos os smoke tests passaram ✔"

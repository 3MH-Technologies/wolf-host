#!/bin/bash
set -euo pipefail

echo "Checking Wolf Host services health..."

# Production compose publishes only nginx (80/443), so probes go through nginx.
# Only 2xx counts as healthy — a 301 redirect from port 80 to https is not enough.
check_service() {
  local name="$1"
  shift
  local url code
  for url in "$@"; do
    code=$(curl -ksS -o /dev/null -w '%{http_code}' --max-time 10 "$url" 2>/dev/null) || code="000"
    case "$code" in
      2??)
        echo "  [OK] $name ($url)"
        return 0
        ;;
    esac
  done
  echo "  [FAIL] $name"
  return 1
}

FAILED=0

check_service "Backend API" "https://localhost/api/health" "http://localhost/api/health" || FAILED=1
check_service "Frontend" "https://localhost/" "http://localhost/" || FAILED=1

if docker compose exec -T postgres pg_isready -U "${POSTGRES_USER:-wolfhost}" > /dev/null 2>&1; then
  echo "  [OK] PostgreSQL"
else
  echo "  [FAIL] PostgreSQL"
  FAILED=1
fi

if docker compose exec -T redis redis-cli -a "${REDIS_PASSWORD:-}" ping > /dev/null 2>&1; then
  echo "  [OK] Redis"
else
  echo "  [FAIL] Redis"
  FAILED=1
fi

if [ "$FAILED" -eq 0 ]; then
  echo "All services healthy."
  exit 0
else
  echo "One or more services are unhealthy."
  exit 1
fi

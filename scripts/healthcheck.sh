#!/bin/bash
set -euo pipefail

echo "Checking Wolf Host services health..."

check_service() {
  local name="$1"
  local url="$2"
  if curl -sf "$url" > /dev/null 2>&1; then
    echo "  [OK] $name"
  else
    echo "  [FAIL] $name"
    return 1
  fi
}

FAILED=0

check_service "Backend API" "http://localhost:8000/api/health" || FAILED=1
check_service "Frontend" "http://localhost:3000" || FAILED=1

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

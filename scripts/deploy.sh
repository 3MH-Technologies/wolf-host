#!/bin/bash
set -euo pipefail

if [ ! -f .env ]; then
  echo "Missing .env file. Copy .env.example to .env and fill in the values first."
  exit 1
fi

# nginx requires certificates at startup — generate a self-signed pair if none
# exists yet (replace with a real certificate, e.g. Let's Encrypt, for production).
if [ ! -f nginx/certs/fullchain.pem ] || [ ! -f nginx/certs/privkey.pem ]; then
  echo "No SSL certificate found in nginx/certs/ — generating a self-signed one..."
  mkdir -p nginx/certs
  openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
    -keyout nginx/certs/privkey.pem \
    -out nginx/certs/fullchain.pem \
    -subj "/CN=${TLS_CN:-localhost}"
  echo "Self-signed certificate created (valid 365 days)."
fi

echo "Building and starting Wolf Host..."
docker compose build
docker compose up -d postgres redis
echo "Waiting for database..."
sleep 8

docker compose run --rm backend alembic upgrade head || \
  echo "No Alembic versions yet — the backend will create the schema on startup."

docker compose up -d

echo "Waiting for the backend to initialize the database schema..."
for _ in $(seq 1 60); do
  if docker compose exec -T backend curl -fsS http://localhost:8000/api/health > /dev/null 2>&1; then
    break
  fi
  sleep 2
done

docker compose run --rm backend python -m app.db.seed

echo "Wolf Host is starting. Check status with: docker compose ps"
echo "Check health with: ./scripts/healthcheck.sh"

#!/bin/bash
set -euo pipefail

if [ ! -f .env ]; then
  echo "Missing .env file. Copy .env.example to .env and fill in the values first."
  exit 1
fi

echo "Building and starting Wolf Host..."
docker compose build
docker compose up -d postgres redis
echo "Waiting for database..."
sleep 8

docker compose run --rm backend alembic upgrade head
docker compose run --rm backend python -m app.db.seed

docker compose up -d

echo "Wolf Host is starting. Check status with: docker compose ps"

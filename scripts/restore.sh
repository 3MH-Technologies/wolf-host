#!/bin/bash
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: $0 <db_backup.sql.gz> <bots_storage_backup.tar.gz>"
  exit 1
fi

DB_BACKUP="$1"
STORAGE_BACKUP="$2"

source .env

echo "Restoring PostgreSQL database from $DB_BACKUP..."
gunzip -c "$DB_BACKUP" | docker compose exec -T postgres psql -U "$POSTGRES_USER" "$POSTGRES_DB"

echo "Restoring bots storage volume from $STORAGE_BACKUP..."
docker run --rm \
  -v wolfhost_bots_storage:/data \
  -v "$(pwd)/$(dirname "$STORAGE_BACKUP"):/backup" \
  alpine sh -c "rm -rf /data/* && tar xzf /backup/$(basename "$STORAGE_BACKUP") -C /data"

echo "Restore completed. Restart services with: docker compose restart"

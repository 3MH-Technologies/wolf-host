#!/bin/bash
set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"

source .env

echo "Backing up PostgreSQL database..."
docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$BACKUP_DIR/db_${TIMESTAMP}.sql.gz"

echo "Backing up bots storage volume..."
docker run --rm \
  -v wolfhost_bots_storage:/data \
  -v "$(pwd)/$BACKUP_DIR:/backup" \
  alpine tar czf "/backup/bots_storage_${TIMESTAMP}.tar.gz" -C /data .

echo "Backup completed:"
echo "  - $BACKUP_DIR/db_${TIMESTAMP}.sql.gz"
echo "  - $BACKUP_DIR/bots_storage_${TIMESTAMP}.tar.gz"

find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +14 -delete
find "$BACKUP_DIR" -name "bots_storage_*.tar.gz" -mtime +14 -delete

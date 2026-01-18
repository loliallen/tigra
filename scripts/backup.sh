#!/bin/bash

# Скрипт для автоматического дампа базы данных
# Используется для планирования через cron

set -e

# Переходим в директорию проекта
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "Starting database dump at $(date)"

# Создаем дамп
docker exec tigra-db-1 sh -c "pg_dump db > dump.sql"
docker cp tigra-db-1:/dump.sql dump.sql

# Читаем переменные и отправляем в Telegram
BOT_TOKEN=$(grep '^DUMP_BOT_TOKEN=' .env | cut -d= -f2-)
BOT_CHAT_ID=$(grep '^DUMP_BOT_CHAT_ID=' .env | cut -d= -f2-)

echo "Sending to Telegram - BOT_TOKEN: $BOT_TOKEN, BOT_CHAT_ID: $BOT_CHAT_ID"

curl -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendDocument?chat_id=$BOT_CHAT_ID" \
  --form "document=@dump.sql;type=text/csv" \
  -H "Content-Type: multipart/form-data"

# Удаляем дамп
rm dump.sql

echo "Database dump completed successfully at $(date)"

#!/bin/bash

# Извлекаем хост и порт из DATABASE_URL
DB_HOST=$(echo $DATABASE_URL | sed -E 's|.*://[^@]+@([^:/]+):([0-9]+)/.*|\1|')
DB_PORT=$(echo $DATABASE_URL | sed -E 's|.*://[^@]+@([^:/]+):([0-9]+)/.*|\2|')

echo "🔄 Ждём, пока БД станет доступна..."

while ! nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 1
done

echo "✅ БД доступна, продолжаем"
flask db upgrade
flask create-superuser
exec flask run --host=0.0.0.0 --port=5000
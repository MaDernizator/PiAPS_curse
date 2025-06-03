#!/bin/bash

echo "🔄 Ждём, пока БД станет доступна ($DB_HOST:$DB_PORT)..."
while ! nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 1
done

echo "✅ БД доступна, продолжаем"

flask db upgrade
flask create-superuser

exec flask run --host=0.0.0.0 --port=5000
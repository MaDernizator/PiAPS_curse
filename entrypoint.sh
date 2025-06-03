#!/bin/bash

echo "🔄 Ждём, пока БД станет доступна..."
while ! nc -z db 5432; do
  sleep 1
done

echo "✅ БД доступна, продолжаем"

flask db upgrade
flask create-superuser

# Запускаем сервер
exec flask run --host=0.0.0.0 --port=5000

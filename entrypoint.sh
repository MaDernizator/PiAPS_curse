#!/bin/bash

echo "🔄 Ждём, пока БД станет доступна ($DB_HOST:$DB_PORT)..."
while ! nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 1
done

echo "✅ БД доступна, запускаем миграции"
flask db upgrade

echo "⌛ Ждём завершения миграций"
sleep 10  # ⬅️ Дай миграциям немного времени

echo "👤 Создание суперпользователя"
flask create-superuser

echo "🚀 Запуск сервера"
exec flask run --host=0.0.0.0 --port=5000
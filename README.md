# PiAPS_curse

## Telegram Bot

- `/login` – интерактивная авторизация через e‑mail и пароль
- `/notifications` – вручную выводит непрочитанные уведомления

### Запуск

   - `TELEGRAM_TOKEN` – токен вашего бота
   - `API_URL` – адрес запущенного приложения (по умолчанию `http://localhost:5000`)
   - `python telegram_bot.py

При запуске через Docker `entrypoint.sh` автоматически стартует бота,
если задана переменная окружения `TELEGRAM_TOKEN`.


## Консольный клиент

   ```bash
   python console_client.py --email admin@example.com --password admin --url https://example.com
   ```
   Для непрерывного отслеживания новых записей используйте флаг `--watch`.

Клиент использует переменную окружения `API_URL` (по умолчанию
`http://localhost:5000`) для подключения к запущенному приложению.

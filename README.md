# PiAPS_curse

This project is a Flask-based API and web application. A simple Telegram bot is provided to interact with the same API.

## Telegram bot

The bot allows a user to authenticate using the `/login` command and fetch notifications via `/notifications`.

### Running the bot

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Export required variables:
   ```bash
   export TELEGRAM_BOT_TOKEN=<your_bot_token>
   export API_URL=http://localhost:5000  # change if API hosted elsewhere
   ```
3. Start the bot:
   ```bash
   python bot/telegram_bot.py
   ```

The bot uses the same endpoints as the web application and requires the API server to be running.

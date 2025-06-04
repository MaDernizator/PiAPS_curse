import logging
import os
from typing import Tuple

import requests
from telegram import Update
from telegram.ext import (ApplicationBuilder, CommandHandler, ContextTypes,
                          ConversationHandler, MessageHandler, filters)

API_URL = os.getenv("API_URL", "http://localhost:5000")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOGIN_EMAIL, LOGIN_PASSWORD = range(2)

user_tokens = {}


def login_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    update.message.reply_text("Введите email")
    return LOGIN_EMAIL


def login_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['email'] = update.message.text.strip()
    update.message.reply_text("Введите пароль")
    return LOGIN_PASSWORD


def login_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    password = update.message.text.strip()
    email = context.user_data.get('email')
    resp = requests.post(f"{API_URL}/api/auth/login", json={"email": email, "password": password})
    if resp.status_code == 200:
        data = resp.json()
        user_tokens[update.effective_user.id] = data['access_token']
        update.message.reply_text("Успешный вход")
    else:
        update.message.reply_text("Ошибка авторизации")
    return ConversationHandler.END


def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    update.message.reply_text("Отменено")
    return ConversationHandler.END


def get_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    token = user_tokens.get(update.effective_user.id)
    if not token:
        update.message.reply_text("Сначала выполните /login")
        return
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_URL}/api/notifications/", headers=headers)
    if resp.status_code == 200:
        notifications = resp.json()
        if not notifications:
            update.message.reply_text("Новых уведомлений нет")
        else:
            for n in notifications:
                update.message.reply_text(f"{n['sent_at']}: {n['event']}")
    else:
        update.message.reply_text("Ошибка получения уведомлений")


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set")
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler('login', login_start)],
        states={
            LOGIN_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_email)],
            LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    application.add_handler(conv)
    application.add_handler(CommandHandler('notifications', get_notifications))

    application.run_polling()


if __name__ == '__main__':
    main()

import os
import logging
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

API_URL = os.getenv("API_URL", "http://localhost:5000")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation states
LOGIN_EMAIL, LOGIN_PASSWORD = range(2)

# In-memory store for user tokens and scheduled jobs
user_tokens = {}
user_jobs = {}


async def poll_notifications(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.data["chat_id"]
    token = user_tokens.get(chat_id)
    if not token:
        return
    try:
        r = requests.get(
            f"{API_URL}/api/notifications/?unread=1",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if r.status_code == 200:
            for n in r.json():
                message = n.get("message") or n.get("event")
                await context.bot.send_message(chat_id=chat_id, text=message)
                requests.put(
                    f"{API_URL}/api/notifications/{n['id']}/view",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10,
                )
    except Exception:
        logger.exception("Failed to poll notifications")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать! Используйте /login для входа. После входа уведомления будут приходить автоматически."
    )

async def login_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите email:")
    return LOGIN_EMAIL

async def login_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['email'] = update.message.text.strip()
    await update.message.reply_text("Введите пароль:")
    return LOGIN_PASSWORD

async def login_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = context.user_data.get('email')
    password = update.message.text.strip()
    try:
        r = requests.post(
            f"{API_URL}/api/auth/login",
            json={"email": email, "password": password},
            timeout=10,
        )
        if r.status_code == 200:
            tokens = r.json()
            user_tokens[update.effective_user.id] = tokens['access_token']
            await update.message.reply_text("Успешный вход! Теперь уведомления будут приходить автоматически.")
            # start background polling for this user
            if context.job_queue:
                # cancel existing job if any
                old_job = user_jobs.get(update.effective_user.id)
                if old_job:
                    old_job.schedule_removal()
                job = context.job_queue.run_repeating(
                    poll_notifications,
                    interval=60,
                    first=0,
                    data={'chat_id': update.effective_user.id},
                )
                user_jobs[update.effective_user.id] = job
        else:
            await update.message.reply_text("Ошибка авторизации")
    except Exception as e:
        logger.exception("Login failed")
        await update.message.reply_text("Ошибка подключения к серверу")
    return ConversationHandler.END

async def login_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Авторизация отменена")
    return ConversationHandler.END

async def notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = user_tokens.get(update.effective_user.id)
    if not token:
        await update.message.reply_text("Сначала выполните /login")
        return
    try:
        r = requests.get(
            f"{API_URL}/api/notifications/?unread=1",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if r.status_code == 200:
            notifs = r.json()
            if not notifs:
                await update.message.reply_text("Нет новых уведомлений")
            else:
                messages = [n.get('message') or n['event'] for n in notifs]
                await update.message.reply_text("\n".join(messages))
                # Mark notifications as viewed
                for n in notifs:
                    requests.put(
                        f"{API_URL}/api/notifications/{n['id']}/view",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=10,
                    )
        else:
            await update.message.reply_text("Ошибка при получении уведомлений")
    except Exception:
        logger.exception("Failed to fetch notifications")
        await update.message.reply_text("Ошибка подключения к серверу")

def main():
    if not TELEGRAM_TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN not set")
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('login', login_start)],
        states={
            LOGIN_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_email)],
            LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_password)],
        },
        fallbacks=[CommandHandler('cancel', login_cancel)],
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('notifications', notifications))

    application.run_polling()

if __name__ == '__main__':
    main()

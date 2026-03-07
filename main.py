#at least 5 commands for the bot and spanish version too.
from dotenv import load_dotenv
import os
from telegram.ext import CommandHandler, Application, ContextTypes, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import psycopg2
from psycopg2.extras import RealDictCursor
import asyncio
import logging
from datetime import datetime, timedelta
import pytz

load_dotenv(override=True)
#Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
#Specific logger for the application
logger = logging.getLogger(__name__)
# Database connection parameters
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# Initialize the scheduler
scheduler = AsyncIOScheduler()

#initialize the database and create the reminders table if it doesn't exist
def init_db():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            message TEXT NOT NULL,
            remind_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

#Commands start here

user_languages = {}

TEXTS = {
    "en": {
        "setreminder_success": "✅ Reminder set! ID: {id}\n⏰ I'll remind you at {time}",
        "setreminder_usage": "Usage: /setreminder <message> <time>\nExample: /setreminder Call the dentist 30m",
        "no_reminders": "You have no active reminders!",
        "reminders_header": "🔔 Your active reminders:\n\n",
        "reminder_row": "ID: {id} - {message} at {time}\n",
        "reminder_prefix": "🔔 Reminder:",
        "delete_usage": "Usage: /deletereminder <id>",
        "delete_success": "✅ Reminder {id} deleted!",
        "clearall_success": "✅ All your reminders have been deleted",
        "help": (
            "🔔 *IRemindr - Commands*\n\n"
            "/setreminder `<message> <time>` — Set a reminder\n"
            "Example: `/setreminder Call the dentist 30m`\n\n"
            "/listreminders — Show your active reminders\n\n"
            "/deletereminder `<id>` — Delete a reminder by ID\n"
            "Example: `/deletereminder 3`\n\n"
            "/clearall — Delete all your reminders\n\n"
            "⏰ *Time formats:* `30m` · `2h` · `1d`"
        ),
    },
    "es": {
        "setreminder_success": "✅ Recordatorio creado! ID: {id}\n⏰ Te recuerdo a las {time}",
        "setreminder_usage": "Uso: /recordatorio <mensaje> <tiempo>\nEjemplo: /recordatorio Llamar al dentista 30m",
        "no_reminders": "No tenés recordatorios activos!",
        "reminders_header": "🔔 Tus recordatorios activos:\n\n",
        "reminder_row": "ID: {id} - {message} a las {time}\n",
        "reminder_prefix": "🔔 Recordatorio:",
        "delete_usage": "Uso: /eliminar <id>",
        "delete_success": "✅ Recordatorio {id} eliminado!",
        "clearall_success": "✅ Todos tus recordatorios fueron eliminados",
        "help": (
            "🔔 *IRemindr - Comandos*\n\n"
            "/recordatorio `<mensaje> <tiempo>` — Crear un recordatorio\n"
            "Ejemplo: `/recordatorio Llamar al dentista 30m`\n\n"
            "/misrecordatorios — Ver tus recordatorios activos\n\n"
            "/eliminar `<id>` — Eliminar un recordatorio por ID\n"
            "Ejemplo: `/eliminar 3`\n\n"
            "/eliminartodo — Eliminar todos tus recordatorios\n\n"
            "⏰ *Formatos de tiempo:* `30m` · `2h` · `1d`"
        ),
    }
}

async def language_selector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "lang_en":
        user_languages[query.from_user.id] = "en"
        await query.edit_message_text("🇺🇸 English selected! Use /setreminder to get started.")
    elif query.data == "lang_es":
        user_languages[query.from_user.id] = "es"
        await query.edit_message_text("🇪🇸 Español seleccionado! Usá /recordatorio para empezar.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
        InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome to IRemindr! Choose your language:\nBienvenido a IRemindr! Elegi el lenguaje:", reply_markup=reply_markup)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_languages.get(update.message.from_user.id, "en")
    await update.message.reply_text(TEXTS[lang]["help"], parse_mode="Markdown")

# Helper function to parse time strings like '30m', '2h', '1d' into datetime objects
def parse_time(time_str):
    unit = time_str[-1]
    amount = int(time_str[:-1])
    tz = pytz.timezone("America/Argentina/Buenos_Aires")
    now = datetime.now(tz)
    if unit == 'm':
        return now + timedelta(minutes=amount)
    elif unit == 'h':
        return now + timedelta(hours=amount)
    elif unit == 'd':
        return now + timedelta(days=amount)
    else:
        raise ValueError("Invalid time format. Use 30m, 2h or 1d")

# Define send_reminder function to send the reminder message
async def send_reminder(bot, user_id, message, lang="en"):
    prefix = TEXTS[lang]["reminder_prefix"]
    await bot.send_message(chat_id=user_id, text=f"{prefix} {message}").capitalize()

async def setreminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_languages.get(update.message.from_user.id, "en")
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(TEXTS[lang]["setreminder_usage"])
        return
    message = ' '.join(context.args[:-1])
    remind_at = parse_time(context.args[-1])
    # Save the reminder to the database
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute("INSERT INTO reminders (user_id, message, remind_at) VALUES (%s, %s, %s) RETURNING id",
                (update.message.from_user.id, message, remind_at))
    reminder_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    await update.message.reply_text(TEXTS[lang]["setreminder_success"].format(id=reminder_id, time=remind_at.strftime('%H:%M')))
    # Schedule the reminder
    if not scheduler.running:
        scheduler.start()
    scheduler.add_job(send_reminder, 'date', run_date=remind_at,
                      args=[context.bot, update.message.from_user.id, message, lang])
    # Log the scheduled reminder
    logger.info(f"Scheduled reminder for user {update.message.from_user.id} at {remind_at} with message: {message}")

# I will work on this tomorrow i tried to put some texts to make it more readable. 06/03/26

async def listreminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_languages.get(update.message.from_user.id, "en")
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
                SELECT * FROM reminders 
                WHERE user_id = %s AND remind_at > NOW()
                """, (update.message.from_user.id,))
    reminders = cur.fetchall()
    cur.close()
    conn.close()
    if not reminders:
        await update.message.reply_text(TEXTS[lang]["no_reminders"])
        return
    text = TEXTS[lang]["reminders_header"]
    for r in reminders:
        text += TEXTS[lang]["reminder_row"].format(
            id=r['id'],
            message=r['message'],
            time=r['remind_at'].strftime('%H:%M %d/%m/%Y')
        )
    await update.message.reply_text(text)

# Create a command to delete an specific reminder with the id
async def deletereminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_languages.get(update.message.from_user.id, "en")
    # If it's not used right reply this
    if not context.args:
        await update.message.reply_text(TEXTS[lang]["delete_usage"])
        return
    # Connect to DB
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor(cursor_factory=RealDictCursor)
    reminder_id = int(context.args[0])
    cur.execute("DELETE FROM reminders WHERE id = %s AND user_id = %s", (reminder_id, update.message.from_user.id))
    # Commit because we changed the DB
    conn.commit()
    cur.close()
    conn.close()
    # Reply this
    await update.message.reply_text(TEXTS[lang]["delete_success"].format(id=reminder_id))

# Command to Clear all the reminders
async def clearall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_languages.get(update.message.from_user.id, "en")
    # Connect to the DB
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    # Cursor
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("DELETE FROM reminders WHERE user_id = %s", (update.message.from_user.id,))
    conn.commit() # Needed to commit for sure
    cur.close()
    conn.close()
    # Reply this
    await update.message.reply_text(TEXTS[lang]["clearall_success"])

# Main with all the app builder and command handler stuff
def main():
    print("Starting bot...")
    app = Application.builder().token(os.getenv("TELEGRAM_API_KEY")).build()
    # English commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("setreminder", setreminder))
    app.add_handler(CommandHandler("listreminders", listreminders))
    app.add_handler(CommandHandler("deletereminder", deletereminder))
    app.add_handler(CommandHandler("clearall", clearall))
    # Spanish commands
    app.add_handler(CommandHandler("ayuda", help))
    app.add_handler(CommandHandler("recordatorio", setreminder))
    app.add_handler(CommandHandler("misrecordatorios", listreminders))
    app.add_handler(CommandHandler("eliminar", deletereminder))
    app.add_handler(CommandHandler("eliminartodo", clearall))
    # Callback for language selector buttons
    app.add_handler(CallbackQueryHandler(language_selector))
    init_db()
    app.run_polling()

if __name__ == "__main__":
    main()
# End
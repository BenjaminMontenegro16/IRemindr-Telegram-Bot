#at least 5 commands for the bot and spanish version too.
from multiprocessing import context

from dotenv import load_dotenv
import os
from telegram.ext import CommandHandler, Application, ContextTypes
from telegram import Update
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import psycopg2
from psycopg2.extras import RealDictCursor
import asyncio
import logging
from datetime import datetime, timedelta

load_dotenv()
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your reminder bot. Use /setreminder to set a reminder.")

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("...")


# Helper function to parse time strings like '30m', '2h', '1d' into datetime objects

def parse_time(time_str):
    unit = time_str[-1]        # último caracter: 'm', 'h', o 'd'
    amount = int(time_str[:-1]) # todo menos el último: '30'
    
    if unit == 'm':
        return datetime.now() + timedelta(minutes=amount)
    elif unit == 'h':
        return datetime.now() + timedelta(hours=amount)
    elif unit == 'd':
        return datetime.now() + timedelta(days=amount)
    else:
        raise ValueError("Invalid time format. Use 30m, 2h or 1d")

# Define send_reminder function to send the reminder message
async def send_reminder(bot, user_id, message):
    await bot.send_message(chat_id=user_id, text=f"🔔 Reminder: {message}")

async def setreminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Please provide the reminder in the format: /setreminder <message> <time>")
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
    await update.message.reply_text(f"Reminder set successfully! ID: {reminder_id}")
    # Schedule the reminder    
    scheduler.add_job(send_reminder, 'date', run_date=remind_at, 
        args=[context.bot, update.message.from_user.id, message])
    # Log the scheduled reminder
    logger.info(f"Scheduled reminder for user {update.message.from_user.id} at {remind_at} with message: {message}")

async def listreminders(update:Update, context: ContextTypes.DEFAULT_TYPE):
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
# I will work on this tomorrow i tried to put some texts to make it more readable.
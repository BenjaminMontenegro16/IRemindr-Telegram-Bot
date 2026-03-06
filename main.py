from dotenv import load_dotenv
import os
from telegram.ext import CommandHandler, Application, ContextTypes
from telegram import Update
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import psycopg2
from psycopg2.extras import RealDictCursor
import asyncio
import logging

load_dotenv()



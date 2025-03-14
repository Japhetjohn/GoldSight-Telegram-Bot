import asyncio
import os
import requests
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from fastapi import FastAPI, Request
import uvicorn
from database import init_db
from helpers import fetch_auto_signals

# Load environment variables
load_dotenv()
API_TOKEN = os.getenv("MAIN_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
VIP_CHANNEL = int(os.getenv("VIP_CHANNEL_ID"))
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8080))

# Validate environment variables
if not all([API_TOKEN, ADMIN_ID, VIP_CHANNEL, ALPHA_VANTAGE_KEY, WEBHOOK_URL]):
    raise ValueError("❌ Missing required environment variables!")

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
app = FastAPI()

# Set up webhook path
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"

@app.post(WEBHOOK_PATH)
async def handle_update(request: Request):
    """Receive webhook updates from Telegram."""
    update = await request.json()
    telegram_update = Update(**update)
    await dp.feed_update(bot, telegram_update)
    return {"ok": True}

async def on_startup():
    """Set webhook on startup and start auto signals."""
    webhook_url = f"{WEBHOOK_URL}{WEBHOOK_PATH}"
    response = requests.get(f"https://api.telegram.org/bot{API_TOKEN}/setWebhook?url={webhook_url}")
    print("✅ Webhook Set:", response.json())

    try:
        await bot.send_message(VIP_CHANNEL, "Bot started successfully via Webhook!")
    except Exception as e:
        print(f"🚨 Failed to access VIP channel ({VIP_CHANNEL}): {e}")
        await bot.send_message(ADMIN_ID, f"VIP channel error: {e}")

    asyncio.create_task(fetch_auto_signals(bot, VIP_CHANNEL, ADMIN_ID, ALPHA_VANTAGE_KEY))

async def on_shutdown():
    """Delete webhook on shutdown."""
    response = requests.get(f"https://api.telegram.org/bot{API_TOKEN}/deleteWebhook")
    print("🛑 Webhook Deleted:", response.json())

if __name__ == "__main__":
    init_db()  # Initialize database
    asyncio.run(on_startup())
    uvicorn.run(app, host="0.0.0.0", port=PORT)
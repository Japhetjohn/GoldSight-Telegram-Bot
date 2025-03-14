import asyncio
import requests
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from fastapi import FastAPI, Request
import uvicorn

# Load environment variables
API_TOKEN = os.getenv("MAIN_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
VIP_CHANNEL = os.getenv("VIP_CHANNEL_ID")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8080))

# Logger setup
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
app = FastAPI()

# Webhook path
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"

@app.post(WEBHOOK_PATH)
async def handle_update(request: Request):
    """Receive webhook updates from Telegram."""
    update_data = await request.json()
    telegram_update = Update(**update_data)
    await dp.process_update(telegram_update)
    return {"ok": True}

async def fetch_auto_signals():
    """Fetch signals from Alpha Vantage and send to VIP_CHANNEL."""
    while True:
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=XAUUSD&apikey={ALPHA_VANTAGE_KEY}"
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()

            if "Global Quote" in data and data["Global Quote"].get("05. price"):
                price = data["Global Quote"]["05. price"]
                signal = f"📈 XAUUSD Latest: {price} (Auto)"
                
                await bot.send_message(VIP_CHANNEL, signal)
            else:
                await bot.send_message(ADMIN_ID, "Alpha Vantage returned empty data!")

        except Exception as e:
            logging.error(f"Signal error: {e}")
            await bot.send_message(ADMIN_ID, f"Signal fetch error: {e}")

        await asyncio.sleep(300)

async def on_startup():
    """Set webhook and start background tasks."""
    webhook_url = f"{WEBHOOK_URL}{WEBHOOK_PATH}"
    requests.get(f"https://api.telegram.org/bot{API_TOKEN}/setWebhook?url={webhook_url}")

    await bot.send_message(ADMIN_ID, "Bot started successfully!")
    asyncio.create_task(fetch_auto_signals())

async def on_shutdown():
    """Delete webhook on shutdown."""
    requests.get(f"https://api.telegram.org/bot{API_TOKEN}/deleteWebhook")

if __name__ == "__main__":
    asyncio.run(on_startup())
    uvicorn.run(app, host="0.0.0.0", port=PORT)
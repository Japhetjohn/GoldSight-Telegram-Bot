import asyncio
import requests
import os
import threading
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from aiogram.utils.executor import start_webhook
from dotenv import load_dotenv
from fastapi import FastAPI, Request

# Load environment variables
load_dotenv()
API_TOKEN = os.getenv("MAIN_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
VIP_CHANNEL = os.getenv("VIP_CHANNEL_ID")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")

# Validate environment variables
if not all([API_TOKEN, ADMIN_ID, VIP_CHANNEL, ALPHA_VANTAGE_KEY]):
    raise ValueError("Missing required environment variables!")

# Convert VIP_CHANNEL to int
try:
    VIP_CHANNEL = int(VIP_CHANNEL)
except ValueError:
    raise ValueError("VIP_CHANNEL_ID must be a valid integer!")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
app = FastAPI()

WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Example: "https://your-public-url.loca.lt"
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
PORT = int(os.getenv("PORT", 8080))

@app.post(WEBHOOK_PATH)
async def handle_update(request: Request):
    """Receive webhook updates from Telegram."""
    update = await request.json()
    telegram_update = Update(**update)
    await dp.process_update(telegram_update)
    return {"ok": True}

async def fetch_auto_signals():
    """Fetch signals from Alpha Vantage and send them to VIP_CHANNEL."""
    max_retries = 3
    base_delay = 5
    last_signal = "XAUUSD Latest: N/A (Fallback)"

    while True:
        for attempt in range(max_retries):
            try:
                url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=XAUUSD&apikey={ALPHA_VANTAGE_KEY}"
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                data = response.json()

                print(f"Alpha Vantage Response: {data}")

                if "Global Quote" in data and data["Global Quote"].get("05. price"):
                    price = data["Global Quote"]["05. price"]
                    signal = f"📈 XAUUSD Latest: {price} (Auto)"
                    
                    print(f"Sending to VIP channel ({VIP_CHANNEL}): {signal}")
                    await bot.send_message(VIP_CHANNEL, signal)  # ✅ Send only to VIP_CHANNEL
                    last_signal = signal
                    break
                else:
                    print("🚨 No valid data from Alpha Vantage!")
                    await bot.send_message(ADMIN_ID, "Alpha Vantage returned empty data!")
                    break

            except Exception as e:
                print(f"Signal error (attempt {attempt + 1}): {e}")
                
                if attempt == max_retries - 1:
                    print(f"⚠️ Sending fallback signal to VIP channel ({VIP_CHANNEL}): {last_signal}")
                    await bot.send_message(VIP_CHANNEL, last_signal)
                    await bot.send_message(ADMIN_ID, f"Alpha Vantage failed after {max_retries} attempts: {e}")
                else:
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)

        print("Waiting 5 minutes for next signal...")
        await asyncio.sleep(300)

async def on_startup():
    """Set webhook on startup."""
    webhook_url = f"{WEBHOOK_URL}{WEBHOOK_PATH}"
    response = requests.get(f"https://api.telegram.org/bot{API_TOKEN}/setWebhook?url={webhook_url}")
    print("✅ Webhook Set:", response.json())

    try:
        await bot.send_message(VIP_CHANNEL, "Bot started successfully via Webhook!")
        print(f"🎉 VIP channel ({VIP_CHANNEL}) is accessible!")
    except Exception as e:
        print(f"🚨 Failed to access VIP channel ({VIP_CHANNEL}): {e}")
        await bot.send_message(ADMIN_ID, f"VIP channel error: {e}")

    asyncio.create_task(fetch_auto_signals())

async def on_shutdown():
    """Delete webhook on shutdown."""
    response = requests.get(f"https://api.telegram.org/bot{API_TOKEN}/deleteWebhook")
    print("🛑 Webhook Deleted:", response.json())

# Start FastAPI with Uvicorn
if __name__ == "__main__":
    import uvicorn

    asyncio.run(on_startup())
    uvicorn.run(app, host="0.0.0.0", port=PORT)
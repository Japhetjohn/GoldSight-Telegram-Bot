import asyncio
import requests
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from dotenv import load_dotenv
from fastapi import FastAPI, Request
import uvicorn

# Load environment variables
load_dotenv()
API_TOKEN = os.getenv("MAIN_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
VIP_CHANNEL = os.getenv("VIP_CHANNEL_ID")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8080))

# Validate environment variables
if not all([API_TOKEN, ADMIN_ID, VIP_CHANNEL, ALPHA_VANTAGE_KEY, WEBHOOK_URL]):
    raise ValueError("Missing required environment variables!")

# Ensure VIP_CHANNEL is an integer
try:
    VIP_CHANNEL = int(VIP_CHANNEL)
except ValueError:
    raise ValueError("VIP_CHANNEL_ID must be a valid integer!")

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
    try:
        update_data = await request.json()
        telegram_update = Update(**update_data)
        await dp.process_update(telegram_update)
    except Exception as e:
        logging.error(f"Error processing update: {e}")
    return {"ok": True}

async def fetch_auto_signals():
    """Fetch signals from Alpha Vantage and send to VIP_CHANNEL."""
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

                if "Global Quote" in data and data["Global Quote"].get("05. price"):
                    price = data["Global Quote"]["05. price"]
                    signal = f"📈 XAUUSD Latest: {price} (Auto)"
                    
                    logging.info(f"Sending to VIP channel ({VIP_CHANNEL}): {signal}")
                    await bot.send_message(VIP_CHANNEL, signal)
                    last_signal = signal
                    break
                else:
                    logging.warning("No valid data from Alpha Vantage!")
                    await bot.send_message(ADMIN_ID, "Alpha Vantage returned empty data!")
                    break

            except Exception as e:
                logging.error(f"Signal error (attempt {attempt + 1}): {e}")

                if attempt == max_retries - 1:
                    logging.warning(f"Sending fallback signal to VIP channel ({VIP_CHANNEL}): {last_signal}")
                    await bot.send_message(VIP_CHANNEL, last_signal)
                    await bot.send_message(ADMIN_ID, f"Alpha Vantage failed after {max_retries} attempts: {e}")
                else:
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)

        logging.info("Waiting 5 minutes for next signal...")
        await asyncio.sleep(300)

async def on_startup():
    """Set webhook and start background tasks."""
    webhook_url = f"{WEBHOOK_URL}{WEBHOOK_PATH}"
    response = requests.get(f"https://api.telegram.org/bot{API_TOKEN}/setWebhook?url={webhook_url}")
    logging.info(f"Webhook Set: {response.json()}")

    try:
        await bot.send_message(VIP_CHANNEL, "Bot started successfully via Webhook!")
        logging.info(f"VIP channel ({VIP_CHANNEL}) is accessible!")
    except Exception as e:
        logging.error(f"Failed to access VIP channel ({VIP_CHANNEL}): {e}")
        await bot.send_message(ADMIN_ID, f"VIP channel error: {e}")

    asyncio.create_task(fetch_auto_signals())

async def on_shutdown():
    """Delete webhook on shutdown."""
    response = requests.get(f"https://api.telegram.org/bot{API_TOKEN}/deleteWebhook")
    logging.info(f"Webhook Deleted: {response.json()}")

# Start FastAPI with Uvicorn
if __name__ == "__main__":
    asyncio.run(on_startup())
    uvicorn.run(app, host="0.0.0.0", port=PORT)
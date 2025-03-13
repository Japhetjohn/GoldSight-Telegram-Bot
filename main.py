import asyncio
import requests
import os
import threading
import http.server
import socketserver
from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_TOKEN = os.getenv("MAIN_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
VIP_CHANNEL = os.getenv("VIP_CHANNEL_ID")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")

# Validate environment variables
if not all([API_TOKEN, ADMIN_ID, VIP_CHANNEL, ALPHA_VANTAGE_KEY]):
    raise ValueError("Missing required environment variables!")

# Convert VIP_CHANNEL to int (Fix potential error)
try:
    VIP_CHANNEL = int(VIP_CHANNEL)
except ValueError:
    raise ValueError("VIP_CHANNEL_ID must be a valid integer!")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

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

                # Log API response
                print(f"Alpha Vantage Response: {data}")

                # Check if valid signal is present
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
                    await bot.send_message(VIP_CHANNEL, last_signal)  # ✅ Send fallback to VIP_CHANNEL
                    await bot.send_message(ADMIN_ID, f"Alpha Vantage failed after {max_retries} attempts: {e}")
                else:
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)

        print("Waiting 5 minutes for next signal...")
        await asyncio.sleep(300)

async def main():
    """Start the bot and tasks."""
    print("✅ GoldSightBot starting...")

    try:
        await bot.send_message(VIP_CHANNEL, "Bot started successfully!")
        print(f"🎉 VIP channel ({VIP_CHANNEL}) is accessible!")
    except Exception as e:
        print(f"🚨 Failed to access VIP channel ({VIP_CHANNEL}): {e}")
        await bot.send_message(ADMIN_ID, f"VIP channel error: {e}")

    asyncio.create_task(fetch_auto_signals())
    await dp.start_polling(bot)

# HTTP server for Render (Keeps bot alive)
PORT = int(os.getenv("PORT", 8080))

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving on port {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    asyncio.run(main())
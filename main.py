import asyncio
import requests
import os
import sys
import traceback
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from aiohttp import web
from dotenv import load_dotenv

# Log startup
print("Starting main.py...")

# Load env vars
load_dotenv()
API_TOKEN = os.getenv("MAIN_BOT_TOKEN")
HELP_BOT_TOKEN = os.getenv("HELP_BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
VIP_CHANNEL = os.getenv("VIP_CHANNEL_ID")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")

print(f"Env vars: MAIN_BOT_TOKEN={API_TOKEN[:5] if API_TOKEN else 'None'}..., HELP_BOT_TOKEN={HELP_BOT_TOKEN[:5] if HELP_BOT_TOKEN else 'None'}..., ADMIN_ID={ADMIN_ID or 'None'}, VIP_CHANNEL={VIP_CHANNEL or 'None'}, ALPHA_VANTAGE_KEY={ALPHA_VANTAGE_KEY[:5] if ALPHA_VANTAGE_KEY else 'None'}...")

# Validate env vars
if not all([API_TOKEN, HELP_BOT_TOKEN, ADMIN_ID, VIP_CHANNEL, ALPHA_VANTAGE_KEY]):
    print("Error: Missing critical env vars!")
    sys.exit(1)

try:
    ADMIN_ID = int(ADMIN_ID)
    VIP_CHANNEL = int(VIP_CHANNEL)
    print(f"Converted: ADMIN_ID={ADMIN_ID}, VIP_CHANNEL={VIP_CHANNEL}")
except ValueError as e:
    print(f"Error: ADMIN_ID or VIP_CHANNEL not integers - {e}")
    sys.exit(1)

# Fake server setup (priority: bind port ASAP)
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.environ.get("PORT", 10000))  # Fallback to 10000
print(f"Binding server to {WEBAPP_HOST}:{WEBAPP_PORT}...")

async def fake_handler(request):
    print("Server hit: /")
    return web.Response(text="Yo, I’m live—GoldSight running!")

app = web.Application()
app.add_routes([web.get('/', fake_handler)])

# Initialize bots
print("Initializing bots...")
try:
    main_bot = Bot(token=API_TOKEN)
    main_dp = Dispatcher()
    help_bot = Bot(token=HELP_BOT_TOKEN)
    help_dp = Dispatcher()
except Exception as e:
    print(f"Bot init failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Main Bot Handlers
@main_dp.message()
async def handle_message(message: Message):
    user_id = message.from_user.id
    text = message.text.lower() if message.text else ""
    print(f"Main Bot got: {text}")

    if text.startswith("/start"):
        welcome_msg = (
            "WELCOME TO GOLDSIGHT 🥇\n"
            "Top-tier trading signals worldwide 🌎\n"
            "Chat: @GoldSight\n"
            "Help: @GoldSightHelpBot"
        )
        await message.reply(welcome_msg)

    elif text.startswith("/signal"):
        try:
            admins = [admin.user.id for admin in await message.chat.get_administrators()]
        except Exception as e:
            print(f"Failed to fetch admins: {e}")
            admins = [ADMIN_ID]
        if user_id == ADMIN_ID or user_id in admins:
            signal = text.split(maxsplit=1)[1] if len(text.split()) > 1 else None
            if not signal:
                await message.reply("Use: /signal <text>")
                return
            try:
                await main_bot.send_message(VIP_CHANNEL, f"📈 Signal: {signal}")
                print(f"Signal '{signal}' sent to {VIP_CHANNEL}")
                await message.reply("Signal sent!")
            except Exception as e:
                print(f"Failed to send signal: {e}")
                await message.reply(f"Error: {e}")
        else:
            print(f"User {user_id} not authorized")
            await message.reply("Admins only!")

# Help Bot Handlers
@help_dp.message()
async def handle_help(message: Message):
    text = message.text.lower()
    print(f"Help Bot got: {text}")
    if text == "/start":
        await message.reply("Yo! GoldSight Help Bot here. What’s up?")

# Auto Signals
async def fetch_auto_signals():
    max_retries = 3
    base_delay = 5
    last_signal = "XAUUSD Latest: N/A (Fallback)"
    while True:
        for attempt in range(max_retries):
            try:
                url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=XAUUSD&apikey={ALPHA_VANTAGE_KEY}"
                print(f"Fetching signal from: {url}")
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                if "Global Quote" in data and data["Global Quote"]:
                    price = data["Global Quote"]["05. price"]
                    signal = f"XAUUSD Latest: {price} (Auto)"
                    print(f"Sending signal: {signal} to {VIP_CHANNEL}")
                    await main_bot.send_message(VIP_CHANNEL, f"📈 {signal}")
                    last_signal = signal
                    break
                else:
                    print("No valid data from Alpha Vantage!")
                    break
            except Exception as e:
                print(f"Auto signal error (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    await main_bot.send_message(VIP_CHANNEL, f"📈 {last_signal}")
        await asyncio.sleep(300)  # Every 5 mins

# Startup and Shutdown
async def on_startup():
    print("Starting up bots...")
    print(f"✅ Bots polling, server on {WEBAPP_PORT}!")
    asyncio.create_task(fetch_auto_signals())

async def on_shutdown():
    print("🛑 Shutting down bots...")
    await main_bot.session.close()
    await help_bot.session.close()

async def main():
    print("Entering main()...")
    main_dp.startup.register(on_startup)
    main_dp.shutdown.register(on_shutdown)
    help_dp.startup.register(on_startup)
    help_dp.shutdown.register(on_shutdown)

    # Start server first
    print(f"Starting server on {WEBAPP_HOST}:{WEBAPP_PORT}...")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)
    await site.start()
    print(f"Server live on {WEBAPP_HOST}:{WEBAPP_PORT}!")

    # Then poll bots
    print("Starting polling...")
    await asyncio.gather(
        main_dp.start_polling(main_bot),
        help_dp.start_polling(help_bot)
    )

if __name__ == "__main__":
    print("Running asyncio...")
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Asyncio run failed: {e}")
        traceback.print_exc()
        sys.exit(1)
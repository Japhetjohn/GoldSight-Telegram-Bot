import asyncio
import requests
import os
import sys
import traceback
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from aiohttp import web
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s", force=True)
logger = logging.getLogger(__name__)

def log_print(*args, **kwargs):
    print(*args, flush=True, **kwargs)
    logger.info(" ".join(map(str, args)))

log_print("Starting main.py...")

# Load env vars
load_dotenv()
API_TOKEN = os.getenv("MAIN_BOT_TOKEN")
HELP_BOT_TOKEN = os.getenv("HELP_BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
VIP_CHANNEL = os.getenv("VIP_CHANNEL_ID")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")

log_print(f"Env vars: MAIN_BOT_TOKEN={API_TOKEN[:5] if API_TOKEN else 'None'}..., HELP_BOT_TOKEN={HELP_BOT_TOKEN[:5] if HELP_BOT_TOKEN else 'None'}..., ADMIN_ID={ADMIN_ID or 'None'}, VIP_CHANNEL={VIP_CHANNEL or 'None'}, ALPHA_VANTAGE_KEY={ALPHA_VANTAGE_KEY[:5] if ALPHA_VANTAGE_KEY else 'None'}...")

if not all([API_TOKEN, HELP_BOT_TOKEN, ADMIN_ID, VIP_CHANNEL, ALPHA_VANTAGE_KEY]):
    log_print("Error: Missing critical env vars!")
    sys.exit(1)

try:
    ADMIN_ID = int(ADMIN_ID)
    VIP_CHANNEL = int(VIP_CHANNEL)
    log_print(f"Converted: ADMIN_ID={ADMIN_ID}, VIP_CHANNEL={VIP_CHANNEL}")
except ValueError as e:
    log_print(f"Error: ADMIN_ID or VIP_CHANNEL not integers - {e}")
    sys.exit(1)

# Server setup
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.environ.get("PORT", 8080))
log_print(f"Binding server to {WEBAPP_HOST}:{WEBAPP_PORT}...")

async def fake_handler(request):
    log_print("Server hit: /")
    return web.Response(text="live GoldSight running!")

app = web.Application()
app.add_routes([web.get('/', fake_handler)])

# Initialize bots
log_print("Initializing bots...")
try:
    main_bot = Bot(token=API_TOKEN)
    main_dp = Dispatcher()
    help_bot = Bot(token=HELP_BOT_TOKEN)
    help_dp = Dispatcher()
except Exception as e:
    log_print(f"Bot init failed: {e}")
    traceback.print_exc()
    sys.exit(1)

class SubscribeState:
    PLAN = "plan"
    PROOF = "proof"

user_states = {}

# Main Bot Handlers
@main_dp.message()
async def handle_message(message: Message):
    user_id = message.from_user.id
    text = message.text.lower() if message.text else ""
    log_print(f"Main Bot got: {text}")

    if text.startswith("/start"):
        welcome_msg = (
            "WELCOME TO GOLDSIGHT 🥇\n\n"
            "Join our team for top-tier trading signals worldwide 🌎\n\n"
            "We trade:\n✅XAUUSD\n✅USDJPY\n✅EURUSD\n\n"
            "Chat with us: @GoldSight\n"
            "Need help? Hit up @GoldSightHelpBot\n\n"
            "Tap below:\n/subscribe - Join VIP\n/referral - Earn 10%\n/terms - Read Terms"
        )
        await message.reply(welcome_msg)

    elif text.startswith("/referral"):
        await message.reply("Referral link coming soon! Earn 10% per paid referral.")

    elif text.startswith("/subscribe"):
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="$30 Bi-Weekly", callback_data="plan_biweekly")],
                [types.InlineKeyboardButton(text="$50 Monthly", callback_data="plan_monthly")]
            ]
        )
        await message.reply("Choose your VIP plan:", reply_markup=keyboard)

    elif text.startswith("/terms"):
        await message.reply("TERMS & CONDITIONS\n1. Past results don’t guarantee future gains.\n2. No refunds after VIP access.\n3. No disputes or chargebacks, you’ll be banned forever.\n4. Payment issues?  message @GoldSightSupport.\n5. Subscriptions aren’t automatic—renew manually when expired.\n6. use @Goldsighthelpbot incase of any issues.\n7. We can contact you anytime about your subscription.\n8. Read the pinned message in the VIP channel once in.\n\nPRIVACY POLICY\nWe don’t share your info with third parties. You might get forex info from us after payment.\n\nREFUND POLICY\nNo refunds after joining the channel.")

    elif text.startswith("/signal"):
        try:
            admins = [admin.user.id for admin in await message.chat.get_administrators()]
        except Exception as e:
            log_print(f"Failed to fetch admins: {e}")
            admins = [ADMIN_ID]
        if user_id == ADMIN_ID or user_id in admins:
            signal = text.split(maxsplit=1)[1] if len(text.split()) > 1 else None
            if not signal:
                await message.reply("Use: /signal <text>")
                return
            await main_bot.send_message(VIP_CHANNEL, f"📈 Signal: {signal}")
            log_print(f"Signal '{signal}' sent to {VIP_CHANNEL}")
            await message.reply("Signal sent!")
        else:
            log_print(f"User {user_id} not authorized")
            await message.reply("Admins only!")

    elif user_id in user_states and user_states[user_id]["state"] == SubscribeState.PROOF:
        if message.photo or message.text:
            plan = user_states[user_id]["plan"]
            await main_bot.send_message(ADMIN_ID, f"User {user_id} sent proof for {plan}:")
            if message.photo:
                await main_bot.send_photo(ADMIN_ID, message.photo[-1].file_id)
            elif message.text:
                await main_bot.send_message(ADMIN_ID, message.text)
            await message.reply("Proof sent! Awaiting approval.")
            del user_states[user_id]

@main_dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    log_print(f"Callback: {callback.data}")
    if callback.data.startswith("plan_"):
        plan = callback.data.split("_")[1]
        await main_bot.answer_callback_query(callback.id)
        payment_msg = (
            f"Pay for {plan.capitalize()} - ${'30' if plan == 'biweekly' else '50'}:\n"
            "USDT (SOL): 7ryDkprn33twExM1ScdfStcuxTrdDxuJXedTZZH66gAZ\n"
            "Usdt (BSC Bnb): 0x59b733f5cc3f2b48c703aef91bd9a531f39d60a0\n"
            "Usdt (trc20): TH6W67eY7XtQusdrWGProevkXsQV6C9iC8\n"
            "Usdt (Eth): 0x59b733f5cc3f2b48c703aef91bd9a531f39d60a0\n"
            "Usdt (TON): 0x59b733f5cc3f2b48c703aef91bd9a531f39d60a0\n"
            "Send proof here (screenshot/hash).\n"
            "Support: @GoldSightSupport"
        )
        await main_bot.send_message(user_id, payment_msg)
        user_states[user_id] = {"state": SubscribeState.PROOF, "plan": plan}

# Help Bot Handlers
@help_dp.message()
async def handle_help(message: Message):
    text = message.text.lower()
    log_print(f"Help Bot got: {text}")
    if text == "/start":
        await message.reply("Yo! GoldSight Help Bot here. What’s up?")
    elif text == "/faq":
        await message.reply("FAQ:\n- Join? /subscribe\n- Cost? $30 bi-weekly or $50 monthly\n- Support? @GoldSightSupport")
    else:
        await message.reply("Try /faq or hit @GoldSightSupport!")
        await help_bot.send_message(ADMIN_ID, f"Help request from {message.from_user.id}: {text}")

# Auto Signals
async def fetch_auto_signals():
    max_retries = 3
    last_signal = "XAUUSD Latest: N/A (Fallback)"
    while True:
        for attempt in range(max_retries):
            try:
                url = f"https://www.alphavantage.co/query?function=FX_DAILY&from_symbol=XAU&to_symbol=USD&apikey={ALPHA_VANTAGE_KEY}"
                log_print(f"Fetching signal from: {url}")
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                log_print(f"Alpha Vantage response: {data}")
                if "Time Series FX (Daily)" in data and data["Time Series FX (Daily)"]:
                    latest_date = max(data["Time Series FX (Daily)"].keys())
                    price = data["Time Series FX (Daily)"][latest_date]["4. close"]
                    signal = f"XAUUSD Latest: {price} (Auto)"
                    await main_bot.send_message(VIP_CHANNEL, f"📈 {signal}")
                    last_signal = signal
                    log_print(f"Signal '{signal}' sent to {VIP_CHANNEL}")
                    break
                else:
                    log_print("No valid time series data from Alpha Vantage!")
                    if "Information" in data and "rate limit" in data["Information"]:
                        log_print("Rate limit hit, using fallback signal.")
                        await main_bot.send_message(VIP_CHANNEL, f"📈 {last_signal}")
                    break
            except Exception as e:
                log_print(f"Auto signal error (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    await main_bot.send_message(VIP_CHANNEL, f"📈 {last_signal}")
        await asyncio.sleep(300)

# Startup and Shutdown
async def on_startup():
    log_print("Starting up bots...")
    log_print(f"✅ Bots polling, server on {WEBAPP_PORT}!")
    asyncio.create_task(fetch_auto_signals())

async def on_shutdown():
    log_print("🛑 Shutting down bots...")
    await main_bot.session.close()
    await help_bot.session.close()

async def main():
    log_print("Entering main()...")
    main_dp.startup.register(on_startup)
    main_dp.shutdown.register(on_shutdown)
    help_dp.startup.register(on_startup)
    help_dp.shutdown.register(on_shutdown)

    log_print(f"Starting server on {WEBAPP_HOST}:{WEBAPP_PORT}...")
    try:
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)
        await site.start()
        log_print(f"Server live on {WEBAPP_HOST}:{WEBAPP_PORT}!")
        await asyncio.sleep(1)  # Let Render catch the port
    except Exception as e:
        log_print(f"Server failed: {e}")
        traceback.print_exc()
        sys.exit(1)

    log_print("Starting polling...")
    try:
        await asyncio.gather(
            main_dp.start_polling(main_bot, handle_errors=True),
            help_dp.start_polling(help_bot, handle_errors=True)
        )
    except Exception as e:
        log_print(f"Polling failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    log_print("Running asyncio...")
    try:
        asyncio.run(main())
    except Exception as e:
        log_print(f"Asyncio run failed: {e}")
        traceback.print_exc()
        sys.exit(1)
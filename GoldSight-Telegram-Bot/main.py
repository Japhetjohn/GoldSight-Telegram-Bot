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
VIP_CHANNEL = int(os.getenv("VIP_CHANNEL_ID"))
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")

# Validate environment variables
if not all([API_TOKEN, ADMIN_ID, VIP_CHANNEL, ALPHA_VANTAGE_KEY]):
    raise ValueError("Missing required environment variables!")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class SubscribeState:
    PLAN = "plan"
    PROOF = "proof"

user_states = {}
HELP_BOT_USERNAME = None

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    text = message.text.lower()
    print(f"Main Bot got: {text}")

    if text.startswith("/start"):
        from database import add_user
        referral = text.split(maxsplit=1)[1] if len(text.split()) > 1 else None
        ref_code = add_user(user_id, referral)
        # Log the username being used
        print(f"Building welcome message with HELP_BOT_USERNAME: {HELP_BOT_USERNAME}")
        welcome_msg = (
            "WELCOME TO GOLDSIGHT 🥇\n\n"
            "Receive Day trading & swing trading signals from the GoldSight team everywhere around the world 🌎\n\n"
            "We trade:\n✅XAUUSD\n✅USDJPY\n✅EURUSD\n\n"
            "Join the general chat for questions and updates: @GoldSight\n"
            f"Need help? Contact our Help Bot: {HELP_BOT_USERNAME or '@GoldSightHelpBot'}\n\n"
            "Weekly - $30.00\nMonthly - $50.00\n"
            "This service lets you copy GoldSight’s unique trades across our instruments.\n\n"
            "NOTE: All trades are our perspective on Forex\n"
            "DISCLAIMER: Past performance does not guarantee future profits.\n\n"
            "Tap below:\n/subscribe - Join VIP\n/referral - Earn 10%\n/terms - Read Terms"
        )
        await message.reply(welcome_msg)
        print("Welcome message sent")

    elif text.startswith("/referral"):
        from database import get_user
        user = get_user(user_id)
        if user:
            await message.reply(f"Referral link: t.me/GoldSightBot?start={user[2]}\nEarn 10% per paid referral!")
        else:
            await message.reply("Run /start first!")

    elif text.startswith("/subscribe"):
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="Weekly - $30", callback_data="plan_weekly")],
                [types.InlineKeyboardButton(text="Monthly - $50", callback_data="plan_monthly")]
            ]
        )
        await message.reply("Pick your plan:", reply_markup=keyboard)

    elif text.startswith("/terms"):
        terms_msg = (
            "TERMS & CONDITIONS\n"
            "Past results don’t guarantee future performance. Use proper risk management to protect your capital.\n"
            "1. Stolen debit/credit cards are banned—you’ll be caught and removed.\n"
            "2. Use valid emails only—access goes to legit emails.\n"
            "3. No disputes or chargebacks—you’ll be banned forever.\n"
            "4. Payment issues? Email vipsubscribepro@gmail.com or message @GoldSightSupport. Be patient—lots of messages.\n"
            "5. Subscriptions aren’t automatic—renew manually when expired.\n"
            f"6. Contact support at vipsubscribepro@gmail.com or use {HELP_BOT_USERNAME or '@GoldSightHelpBot'}.\n"
            "7. You’ll get emails about our products after purchase.\n"
            "8. We can contact you anytime about your subscription.\n"
            "9. Read the pinned message in the VIP channel once in.\n\n"
            "PRIVACY POLICY\n"
            "We don’t share your info with third parties. You might get forex info from us after payment.\n\n"
            "REFUND POLICY\n"
            "No refunds after joining the channel."
        )
        await message.reply(terms_msg)

@dp.callback_query(lambda c: c.data in ["plan_weekly", "plan_monthly"])
async def process_subscription(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    plan = "Weekly - $30" if callback_query.data == "plan_weekly" else "Monthly - $50"
    print(f"User {user_id} selected {plan}")
    payment_instructions = (
        f"You’ve selected {plan}!\n\n"
        "To proceed, send payment to:\n"
        "[Your Payment Details Here - e.g., PayPal, Crypto Address, etc.]\n\n"
        "After payment, reply here with proof (screenshot or tx ID) or email it to vipsubscribepro@gmail.com."
    )
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(user_id, payment_instructions)
    await bot.send_message(ADMIN_ID, f"Subscription request from {user_id}: {plan}")

async def fetch_auto_signals():
    max_retries = 3
    base_delay = 5
    last_signal = "XAUUSD Latest: N/A (Fallback)"
    for attempt in range(max_retries):
        try:
            test_url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=XAUUSD&apikey={ALPHA_VANTAGE_KEY}"
            response = requests.get(test_url, timeout=15)
            response.raise_for_status()
            print("Alpha Vantage API key validated successfully!")
            break
        except Exception as e:
            print(f"Alpha Vantage API key validation failed (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                await bot.send_message(ADMIN_ID, f"Alpha Vantage API key failed after {max_retries} attempts: {e}")
            else:
                await asyncio.sleep(base_delay * (2 ** attempt))

    while True:
        for attempt in range(max_retries):
            try:
                url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=XAUUSD&apikey={ALPHA_VANTAGE_KEY}"
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                data = response.json()
                if "Global Quote" in data and data["Global Quote"]:
                    price = data["Global Quote"]["05. price"]
                    signal = f"XAUUSD Latest: {price} (Auto)"
                    print(f"Sending to VIP channel ({VIP_CHANNEL}): {signal}")
                    await bot.send_message(VIP_CHANNEL, f"📈 {signal}")
                    last_signal = signal
                    break
                else:
                    print("No data from Alpha Vantage!")
                    await bot.send_message(ADMIN_ID, "Alpha Vantage returned empty data!")
                    break
            except Exception as e:
                print(f"Signal error (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    print(f"Sending fallback signal to VIP channel ({VIP_CHANNEL}): {last_signal}")
                    await bot.send_message(VIP_CHANNEL, f"📈 {last_signal}")
                    await bot.send_message(ADMIN_ID, f"Alpha Vantage failed after {max_retries} attempts: {e}")
                else:
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
        print("Waiting 5 minutes for next signal...")
        await asyncio.sleep(300)

async def subscription_task():
    from database import check_subscriptions
    while True:
        expired, reminders = check_subscriptions()
        for user_id in expired:
            print(f"Expired: {user_id}")
            await bot.send_message(user_id, "VIP expired! Renew with /subscribe.")
        for user_id in reminders:
            print(f"Reminder: {user_id}")
            await bot.send_message(user_id, "VIP expires in 2 days! Renew with /subscribe.")
        await asyncio.sleep(86400)

async def main():
    from database import init_db
    from helpers import start_help_bot
    init_db()
    print("GoldSightBot starting...")
    try:
        await bot.send_message(VIP_CHANNEL, "Bot started successfully!")
        print(f"VIP channel ({VIP_CHANNEL}) is accessible!")
    except Exception as e:
        print(f"Failed to access VIP channel ({VIP_CHANNEL}): {e}")
        await bot.send_message(ADMIN_ID, f"VIP channel error: {e}")
    asyncio.create_task(subscription_task())
    asyncio.create_task(fetch_auto_signals())
    global HELP_BOT_USERNAME
    HELP_BOT_USERNAME = await start_help_bot()
    print(f"Main bot received HELP_BOT_USERNAME: {HELP_BOT_USERNAME}")
    await dp.start_polling(bot)

# HTTP server for Render
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
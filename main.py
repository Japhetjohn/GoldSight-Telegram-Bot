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

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class SubscribeState:
    PLAN = "plan"
    PROOF = "proof"

user_states = {}

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    text = message.text.lower()
    print(f"Main Bot got: {text}")

    if text.startswith("/start"):
        from database import add_user
        referral = text.split(maxsplit=1)[1] if len(text.split()) > 1 else None
        ref_code = add_user(user_id, referral)
        welcome_msg = (
            "WELCOME TO GOLDSIGHT 🥇\n\n"
            "Receive Day trading & swing trading signals from the GoldSight team everywhere around the world 🌎\n\n"
            "We trade:\n✅XAUUSD\n✅USDJPY\n✅EURUSD\n\n"
            "Join the general chat for questions and updates: @GoldSight\n\n"
            "Standard - $75.00\n"
            "This service lets you copy GoldSight’s unique trades for a month across our instruments.\n\n"
            "NOTE: All trades are our perspective on Forex\n"
            "DISCLAIMER: Past performance does not guarantee future profits.\n\n"
            "Tap below:\n/subscribe - Join VIP\n/referral - Earn 10%\n/terms - Read Terms"
        )
        await message.reply(welcome_msg)

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
                [types.InlineKeyboardButton(text="Standard - $75 (Monthly)", callback_data="plan_standard")]
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
            "6. Contact support at vipsubscribepro@gmail.com for issues.\n"
            "7. You’ll get emails about our products after purchase.\n"
            "8. We can contact you anytime about your subscription.\n"
            "9. Read the pinned message in the VIP channel once in.\n\n"
            "PRIVACY POLICY\n"
            "We don’t share your info with third parties. You might get forex info from us after payment.\n\n"
            "REFUND POLICY\n"
            "No refunds after joining the channel."
        )
        await message.reply(terms_msg)

async def fetch_auto_signals():
    max_retries = 3
    base_delay = 5
    last_signal = "XAUUSD Latest: N/A (Fallback)"
    while True:
        for attempt in range(max_retries):
            try:
                url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=XAUUSD&apikey={ALPHA_VANTAGE_KEY}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                if "Global Quote" in data and data["Global Quote"]:
                    price = data["Global Quote"]["05. price"]
                    signal = f"XAUUSD Latest: {price} (Auto)"
                    print(f"Sending: {signal}")
                    await bot.send_message(VIP_CHANNEL, f"📈 {signal}")
                    last_signal = signal
                    break
                else:
                    print("No data from Alpha Vantage!")
                    await bot.send_message(ADMIN_ID, "Alpha Vantage issue!")
                    break
            except Exception as e:
                print(f"Signal error (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    await bot.send_message(VIP_CHANNEL, f"📈 {last_signal}")
                    await bot.send_message(ADMIN_ID, "Alpha Vantage keeps failing!")
                else:
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
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
    asyncio.create_task(subscription_task())
    asyncio.create_task(fetch_auto_signals())
    asyncio.create_task(start_help_bot())
    await dp.start_polling(bot)

# Adding an HTTP server to prevent Render's timeout issue
PORT = 8080  # Ensure this matches the PORT variable in Render settings

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
    # Start the HTTP server in a separate thread to satisfy Render's port binding requirement
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Start the bot
    asyncio.run(main())
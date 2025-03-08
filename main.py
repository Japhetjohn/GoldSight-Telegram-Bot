# main.py
import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv
import os
from database import init_db, add_user, approve_vip, get_user, check_subscriptions
from helpers import start_help_bot

load_dotenv()
API_TOKEN = os.getenv("MAIN_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
VIP_CHANNEL = int(os.getenv("VIP_CHANNEL_ID"))
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Simple state management
class SubscribeState:
    PLAN = "plan"
    PROOF = "proof"

user_states = {}

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    text = message.text.lower()
    print(f"Main Bot received: {text}")  # Debug log

    if text.startswith("/start"):
        referral = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
        ref_code = add_user(user_id, referral)
        welcome_msg = (
            "Welcome to GoldSightBot, Japhet! 📈\n"
            "/subscribe - Join VIP\n"
            "/referral - Earn 10%\n"
            "Help? @Goldsighthelpbot"
        )
        await message.reply(welcome_msg)

    elif text.startswith("/referral"):
        user = get_user(user_id)
        if user:
            await message.reply(f"Referral link: t.me/GoldSightBot?start={user[2]}\nEarn 10% per paid referral!")
        else:
            await message.reply("Run /start first!")

    elif text.startswith("/subscribe"):
        # Fixed: Proper InlineKeyboardMarkup syntax for aiogram 3.x
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="$30 Bi-Weekly", callback_data="plan_biweekly")],
                [types.InlineKeyboardButton(text="$50 Monthly", callback_data="plan_monthly")]
            ]
        )
        await message.reply("Pick a plan:", reply_markup=keyboard)

    elif text.startswith("/approve"):
        admins = [admin.user.id for admin in await message.chat.get_administrators()]
        if message.from_user.id == ADMIN_ID or message.from_user.id in admins:
            args = message.text.split()
            if len(args) != 3 or args[2] not in ["biweekly", "monthly"]:
                await message.reply("Use: /approve <user_id> <biweekly/monthly>")
                return
            target_user_id, plan = int(args[1]), args[2]
            referrer, commission = approve_vip(target_user_id, plan)
            await bot.send_message(target_user_id, "You’re VIP! Check the channel.")
            await bot.send_message(VIP_CHANNEL, f"New VIP: @{message.from_user.username}")
            await message.reply(f"Approved {target_user_id}.")
            if referrer:
                await bot.send_message(referrer, f"Referral bonus: ${commission}!")

    elif text.startswith("/signal"):
        admins = [admin.user.id for admin in await message.chat.get_administrators()]
        if message.from_user.id == ADMIN_ID or message.from_user.id in admins:
            signal = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
            if not signal:
                await message.reply("Use: /signal <text>")
                return
            await bot.send_message(VIP_CHANNEL, f"📈 XAUUSD Signal: {signal}")
            await message.reply("Signal posted!")

    # Handle proof submission
    elif user_id in user_states and user_states[user_id]["state"] == SubscribeState.PROOF:
        if message.photo or message.text:
            plan = user_states[user_id]["plan"]
            await bot.send_message(ADMIN_ID, f"User {user_id} sent proof for {plan}:")
            if message.photo:
                await bot.send_photo(ADMIN_ID, message.photo[-1].file_id)
            elif message.text:
                await bot.send_message(ADMIN_ID, message.text)
            await message.reply("Proof sent! Waiting for approval.")
            del user_states[user_id]

    # Spam filter
    elif message.chat.id == VIP_CHANNEL and not message.from_user.is_bot:
        user = get_user(user_id)
        if not user or user[4] != 1:
            await message.delete()
            await bot.send_message(user_id, "VIPs only! Use /subscribe.")

@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    print(f"Callback received: {callback.data}")  # Debug log
    if callback.data.startswith("plan_"):
        plan = callback.data.split("_")[1]
        await bot.answer_callback_query(callback.id)
        payment_msg = (
            "Pay here:\n"
            "USDT (SOL): 7ryDkprn33twExM1ScdfStcuxTrdDxuJXedTZZH66gAZ\n"
            "USDT (BSC): 0x59b733f5cc3f2b48c703aef91bd9a531f39d60a0\n"
            "USDT (TRC20): TH6W67eY7XtQusdrWGProevkXsQV6C9iC8\n"
            "USDT (ETH): 0x59b733f5cc3f2b48c703aef91bd9a531f39d60a0\n"
            "USDT (TON): 0x59b733f5cc3f2b48c703aef91bd9a531f39d60a0\n"
            "Send proof here (screenshot/hash)."
        )
        await bot.send_message(callback.from_user.id, payment_msg)
        user_states[user_id] = {"state": SubscribeState.PROOF, "plan": plan}

async def fetch_auto_signals():
    max_retries = 3
    base_delay = 5  # Seconds
    last_signal = "XAUUSD Latest: N/A (Fallback)"  # Fallback signal
    while True:
        for attempt in range(max_retries):
            try:
                url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=XAUUSD&apikey={ALPHA_VANTAGE_KEY}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                print(f"Alpha Vantage response: {data}")  # Debug log
                if "Global Quote" in data and data["Global Quote"]:
                    price = data["Global Quote"]["05. price"]
                    signal = f"XAUUSD Latest: {price} (Auto)"
                    print(f"Sending auto-signal: {signal}")
                    await bot.send_message(VIP_CHANNEL, f"📈 {signal}")
                    last_signal = signal  # Store last good signal
                    break  # Success, exit retry loop
                else:
                    print("Alpha Vantage API returned no data—check key or limits!")
                    await bot.send_message(ADMIN_ID, f"Alpha Vantage API issue—raw response: {data}")
                    break
            except requests.exceptions.RequestException as e:
                print(f"Auto-signal network error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:  # Last attempt failed
                    print("Max retries reached, using fallback signal!")
                    await bot.send_message(VIP_CHANNEL, f"📈 {last_signal}")
                    await bot.send_message(ADMIN_ID, "Alpha Vantage keeps failing—check network or key!")
                else:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    print(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
        await asyncio.sleep(300)  # Every 5 mins

async def subscription_task():
    while True:
        expired, reminders = check_subscriptions()
        for user_id in expired:
            print(f"Sending expiration notice to {user_id}")
            await bot.send_message(user_id, "VIP expired! Renew with /subscribe.")
        for user_id in reminders:
            print(f"Sending reminder to {user_id}")
            await bot.send_message(user_id, "VIP expires in 2 days! Renew with /subscribe.")
        await asyncio.sleep(86400)  # Daily

async def main():
    init_db()
    print("Main Bot is starting...")
    asyncio.create_task(subscription_task())
    asyncio.create_task(fetch_auto_signals())
    asyncio.create_task(start_help_bot())
    try:
        await dp.start_polling(bot, polling_timeout=10)
    except Exception as e:
        print(f"Main Bot polling failed: {str(e)}")
    print("Main Bot polling ended unexpectedly!")

if __name__ == "__main__":
    print("Starting GoldSightBot...")
    asyncio.run(main())
    print("GoldSightBot has stopped—shouldn’t see this unless it crashes!")
    while True:
        print("Main loop still running...")
        asyncio.run(asyncio.sleep(60))

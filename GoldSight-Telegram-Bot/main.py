import asyncio
import requests
import os
from aiogram import Bot, Dispatcher, types
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("MAIN_BOT_TOKEN")
HELP_BOT_TOKEN = os.getenv("HELP_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
VIP_CHANNEL = int(os.getenv("VIP_CHANNEL_ID"))
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://goldsight-telegram-bot.onrender.com")
WEBHOOK_PATH = "/webhook"
HELP_WEBHOOK_PATH = "/help_webhook"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 5000))

# Main Bot
main_bot = Bot(token=API_TOKEN)
main_dp = Dispatcher()

# Help Bot
help_bot = Bot(token=HELP_BOT_TOKEN)
help_dp = Dispatcher()

class SubscribeState:
    PLAN = "plan"
    PROOF = "proof"

user_states = {}

# Main Bot Handlers
@main_dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    text = message.text.lower() if message.text else ""
    print(f"Main Bot got: {text}")

    if text.startswith("/start"):
        from database import add_user
        referral = text.split(maxsplit=1)[1] if len(text.split()) > 1 else None
        ref_code = add_user(user_id, referral)
        welcome_msg = (
            "WELCOME TO GOLDSIGHT 🥇\n\n"
            "Join our team for top-tier trading signals worldwide 🌎\n\n"
            "We trade:\n✅XAUUSD\n✅USDJPY\n✅EURUSD\n\n"
            "Chat with us: @GoldSight\n\n"
            "NOTE: Trades are our forex perspective\n"
            "DISCLAIMER: Past performance isn’t future profits\n\n"
            "Tap below:\n/subscribe - Join VIP\n/referral - Earn 10%\n/terms - Read Terms"
        )
        await message.reply(welcome_msg)

    elif text.startswith("/referral"):
        from database import add_user
        user = get_user(user_id)
        if user:
            await message.reply(f"Referral link: t.me/GoldSightBot?start={user[2]}\nEarn 10% per paid referral!")
        else:
            await message.reply("Run /start first!")

    elif text.startswith("/subscribe"):
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="$30 Bi-Weekly", callback_data="plan_biweekly")],
                [types.InlineKeyboardButton(text="$50 Monthly", callback_data="plan_monthly")]
            ]
        )
        await message.reply("Choose your VIP plan:", reply_markup=keyboard)

    elif text.startswith("/terms"):
        terms_msg = (
            "TERMS & CONDITIONS\n"
            "Past results don’t guarantee future gains. Use risk management.\n"
            "1. No stolen cards—banned if caught.\n"
            "2. No disputes/chargebacks—permanent ban.\n"
            "3. Payment issues? contact @GoldSightSupport.\n"
            "4. Manually renew subscriptions.\n"
            "5. We may contact you about your sub.\n"
            "6. Check pinned message in VIP channel.\n\n"
            "PRIVACY POLICY\n"
            "No third-party sharing. Forex info post-payment.\n\n"
            "REFUND POLICY\n"
            "No refunds after VIP access."
        )
        await message.reply(terms_msg)

    elif text.startswith("/approve"):
        admins = [admin.user.id for admin in await message.chat.get_administrators()]
        if user_id == ADMIN_ID or user_id in admins:
            args = text.split()
            if len(args) != 3 or args[2] not in ["biweekly", "monthly"]:
                await message.reply("Use: /approve <user_id> <biweekly/monthly>")
                return
            from database import approve_vip
            target_id, plan = int(args[1]), args[2]
            referrer, commission = approve_vip(target_id, plan)
            await main_bot.send_message(target_id, "You’re in! Join VIP: https://t.me/+9CEQlcQ6b1U2Nzdk")
            await main_bot.send_message(VIP_CHANNEL, f"New VIP: @{message.from_user.username or target_id}")
            await message.reply(f"Approved {target_id} for {plan}.")
            if referrer:
                await main_bot.send_message(referrer, f"Referral bonus: ${commission}!")

    elif text.startswith("/signal"):
        admins = [admin.user.id for admin in await message.chat.get_administrators()]
        print(f"Admins in chat: {admins}, User ID: {user_id}, Checking against ADMIN_ID: {ADMIN_ID}")
        if user_id == ADMIN_ID or user_id in admins:
            signal = text.split(maxsplit=1)[1] if len(text.split()) > 1 else None
            if not signal:
                await message.reply("Use: /signal <text>")
                return
            try:
                await main_bot.send_message(VIP_CHANNEL, f"📈 Signal: {signal}")
                print(f"Signal '{signal}' successfully sent to VIP channel: {VIP_CHANNEL}")
                await message.reply("Signal sent to VIP!")
            except Exception as e:
                print(f"Failed to send signal to {VIP_CHANNEL}: {e}")
                await message.reply(f"Error sending signal: {e}")
        else:
            print(f"User {user_id} not authorized to send signals")
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

    elif message.chat.id == VIP_CHANNEL and not message.from_user.is_bot:
        from database import get_user
        user = get_user(user_id)
        if not user or user[4] != 1:
            await message.delete()
            await main_bot.send_message(user_id, "VIPs only! Use /subscribe.")

@main_dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    print(f"Callback: {callback.data}")
    if callback.data.startswith("plan_"):
        plan = callback.data.split("_")[1]
        await main_bot.answer_callback_query(callback.id)
        payment_msg = (
            f"Pay for {plan.capitalize()} - ${'30' if plan == 'biweekly' else '50'}:\n"
            "USDT (SOL): 7ryDkprn33twExM1ScdfStcuxTrdDxuJXedTZZH66gAZ\n"
            "USDT (BSC): 0x59b733f5cc3f2b48c703aef91bd9a531f39d60a0\n"
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
async def handle_help(message: types.Message):
    text = message.text.lower()
    print(f"Help Bot got: {text}")
    if text == "/start":
        await message.reply("Yo! GoldSight Help Bot here. What’s up?")
    elif text == "/faq":
        await message.reply("FAQ:\n- Join? /subscribe\n- Cost? $30 bi-weekly or $50 monthly\n- Chat? @GoldSight\n- Support? @GoldSightSupport")
    else:
        await message.reply("Not sure? Try /faq or hit @GoldSightSupport!")
        await help_bot.send_message(ADMIN_ID, f"Help request from {message.from_user.id}: {text}")

# Shared Tasks
async def fetch_auto_signals():
    max_retries = 3
    base_delay = 5
    last_signal = "XAUUSD Latest: N/A (Fallback)"
    while True:
        for attempt in range(max_retries):
            try:
                url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=XAUUSD&apikey={ALPHA_VANTAGE_KEY}"
                print(f"Attempting to fetch signal from: {url}")
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                if "Global Quote" in data and data["Global Quote"]:
                    price = data["Global Quote"]["05. price"]
                    signal = f"XAUUSD Latest: {price} (Auto)"
                    print(f"Preparing to send signal: {signal} to {VIP_CHANNEL}")
                    await main_bot.send_message(VIP_CHANNEL, f"📈 {signal}")
                    print(f"Auto signal '{signal}' sent to {VIP_CHANNEL}")
                    last_signal = signal
                    break
                else:
                    print("No valid data from Alpha Vantage!")
                    await main_bot.send_message(ADMIN_ID, "Alpha Vantage issue!")
                    break
            except Exception as e:
                print(f"Auto signal error (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    await main_bot.send_message(VIP_CHANNEL, f"📈 {last_signal}")
                    await main_bot.send_message(ADMIN_ID, "Alpha Vantage down!")
                await asyncio.sleep(base_delay * (2 ** attempt))
        await asyncio.sleep(300)

async def subscription_task():
    from database import check_subscriptions
    while True:
        expired, reminders = check_subscriptions()
        for user_id in expired:
            print(f"Expired: {user_id}")
            await main_bot.send_message(user_id, "VIP expired! Renew with /subscribe.")
        for user_id in reminders:
            print(f"Reminder: {user_id}")
            await main_bot.send_message(user_id, "VIP expires in 2 days! Renew with /subscribe.")
        await asyncio.sleep(86400)

# Startup and Shutdown
async def on_startup():
    from database import init_db
    init_db()
    print("Setting main bot webhook...")
    main_webhook_url = f"{WEBHOOK_URL}{WEBHOOK_PATH}"
    await main_bot.set_webhook(url=main_webhook_url)
    print(f"Main bot webhook set to {main_webhook_url}")

    print("Setting help bot webhook...")
    help_webhook_url = f"{WEBHOOK_URL}{HELP_WEBHOOK_PATH}"
    try:
        bot_info = await help_bot.get_me()
        help_bot_username = f"@{bot_info.username}"
        print(f"Help Bot username fetched: {help_bot_username}")
    except Exception as e:
        print(f"Failed to get Help Bot info: {e}")
        help_bot_username = "@GoldSightHelpBot"  # Fallback
        print(f"Using fallback username: {help_bot_username}")
    await help_bot.set_webhook(url=help_webhook_url)
    print(f"Help bot webhook set to {help_webhook_url}")

    asyncio.create_task(subscription_task())
    asyncio.create_task(fetch_auto_signals())

async def on_shutdown():
    print("Shutting down...")
    await main_bot.delete_webhook()
    await help_bot.delete_webhook()
    print("Webhooks deleted.")

def main():
    app = web.Application()

    # Main Bot Webhook
    main_handler = SimpleRequestHandler(dispatcher=main_dp, bot=main_bot)
    main_handler.register(app, path=WEBHOOK_PATH)

    # Help Bot Webhook
    help_handler = SimpleRequestHandler(dispatcher=help_dp, bot=help_bot)
    help_handler.register(app, path=HELP_WEBHOOK_PATH)

    setup_application(app, main_dp, bot=main_bot)
    setup_application(app, help_dp, bot=help_bot)

    main_dp.startup.register(on_startup)
    main_dp.shutdown.register(on_shutdown)

    print(f"Starting webhook server on {WEBAPP_HOST}:{WEBAPP_PORT}")
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)

if __name__ == "__main__":
    main()

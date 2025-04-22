import asyncio
import os
import sys
import traceback
import logging
from collections import defaultdict
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from aiohttp import web
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(message)s",
                    force=True)
logger = logging.getLogger(__name__)


def log_print(*args, **kwargs):
    print(*args, flush=True, **kwargs)
    logger.info(" ".join(map(str, args)))


# Rate limiting
rate_limit = defaultdict(lambda: {"count": 0, "reset_time": datetime.now()})
MAX_REQUESTS = 30
WINDOW_SECONDS = 60


def check_rate_limit(user_id):
    now = datetime.now()
    user_data = rate_limit[user_id]

    if (now - user_data["reset_time"]).seconds >= WINDOW_SECONDS:
        user_data["count"] = 0
        user_data["reset_time"] = now

    user_data["count"] += 1
    return user_data["count"] <= MAX_REQUESTS


# Load env vars and validate
load_dotenv()
required_vars = [
    "MAIN_BOT_TOKEN", "HELP_BOT_TOKEN", "ADMIN_ID", "VIP_CHANNEL_ID"
]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    log_print(f"Error: Missing env vars: {missing_vars}")
    sys.exit(1)

API_TOKEN = os.getenv("MAIN_BOT_TOKEN")
HELP_BOT_TOKEN = os.getenv("HELP_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
VIP_CHANNEL = int(os.getenv("VIP_CHANNEL_ID"))
WEBAPP_PORT = int(os.environ.get("PORT", 5000))

# Initialize bots
main_bot = Bot(token=API_TOKEN, parse_mode="HTML")
main_dp = Dispatcher()
help_bot = Bot(token=HELP_BOT_TOKEN, parse_mode="HTML")
help_dp = Dispatcher()


# Main Bot Handlers
@main_dp.message(Command("start"))
async def cmd_start(message: Message):
    if not check_rate_limit(message.from_user.id):
        return await message.reply("Too many requests. Please try again later."
                                   )

    user_id = message.from_user.id
    from database import add_user
    ref_code = add_user(user_id)
    await message.reply(
        f"Welcome to GoldSight! Your referral code: {ref_code}\nUse /subscribe to join VIP."
    )


@main_dp.message(Command("subscribe"))
async def cmd_subscribe(message: Message):
    if not check_rate_limit(message.from_user.id):
        return await message.reply("Too many requests. Please try again later."
                                   )

    from database import get_user
    user = get_user(message.from_user.id)
    if user and user[4] == 1:  # Check VIP status
        sub_end = datetime.fromisoformat(user[1])
        days_left = (sub_end - datetime.now()).days
        await message.reply(
            f"🌟 You're a VIP member!\nSubscription ends in {days_left} days.")
        return

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[[
            types.InlineKeyboardButton(text="Weekly ($30)",
                                       callback_data="sub_weekly")
        ],
                         [
                             types.InlineKeyboardButton(
                                 text="Monthly ($50)",
                                 callback_data="sub_monthly")
                         ]])
    await message.reply(
        "📊 GoldSight VIP Plans:\n\n🔹 Weekly: $30\n- 1 week access\n- All signals\n- Priority support\n\n🔸 Monthly: $50\n- 1 month access\n- All signals\n- Priority support\n- Early alerts\n\nSelect your plan:",
        reply_markup=keyboard)


@main_dp.message(Command("referral"))
async def cmd_referral(message: Message):
    if not check_rate_limit(message.from_user.id):
        return await message.reply("Too many requests. Please try again later."
                                   )

    from database import get_user
    user = get_user(message.from_user.id)
    if user:
        await message.reply(
            f"Your referral code: {user[2]}\nShare to earn 10% commission!")


@main_dp.message(Command("terms"))
async def cmd_terms(message: Message):
    if not check_rate_limit(message.from_user.id):
        return await message.reply("Too many requests. Please try again later."
                                   )

    await message.reply(
        "Terms & Conditions:\n1. No refunds\n2. Signals are educational\n3. Trade responsibly"
    )


@main_dp.message(Command("approve"))
async def cmd_approve(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) != 3:
        await message.reply("Usage: /approve <user_id> <biweekly/monthly>")
        return
    from database import approve_vip
    user_id = int(args[1])
    referrer, commission = approve_vip(user_id, args[2])
    await main_bot.send_message(user_id, "🎉 VIP access granted!")
    if referrer:
        await main_bot.send_message(int(referrer),
                                    f"💰 Commission earned: ${commission}")


# Help Bot Handlers
@help_dp.message()
async def handle_help(message: Message):
    if not check_rate_limit(message.from_user.id):
        return await message.reply("Too many requests. Please try again later."
                                   )

    text = message.text.lower()
    if text == "/start":
        await message.reply("Welcome to GoldSight Help! How can I assist you?")
    elif text == "/faq":
        await message.reply(
            "FAQ:\n- Join? /subscribe\n- Cost? $30 bi-weekly or $50 monthly\n- Support? @GoldSightSupport"
        )
    else:
        await message.reply("Try /faq or contact @GoldSightSupport!")
        await help_bot.send_message(
            ADMIN_ID, f"Help request from {message.from_user.id}: {text}")


# Server setup
app = web.Application()
app.router.add_get('/', lambda r: web.Response(text="GoldSight Bot running!"))
app.router.add_get('/health', lambda r: web.Response(text="OK"))


async def start_server():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', WEBAPP_PORT)
    await site.start()
    log_print(f"Server running on port {WEBAPP_PORT}")


async def main():
    try:
        await main_bot.delete_webhook(drop_pending_updates=True)
        await help_bot.delete_webhook(drop_pending_updates=True)
        from database import init_db
        init_db()
        await start_server()
        await asyncio.gather(main_dp.start_polling(main_bot),
                             help_dp.start_polling(help_bot))
    except Exception as e:
        log_print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

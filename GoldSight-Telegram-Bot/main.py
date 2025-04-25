import asyncio
import os
import sys
import traceback
import logging
from collections import defaultdict
from datetime import datetime
from aiogram import Bot, Dispatcher, Router, types
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiohttp import web
from dotenv import load_dotenv
from aiogram.client.bot import DefaultBotProperties

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


# Load environment variables and validate
load_dotenv()
required_vars = [
    "MAIN_BOT_TOKEN", "HELP_BOT_TOKEN", "ADMIN_ID", "VIP_CHANNEL_ID"
]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    log_print(f"Error: Missing environment variables: {missing_vars}")
    sys.exit(1)

API_TOKEN = os.getenv("MAIN_BOT_TOKEN")
HELP_BOT_TOKEN = os.getenv("HELP_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
VIP_CHANNEL = int(os.getenv("VIP_CHANNEL_ID"))
WEBAPP_PORT = int(os.environ.get("PORT", 5000))

# Initialize bots
main_bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
help_bot = Bot(token=HELP_BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))

# Initialize dispatchers and routers
main_dp = Dispatcher()
help_dp = Dispatcher()
main_router = Router()
help_router = Router()

# Register routers with dispatchers
main_dp.include_router(main_router)
help_dp.include_router(help_router)

# Create custom reply keyboards
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/subscribe"), KeyboardButton(text="/referral")],
        [KeyboardButton(text="/terms"),]
    ],
    resize_keyboard=True
)

help_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/faq"), KeyboardButton(text="/subscribe")],
        [KeyboardButton(text="/start")]
    ],
    resize_keyboard=True
)


# Main Bot Handlers
@main_router.message(Command("start"))
async def cmd_start(message: Message):
    if not check_rate_limit(message.from_user.id):
        return await message.reply("Too many requests. Please try again later.")

    user_id = message.from_user.id
    from database import add_user
    ref_code = add_user(user_id)
    await message.reply(
        f"🌟 Welcome to GoldSight! 🌟\n\n"
        f"GoldSight offers premium trading signals to help you make informed decisions in the forex market. Here's what we provide:\n"
        f"🔹 Accurate trading signals\n"
        f"🔹 Priority support\n"
        f"🔹 Early alerts for VIP members\n\n"
        f"Your referral code: {ref_code}\n"
        f"Use the buttons below to explore our features!",
        reply_markup=main_keyboard
    )


@main_router.message(Command("subscribe"))
async def cmd_subscribe(message: Message):
    if not check_rate_limit(message.from_user.id):
        return await message.reply("Too many requests. Please try again later.")

    from database import get_user
    user = get_user(message.from_user.id)
    if user and user[4] == 1:  # Check VIP status
        sub_end = datetime.fromisoformat(user[1])
        days_left = (sub_end - datetime.now()).days
        await message.reply(
            f"🌟 You're a VIP member!\nSubscription ends in {days_left} days.")
        return

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="Weekly ($30)", callback_data="sub_weekly")
            ],
            [
                types.InlineKeyboardButton(text="Monthly ($50)", callback_data="sub_monthly")
            ]
        ]
    )
    await message.reply(
        "📊 GoldSight VIP Plans:\n\n🔹 Weekly: $30\n- 1 week access\n- All signals\n- Priority support\n\n🔸 Monthly: $50\n- 1 month access\n- All signals\n- Priority support\n- Early alerts\n\nSelect your plan:",
        reply_markup=keyboard
    )


@main_router.callback_query(lambda c: c.data in ["sub_weekly", "sub_monthly"])
async def handle_subscription_callback(callback_query: CallbackQuery):
    plan = "Weekly ($30)" if callback_query.data == "sub_weekly" else "Monthly ($50)"
    payment_addresses = (
        "💳 **Payment Addresses**:\n\n"
        "USDT (SOL): `7ryDkprn33twExM1ScdfStcuxTrdDxuJXedTZZH66gAZ`\n\n"
        "USDT (BSC BNB): `0x59b733f5cc3f2b48c703aef91bd9a531f39d60a0`\n\n"
        "USDT (TRC20): `TH6W67eY7XtQusdrWGProevkXsQV6C9iC8`\n\n"
        "USDT (ETH): `0x59b733f5cc3f2b48c703aef91bd9a531f39d60a0`\n\n"
        "USDT (TON): `0x59b733f5cc3f2b48c703aef91bd9a531f39d60a0`\n\n"
        "📤 **Send proof here (screenshot/hash):** @GoldSightSupport"
    )
    await callback_query.message.reply(
        f"You selected the {plan} plan.\n\n{payment_addresses}",
        parse_mode="Markdown"
    )
    await callback_query.answer()  # Acknowledge the callback query


@main_router.message(Command("referral"))
async def cmd_referral(message: Message):
    if not check_rate_limit(message.from_user.id):
        return await message.reply("Too many requests. Please try again later.")

    from database import get_user
    user = get_user(message.from_user.id)
    if user:
        await message.reply(
            f"Your referral code: {user[2]}\nShare to earn 10% commission!"
        )


@main_router.message(Command("terms"))
async def cmd_terms(message: Message):
    if not check_rate_limit(message.from_user.id):
        return await message.reply("Too many requests. Please try again later.")

    terms_and_conditions = (
        "📜 **Terms & Conditions**:\n\n"
        "1. **No Refund Policy**: Payments made for VIP access are non-refundable.\n\n"
        "2. **Educational Purpose**: All trading signals provided are for educational purposes only. GoldSight is not responsible for any financial losses.\n\n"
        "3. **Trade Responsibly**: Users are advised to trade responsibly and within their financial capacity.\n\n"
        "4. **Payment Issues**: For any payment-related issues, contact support at @GoldSightSupport.\n\n"
        "5. **Subscription Renewal**: Subscriptions must be renewed manually. Ensure timely renewal to avoid service interruptions.\n\n"
        "6. **VIP Channel Rules**: Follow the pinned messages in the VIP channel for updates and instructions.\n\n"
        "7. **Account Sharing**: Sharing your VIP account or signals with others is strictly prohibited and may result in account termination.\n\n"
        "8. **Privacy Policy**: We do not share your personal information with third parties. All data is handled securely.\n\n"
        "9. **Service Availability**: GoldSight reserves the right to modify or discontinue services at any time without prior notice.\n\n"
        "10. **Dispute Resolution**: Any disputes will be resolved through direct communication with our support team.\n\n"
        "📌 **Note**: By using our services, you agree to these terms and conditions.\n\n"
        "For further assistance, contact @GoldSightSupport."
    )

    await message.reply(terms_and_conditions, parse_mode="Markdown")


# Help Bot Handlers
@help_router.message(Command("start"))
async def help_start(message: Message):
    await message.reply(
        "🌟 **Welcome to GoldSight Help!** 🌟\n\n"
        "GoldSight is here to provide you with premium trading signals and excellent support. Here's how we can assist you:\n\n"
        "🔹 **Subscribe to VIP**: Gain access to exclusive trading signals.\n"
        "🔹 **Frequently Asked Questions (FAQ)**: Get answers to common questions by typing /faq.\n"
        "🔹 **Support**: Need help? Reach out to our support team at @GoldSightSupport.\n\n"
        "Use the buttons below to navigate!",
        reply_markup=help_keyboard
    )


@help_router.message(Command("faq"))
async def help_faq(message: Message):
    await message.reply(
        "📖 **FAQ**:\n\n"
        "🔹 **How to join VIP?** Use the /subscribe command to view our plans.\n"
        "🔹 **What are the costs?** $30 bi-weekly or $50 monthly.\n"
        "🔹 **Need support?** Contact us at @GoldSightSupport.\n\n"
        "For more information, feel free to ask!"
    )


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
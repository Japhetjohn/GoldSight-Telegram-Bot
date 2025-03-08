# helpers.py
import asyncio
from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv
import os

load_dotenv()
HELP_TOKEN = os.getenv("HELP_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

help_bot = Bot(token=HELP_TOKEN)
help_dp = Dispatcher()  # Changed: No bot here, passed at polling

FAQ = {
    "how to join": "Use /subscribe in @GoldSightBot to join VIP!",
    "cost": "Plans: $30 bi-weekly or $50 monthly.",
    "support": "Email support@goldsight.com or ask here!"
}

@help_dp.message()
async def handle_help(message: types.Message):
    text = message.text.lower()
    print(f"Help Bot received: {text}")  # Debug log
    if text.startswith("/start"):
        await message.reply("Yo Japhet! GoldSight Help Bot here. Ask me or /faq!")
    elif text.startswith("/faq"):
        faq_msg = "\n".join([f"- {k}: {v}" for k, v in FAQ.items()])
        await message.reply(f"FAQs:\n{faq_msg}")
    else:
        for question, answer in FAQ.items():
            if question in text:
                await message.reply(answer)
                return
        await message.reply("Not sure? Try /faq or I’ll ping Japhet!")
        await help_bot.send_message(ADMIN_ID, f"Live support from {message.from_user.id}: {message.text}")

async def start_help_bot():
    print("Help Bot is starting...")  # Startup log
    try:
        await help_dp.start_polling(help_bot)  # Fixed: Pass bot here
    except Exception as e:
        print(f"Help Bot failed: {str(e)}")  # Error log
    print("Help Bot polling ended unexpectedly!")  # Shouldn’t hit this

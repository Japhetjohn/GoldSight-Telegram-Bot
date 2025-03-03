# helpers.py
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os

load_dotenv()
HELP_TOKEN = os.getenv("HELP_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
help_bot = Bot(token=HELP_TOKEN)
help_dp = Dispatcher(bot=help_bot, storage=MemoryStorage())  # Fixed: storage as keyword arg

FAQ = {
    "how to join": "Use /subscribe in @GoldSightBot to join VIP!",
    "cost": "Plans: $30 bi-weekly or $50 monthly.",
    "support": "Email support@goldsight.com or ask here!"
}

@help_dp.message_handler(commands=['start'])
async def help_start(message: types.Message):
    await message.reply("Yo Japhet! GoldSight Help Bot here. Ask me or /faq!")

@help_dp.message_handler(commands=['faq'])
async def send_faq(message: types.Message):
    faq_msg = "\n".join([f"- {k}: {v}" for k, v in FAQ.items()])
    await message.reply(f"FAQs:\n{faq_msg}")

@help_dp.message_handler()
async def handle_queries(message: types.Message):
    text = message.text.lower()
    for question, answer in FAQ.items():
        if question in text:
            await message.reply(answer)
            return
    await message.reply("Not sure? Try /faq or I’ll ping Japhet!")
    await help_bot.send_message(ADMIN_ID, f"Live support from {message.from_user.id}: {message.text}")

async def start_help_bot():
    await help_dp.start_polling(skip_updates=True)

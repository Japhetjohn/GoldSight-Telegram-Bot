import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.exceptions import TelegramNetworkError
import os

help_bot = Bot(token=os.getenv("HELP_BOT_TOKEN"))
help_dp = Dispatcher()
ADMIN_ID = int(os.getenv("ADMIN_ID"))

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

async def start_help_bot():
    print("Help Bot starting...")
    retries = 5
    for attempt in range(retries):
        try:
            await help_dp.start_polling(help_bot)
            break
        except TelegramNetworkError as e:
            print(f"Help Bot network error (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                await asyncio.sleep(5 * (2 ** attempt))
            else:
                print("Help Bot max retries reached.")
                raise
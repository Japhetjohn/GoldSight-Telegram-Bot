# main.py
import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
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
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class SubscribeState(StatesGroup):
    plan = State()
    proof = State()

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    referral = message.get_args()
    ref_code = add_user(user_id, referral)
    welcome_msg = (
        "Welcome to GoldSightBot, Japhet! 📈\n"
        "/subscribe - Join VIP\n"
        "/referral - Earn 10%\n"
        "Help? @Goldsighthelpbot"
    )
    await message.reply(welcome_msg)

@dp.message_handler(commands=['referral'])
async def send_referral(message: types.Message):
    user_id = message.from_user.id
    user = get_user(user_id)
    if user:
        await message.reply(f"Referral link: t.me/GoldSightBot?start={user[2]}\nEarn 10% per paid referral!")
    else:
        await message.reply("Run /start first!")

@dp.message_handler(commands=['subscribe'])
async def subscribe_start(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("$30 Bi-Weekly", callback_data="plan_biweekly"))
    keyboard.add(types.InlineKeyboardButton("$50 Monthly", callback_data="plan_monthly"))
    await message.reply("Pick a plan:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("plan_"))
async def process_plan(callback: types.CallbackQuery, state: FSMContext):
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
    await state.update_data(plan=plan)
    await SubscribeState.proof.set()

@dp.message_handler(content_types=['photo', 'text'], state=SubscribeState.proof)
async def process_proof(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    plan = data['plan']
    await bot.send_message(ADMIN_ID, f"User {user_id} sent proof for {plan}:")
    if message.photo:
        await bot.send_photo(ADMIN_ID, message.photo[-1].file_id)
    elif message.text:
        await bot.send_message(ADMIN_ID, message.text)
    await message.reply("Proof sent! Waiting for approval.")
    await state.finish()

@dp.message_handler(commands=['approve'], is_chat_admin=True)
async def approve_user(message: types.Message):
    args = message.get_args().split()
    if len(args) != 2 or args[1] not in ["biweekly", "monthly"]:
        await message.reply("Use: /approve <user_id> <biweekly/monthly>")
        return
    user_id, plan = int(args[0]), args[1]
    referrer, commission = approve_vip(user_id, plan)
    await bot.send_message(user_id, "You’re VIP! Check the channel.")
    await bot.send_message(VIP_CHANNEL, f"New VIP: @{message.from_user.username}")
    await message.reply(f"Approved {user_id}.")
    if referrer:
        await bot.send_message(referrer, f"Referral bonus: ${commission}!")

@dp.message_handler(commands=['signal'], is_chat_admin=True)
async def post_signal(message: types.Message):
    signal = message.get_args()
    if not signal:
        await message.reply("Use: /signal <text>")
        return
    await bot.send_message(VIP_CHANNEL, f"📈 XAUUSD Signal: {signal}")
    await message.reply("Signal posted!")

async def fetch_auto_signals():
    while True:
        try:
            url = f"https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol=XAU&to_symbol=USD&interval=5min&apikey={ALPHA_VANTAGE_KEY}"
            response = requests.get(url).json()
            if "Time Series FX (5min)" in response:
                latest = response["Time Series FX (5min)"][list(response["Time Series FX (5min)"].keys())[0]]
                signal = f"XAUUSD Latest: {latest['4. close']} (Auto)"
                await bot.send_message(VIP_CHANNEL, f"📈 {signal}")
            else:
                await bot.send_message(ADMIN_ID, "Alpha Vantage API issue—check key!")
        except Exception as e:
            await bot.send_message(ADMIN_ID, f"Auto-signal error: {str(e)}")
        await asyncio.sleep(300)  # Every 5 mins

@dp.message_handler(lambda message: message.chat.id == VIP_CHANNEL and not message.from_user.is_bot)
async def filter_spam(message: types.Message):
    user = get_user(message.from_user.id)
    if not user or user[4] != 1:
        await message.delete()
        await bot.send_message(message.from_user.id, "VIPs only! Use /subscribe.")

async def subscription_task():
    while True:
        expired, reminders = check_subscriptions()
        for user_id in expired:
            await bot.send_message(user_id, "VIP expired! Renew with /subscribe.")
        for user_id in reminders:
            await bot.send_message(user_id, "VIP expires in 2 days! Renew with /subscribe.")
        await asyncio.sleep(86400)  # Daily

async def main():
    init_db()
    asyncio.create_task(subscription_task())
    asyncio.create_task(fetch_auto_signals())
    asyncio.create_task(start_help_bot())
    await dp.start_polling(skip_updates=True)

if __name__ == '_main_':
    asyncio.run(main())

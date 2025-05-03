import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv


load_dotenv()


API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise ValueError("Необходимо установить API_TOKEN в файле .env")

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


currencies = {}


class CurrencyStates(StatesGroup):
    waiting_for_currency_name = State()
    waiting_for_currency_rate = State()
    waiting_for_currency_to_convert = State()
    waiting_for_amount = State()

 
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Я бот для конвертации валют. Используй /save_currency или /convert.")


@dp.message(Command("save_currency"))
async def cmd_save_currency(message: Message, state: FSMContext):
    await state.set_state(CurrencyStates.waiting_for_currency_name)
    await message.answer("Введите название валюты (например, USD):")


@dp.message(CurrencyStates.waiting_for_currency_name)
async def process_currency_name(message: Message, state: FSMContext):
    currency_name = message.text.upper()
    await state.update_data(currency_name=currency_name)
    await state.set_state(CurrencyStates.waiting_for_currency_rate)
    await message.answer(f"Введите курс {currency_name} к рублю:")


@dp.message(CurrencyStates.waiting_for_currency_rate)
async def process_currency_rate(message: Message, state: FSMContext):
    try:
        rate = float(message.text.replace(',', '.'))
        data = await state.get_data()
        currency_name = data['currency_name']
        currencies[currency_name] = rate
        await state.clear()
        await message.answer(f"Курс {currency_name} сохранен: 1 {currency_name} = {rate} RUB")
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число для курса.")


@dp.message(Command("convert"))
async def cmd_convert(message: Message, state: FSMContext):
    await state.set_state(CurrencyStates.waiting_for_currency_to_convert)
    await message.answer("Введите название валюты для конвертации:")


@dp.message(CurrencyStates.waiting_for_currency_to_convert)
async def process_currency_to_convert(message: Message, state: FSMContext):
    currency_name = message.text.upper()
    if currency_name not in currencies:
        await message.answer(f"Валюта {currency_name} не найдена. Используйте /save_currency для добавления.")
        await state.clear()
        return
    
    await state.update_data(currency_to_convert=currency_name)
    await state.set_state(CurrencyStates.waiting_for_amount)
    await message.answer(f"Введите сумму в {currency_name} для конвертации в рубли:")


@dp.message(CurrencyStates.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        data = await state.get_data()
        currency_name = data['currency_to_convert']
        rate = currencies[currency_name]
        result = amount * rate
        await state.clear()
        await message.answer(f"{amount} {currency_name} = {result:.2f} RUB (по курсу 1 {currency_name} = {rate} RUB)")
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число для суммы.")

if __name__ == '__main__':
    dp.run_polling(bot)
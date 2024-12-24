import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.utils.exceptions import MessageNotModified
import os
from aiogram.types import Message
from aiogram.utils.markdown import hbold
import asyncio
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.executor import start_webhook
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from db_worker import update_rates
from buttons.buttons_rates import *
from core.engine import save_correction_factors, load_correction_factors
from config import settings, correction_factors2




# Настройка логирования
logging.basicConfig(filename='24_bot.log', filemode='w',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


# Инициализация бота и диспетчера
loop = asyncio.get_event_loop()
storage = MemoryStorage()
bot = Bot(token=settings.TG_TOKEN, loop=loop)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

# Список разрешенных ID пользователей
ALLOWED_USER_IDS = [1201355458, 1807698423]

# Проверка доступа пользователя
def is_allowed_user(user_id):
    return user_id in ALLOWED_USER_IDS

# Команда /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    if not is_allowed_user(message.from_user.id):
        await message.reply("Доступ запрещен.")
        return
    keyboard = main_menu_keyboard()
    await message.reply(
        "Привет! Я ваш бот для изменения коэффициентов обмена",
        reply_markup=keyboard
    )

# Обработка нажатия кнопки "Изменить коэффициенты"
@dp.callback_query_handler(lambda call: call.data == "change_factors")
async def change_factors(call: types.CallbackQuery):
    await call.answer()
    await call.message.answer("Выберите, какой коэффициент изменить:", reply_markup=factors_menu_keyboard())

# Обработка выбора коэффициента
@dp.callback_query_handler(lambda call: call.data in correction_factors2.keys())
async def select_factor(call: types.CallbackQuery):
    correction_factors = await load_correction_factors()
    if not is_allowed_user(call.from_user.id):
        await call.answer("Доступ запрещен.", show_alert=True)
        return
    factor_key = call.data
    await call.answer()
    await call.message.answer(f"Коэффициенты для {factor_key}: {correction_factors[factor_key]}.\n"
                              "Выберите, что изменить:",
                              reply_markup=adjustment_type_keyboard(factor_key))


# Обработка нажатия на изменение покупки или продажи
@dp.callback_query_handler(lambda call: call.data.endswith("_buy") or call.data.endswith("_sell"))
async def choose_adjustment(call: types.CallbackQuery):
    correction_factors = await load_correction_factors()
    if not is_allowed_user(call.from_user.id):
        await call.answer("Доступ запрещен.", show_alert=True)
        return
    factor_key, adjustment_type = call.data.rsplit('_', 1)
    await call.answer()
    await call.message.answer(f"Текущее значение для {factor_key} - {adjustment_type}: {correction_factors[factor_key][0] if adjustment_type == 'buy' else correction_factors[factor_key][1]}.\n"
                              "Используйте кнопки ниже для изменения:",
                              reply_markup=adjustment_keyboard(factor_key, adjustment_type))


# Обработка нажатия кнопок изменения значения
@dp.callback_query_handler(lambda call: call.data.endswith("_increase") or call.data.endswith("_decrease"))
async def adjust_factor(call: types.CallbackQuery):
    # Загружаем текущие коэффициенты
    correction_factors = await load_correction_factors()

    # Проверяем доступ пользователя
    if not is_allowed_user(call.from_user.id):
        await call.answer("Доступ запрещен.", show_alert=True)
        return

    # Разбираем данные из callback
    factor_key, adjustment_type, action = call.data.rsplit('_', 2)
    buy_factor, sell_factor = correction_factors[factor_key]

    # Устанавливаем шаг изменения
    step = 0.005

    # Изменяем значения
    if action == "increase":
        if adjustment_type == "buy":
            buy_factor += step
        else:
            sell_factor += step
    else:  # decrease
        if adjustment_type == "buy":
            buy_factor -= step
        else:
            sell_factor -= step

    # Округляем значения с заданной точностью
    rounding_precision = 3

    # Обновление коэффициента в словаре с нужной точностью
    correction_factors[factor_key] = [round(buy_factor, rounding_precision), round(sell_factor, rounding_precision)]

        # Сохраняем обновленные коэффициенты
    await save_correction_factors(correction_factors)

        # Перезагружаем коэффициенты из источника для синхронизации
    correction_factors = await load_correction_factors()

        # Формируем текст для сообщения
    new_text = (f"Коэффициенты для {factor_key} обновлены:\n"
                    f"Покупка: {correction_factors[factor_key][0]}, Продажа: {correction_factors[factor_key][1]}")

        # Обновляем сообщение
    try:
        await call.message.edit_text(new_text, reply_markup=adjustment_keyboard(factor_key, adjustment_type))
    except MessageNotModified:
        pass

        # Обновляем курсы
    await update_rates()


# Обработка кнопки "Назад"
@dp.callback_query_handler(lambda call: call.data == "back")
async def back(call: types.CallbackQuery):
    if not is_allowed_user(call.from_user.id):
        await call.answer("Доступ запрещен.", show_alert=True)
        return
    await call.answer()
    await call.message.edit_text("Вы вернулись в главное меню.", reply_markup=main_menu_keyboard())


# Функция для форматирования correction_factors
def format_correction_factors(correction_factors: dict) -> str:
    message = f"{hbold('Список коэффициентов:')}\n\n"
    for key, values in correction_factors.items():
        buy, sell = values
        message += f"{hbold(key)}:\n  Покупка: {buy}\n  Продажа: {sell}\n\n"
    return message


# Обработчик команды /correction_factors
@dp.message_handler(commands=["correction_factors"])
async def show_correction_factors(message: Message):
    correction_factors = await load_correction_factors()  # Загружаем данные
    formatted_message = format_correction_factors(correction_factors)  # Форматируем данные
    await message.answer(formatted_message, parse_mode="HTML")

# Запуск бота
async def on_startup(dp):
    await bot.delete_webhook()
    new = f"{settings.WEBHOOK_HOST}{settings.WEBHOOK_PATH}"
    await bot.set_webhook(new)


async def on_shutdown(dp):
    logging.warning('Shutting down..')
    await bot.delete_webhook()


if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=settings.WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=settings.WEBAPP_HOST,
        port=settings.WEBAPP_PORT,
    )


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Функция для создания инлайн-клавиатуры
def main_menu_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton(text="Изменить коэффициенты", callback_data="change_factors"),
        InlineKeyboardButton(text="Помощь", callback_data="help")
    ]
    keyboard.add(*buttons)
    return keyboard

# Функция для создания клавиатуры для выбора коэффициентов
def factors_menu_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton(text="USDT to GBP", callback_data="usdt_to_gbp"),
        InlineKeyboardButton(text="USDT to AED", callback_data="usdt_to_aed"),
        InlineKeyboardButton(text="USDT to THB", callback_data="usdt_to_thb"),
        InlineKeyboardButton(text="USDT to THB 50", callback_data="usdt_to_thb_50"),
        InlineKeyboardButton(text="USDT to EUR", callback_data="usdt_to_eur"),
        InlineKeyboardButton(text="RUB Cash", callback_data="rub_coff_cash"),
        InlineKeyboardButton(text="RUB Transfer", callback_data="rub_coff_tran"),
        InlineKeyboardButton(text="USDT_BOT", callback_data="usdt_bot_rate"),
        InlineKeyboardButton(text="Назад", callback_data="back")
    ]
    keyboard.add(*buttons)
    return keyboard

# Функция для выбора между покупкой и продажей
def adjustment_type_keyboard(factor_key):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text="Изменить покупку", callback_data=f"{factor_key}_buy"),
        InlineKeyboardButton(text="Изменить продажу", callback_data=f"{factor_key}_sell"),
        InlineKeyboardButton(text="Назад", callback_data="back")
    )
    return keyboard

# Функция для создания клавиатуры изменения значения
def adjustment_keyboard(factor_key, adjustment_type):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text="Вверх", callback_data=f"{factor_key}_{adjustment_type}_increase"),
        InlineKeyboardButton(text="Вниз", callback_data=f"{factor_key}_{adjustment_type}_decrease"),
        InlineKeyboardButton(text="Назад", callback_data="back")
    )
    return keyboard
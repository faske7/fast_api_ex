from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def main_menu_pay():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton(text="Перевод на российскую карту", callback_data="rub_online"),
        InlineKeyboardButton(text="Оплата USDT", callback_data="usdt"),
    ]
    keyboard.add(*buttons)
    return keyboard

async def main_menu_pay2():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton(text="Перевод на российскую карту", callback_data="rub_online_2"),
        InlineKeyboardButton(text="Оплата USDT", callback_data="usdt_2"),
    ]
    keyboard.add(*buttons)
    return keyboard

async def create_complete_request_kb(request_id: int) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с кнопкой для завершения заявки.

    :param request_id: ID заявки, которую нужно завершить.
    :return: Объект InlineKeyboardMarkup с кнопкой.
    """
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton(text="Закрыть заявку", callback_data=f"complete_request_{request_id}"),
        InlineKeyboardButton(text="Отменить заявку", callback_data=f"cancel_request_{request_id}"),
    ]
    keyboard.add(*buttons)
    return keyboard


async def create_take_request_kb(request_id: int) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с кнопкой для взятия заявки.

    :param request_id: Уникальный ID заявки.
    :return: Объект InlineKeyboardMarkup с кнопкой.
    """
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            text="Взять заявку",
            callback_data=f"take_request_{request_id}"
        )
    )

async def create_select_request_kb(request_id: int, ) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с кнопкой для выбора заявки.

    :param request_id: Уникальный ID заявки.
    :return: Объект InlineKeyboardMarkup с кнопкой.
    """
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            text=f"Заявка #{request_id}",
            callback_data=f"select_request_{request_id}"
        )
    )


async def main_menu_2():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton(text="Наши офисы", callback_data="office"),
        InlineKeyboardButton(text="Реферальная система", callback_data="ref"),
        InlineKeyboardButton(text="Обменять", callback_data="start"),
        InlineKeyboardButton(text="Правила обмена", callback_data="rules")
    ]
    keyboard.add(*buttons)
    return keyboard

async def back():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton(text="Назад", callback_data="back"),
    ]
    keyboard.add(*buttons)
    return keyboard

async def ref_buttons():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton(text="Получить ссылку", callback_data="ref_link"),
        InlineKeyboardButton(text="Мои рефералы", callback_data="my_refs"),
        InlineKeyboardButton(text="Назад", callback_data="back"),
    ]
    keyboard.add(*buttons)
    return keyboard
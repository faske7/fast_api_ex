import logging
from aiogram import Bot, types
from config import *
from aiogram.dispatcher import Dispatcher
from aiogram.utils.executor import start_webhook
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from buttons.buttons import *
from core.engine import *
from core.api_rates import get_rub_and_thb, get_usdt_to_thb
from db_worker import RequestsManager, ActiveRequestsManager, AssignedRequestsManager, RequestStatus, UsersManager, RequestPhotoManager, MessagesManager
from aiogram.dispatcher import FSMContext
from texts.texts import *
from texts.user_warn import *
from texts.text_info import *
from texts.logging_text import *
import time

# Настройка логирования
logging.basicConfig(filename='app_24_bot.log', filemode='w',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
# Создаем менеджер message
message_users = MessagesManager()
# Создаем менеджер users
manager_users = UsersManager()
# Создаем менеджер заявок
manager_a = RequestsManager()
# Создаем менеджер активных заявок
manager = ActiveRequestsManager()
# Создаем менеджер закрепленных заявок
assigned_manager = AssignedRequestsManager()
# Создаем экземпляр менеджера
request_photo_manager = RequestPhotoManager()
# Инициализация бота и диспетчера
loop = asyncio.get_event_loop()
storage = MemoryStorage()
bot = Bot(token=settings.TG_TOKEN2, loop=loop)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())
# Создаем класс состояний (для FSM — finite state machine)
class Form(StatesGroup):
    enter_start = State()  # Will be represented in storage as 'Form:name'
    enter_sum = State()  # Ввод суммы
    enter_rub = State()  # выбрал рубли
    enter_tg = State()  # выбрал тг
    enter_usdt = State()  # выбрал юсдт
# Команда /start
@dp.message_handler(commands=['start'], state='*')
async def send_welcome(message: types.Message):
    args = message.get_args()
    referrer_id = None
    # Получение списка ID операторов из базы данных
    operator_user_ids = await manager_users.get_operator_user_ids()
    if args:
        try:
            referrer_id = int(args)
        except ValueError:
            pass  # Некорректный реферальный код

    if int(message.from_user.id) not in operator_user_ids:
        chat_id = message.chat.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        await manager_users.add_or_update_user(
            chat_id=chat_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            total_amount=0,
            referrer_id=referrer_id,
        )
        await Form.enter_sum.set()
        await bot.send_message(chat_id, await start_text_2(), reply_markup=await main_menu_2(), disable_web_page_preview=True)
        return
    else:
        await message.reply(hello_manager)


@dp.message_handler(content_types=types.ContentType.CONTACT, state='*')
async def handle_contact(message: types.Message):
    # Удаляем сообщение с контактом
    await message.delete()

# ручка на сумму
@dp.message_handler(state='*')
async def search(message: types.Message, state: FSMContext):
    first_name = message.from_user.first_name
    full_name = message.from_user.full_name
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text
    # Получение списка ID операторов из базы данных
    operator_user_ids = await manager_users.get_operator_user_ids()
    # Ручка 1: Если число с восклицательным знаком
    if text[:-1].isdigit() and text[-1] == '!':
        entered_sum = int(text[:-1])  # Преобразуем сумму в число
        if entered_sum <= 30 or entered_sum >= 5000001:
            await bot.send_message(chat_id, low_or_max_usdt_text)
        else:
            await state.update_data(entered_sum=entered_sum)

            # Проверяем, есть ли активная заявка в БД
            active_request = await manager.get_request(user_id)

            if active_request:
                elapsed_time = (datetime.utcnow() - active_request.timestamp).total_seconds()
                remaining_time = 30 * 60 - elapsed_time

                if remaining_time > 0:
                    # Обновляем данные суммы и временной метки
                    await manager.add_request(
                        user_id=user_id,
                        request_id=active_request.request_id,
                        entered_sum=entered_sum)
                    await bot.send_message(chat_id, await choose_pay(entered_sum=entered_sum, active_request=active_request), reply_markup=await main_menu_pay2())
            else:
                # Создаем новую заявку
                request_id = await manager_a.create_request(chat_id, entered_sum, first_name)

                await state.update_data(request_id=request_id)

                # Добавляем заявку в БД
                await manager.add_request(user_id=user_id, request_id=request_id, entered_sum=entered_sum)

                # Запускаем задачу для напоминания
                asyncio.create_task(reminder_task(user_id, chat_id, request_id, 25 * 60))

                # Запускаем задачу для удаления
                asyncio.create_task(delete_task(user_id, chat_id, request_id, 30 * 60))

                await bot.send_message(chat_id, await create_payment_message(entered_sum, request_id), reply_markup=await main_menu_pay2())

                # Получение списка ID операторов из базы данных
                operator_user_ids = await manager_users.get_operator_user_ids()

                for operator_id in operator_user_ids:
                    try:
                        await bot.send_message(operator_id,
                        await build_new_request_message(message, user_id, text, request_id),
                        reply_markup=await create_take_request_kb(request_id))
                    except Exception as e:
                            logging.error(await error_send(operator_id, e))

    # Ручка 2: Если просто число
    elif text.isdigit():
        if int(text) <= 999:
            await bot.send_message(chat_id, low_or_max_thb_text)
        else:
            number = int(text)  # Преобразуем текст в число
            rounded_number = round(number / 100) * 100  # Округляем до ближайших 100

            # Проверяем, есть ли активная заявка
            active_request = await manager.get_request(user_id)

            if active_request:
                request_id = active_request.request_id
            else:
                request_id = None

            operator_id = await assigned_manager.get_operator_for_request(request_id)

            if operator_id:
                await bot.send_message(
                    operator_id,
                    await user_message_to_log(user_id, message.from_user.full_name, rounded_number, request_id),
                    reply_markup=await create_complete_request_kb(request_id))
                await bot.send_message(chat_id, mes_send_to_oper)

            else:
                await state.update_data(entered_sum=rounded_number)
                request_id = await manager_a.create_request(chat_id, rounded_number, first_name)
                await manager.add_request(user_id=int(user_id), request_id=int(request_id), entered_sum=int(rounded_number))

                # Записываем в FSM ID заявки
                await state.update_data(request_id=request_id)

                # Запускаем задачу для напоминания
                asyncio.create_task(reminder_task(user_id, chat_id, request_id, 25 * 60))

                # Запускаем задачу для удаления
                asyncio.create_task(delete_task(user_id, chat_id, request_id, 30 * 60))

                await bot.send_message(chat_id, await payment_prompt(request_id=request_id, text=rounded_number), reply_markup=await main_menu_pay())

                # Получение списка ID операторов из базы данных
                operator_user_ids = await manager_users.get_operator_user_ids()
                for operator_id in operator_user_ids:
                    try:
                        await bot.send_message(
                            operator_id,
                            await new_request_notification(user_id, full_name, text),
                            reply_markup=await create_take_request_kb(request_id))
                    except Exception as e:
                        logging.error(await error_send(operator_id, e))

    # Ручка 3: Если ни то, ни другое
    else:
        # Получение списка ID операторов из базы данных
        operator_user_ids = await manager_users.get_operator_user_ids()
        if chat_id in operator_user_ids:
            # Получаем заявки, закрепленные за оператором
            operator_requests = await assigned_manager.get_requests_for_operator(chat_id)
            if not operator_requests:
                await message.reply(no_have)
                return

            # Сохраняем сообщение в TEMP_MESSAGES
            TEMP_MESSAGES[chat_id] = {"text": message.text}

            # Если у оператора несколько активных заявок, предлагаем выбрать
            if len(operator_requests) > 1:
                inline_kb = InlineKeyboardMarkup()
                for assigned_request in operator_requests:
                    inline_kb.add(
                        InlineKeyboardButton(
                            text=await request_number_message(assigned_request.request_id, assigned_request.first_name),
                            callback_data=f"select_req_{assigned_request.request_id}"))
                await message.reply(choose, reply_markup=inline_kb)
            else:

                # Если только одна заявка, отправляем сообщение напрямую
                request_id = operator_requests[0].request_id
                user_chat_id = await manager.get_user_chat_id_by_request_id(request_id)

                if user_chat_id:
                    await message_users.create_message(
                        request_id=request_id,
                        sender=full_name,
                        attachment=None,
                        content=text, )
                    await bot.send_message(user_chat_id, await operator_message(request_id, text))
                    await message.reply(await send_to_user(request_id=request_id))
                else:
                    await message.reply(no_have_user)
        else:
            # Проверяем, есть ли активная заявка
            active_request = await manager.get_request(user_id)

            if active_request:
                request_id = active_request.request_id
            else:
                request_id = None

            operator_id = await assigned_manager.get_operator_for_request(request_id)

            if operator_id:
                await message_users.create_message(
                    request_id=request_id,
                    sender=full_name,
                    attachment=None,
                    content=text, )
                await bot.send_message(
                    operator_id,
                    await user_message_to_log(user_id, full_name, text, request_id),
                    reply_markup=await create_complete_request_kb(request_id))
                await bot.send_message(chat_id, mes_send_to_oper)

            else:
                if request_id is not None:
                    user_data = await state.get_data()
                    user_data['entered_sum'] = user_data.get('entered_sum', 0) or 0
                    user_data['pay_way'] = user_data.get('pay_way', 0) or 0
                    data = user_data['entered_sum']
                    pay_way = user_data['pay_way']

                    # Отправляем сообщение операторам
                    for operator_id in operator_user_ids:
                        try:
                            await message_users.create_message(
                                request_id=request_id,
                                sender=full_name,
                                content=text, )
                            await bot.send_message(
                                operator_id,
                                await new_message_notification(user_id, full_name, request_id, data, pay_way, text),
                            reply_markup=await create_take_request_kb(request_id))
                        except Exception as e:
                            logging.error(await error_send(operator_id, e))

                    await bot.send_message(chat_id, mes_send_to_oper)
                else:
                    # Если заявки нет, создаем новую
                    request_id = await manager_a.create_request(chat_id, 0, first_name)
                    await state.update_data(request_id=request_id)
                    await manager.add_request(user_id=user_id, request_id=request_id, entered_sum=0)
                    # Запускаем задачу для напоминания
                    asyncio.create_task(reminder_task(user_id, chat_id, request_id, 25 * 60))
                    # Запускаем задачу для удаления
                    asyncio.create_task(delete_task(user_id, chat_id, request_id, 30 * 60))
                    await message_users.create_message(
                        request_id=request_id,
                        sender=full_name,
                        content=text, )
                    # Отправляем сообщение операторам
                    for operator_id in operator_user_ids:
                        try:
                            await bot.send_message(
                                operator_id,
                            await new_request_notification(user_id, full_name, text),
                            reply_markup=await create_take_request_kb(request_id))
                        except Exception as e:
                            logging.error(await error_send(operator_id, e))

                    await bot.send_message(chat_id, mes_send_to_oper)

@dp.callback_query_handler(lambda c: c.data, state='*')
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    chat_id = callback_query.from_user.id
    first_name = callback_query.from_user.first_name
    # Получение списка ID операторов из базы данных
    operator_user_ids = await manager_users.get_operator_user_ids()
    if callback_query.data.startswith("select_request_vo_"):
        operator_id = callback_query.from_user.id

        # Проверяем, является ли пользователь оператором
        if operator_id not in operator_user_ids:
            await bot.answer_callback_query(callback_query.id, text_no_available, show_alert=True)
            return

        # Извлекаем request_id из callback_data
        request_id = int(callback_query.data.split("_")[3])

        # Проверяем, относится ли заявка к этому оператору
        operator_requests = await assigned_manager.get_requests_for_operator(operator_id)
        if not any(assigned_request.request_id == request_id for assigned_request in operator_requests):
            await bot.answer_callback_query(callback_query.id, not_for_u, show_alert=True)
            return

        # Отправляем голосовое сообщение пользователю
        await send_voice_to_user(operator_id, request_id)

    if callback_query.data.startswith("select_request_s_"):
        operator_id = callback_query.from_user.id

        # Проверяем, является ли пользователь оператором
        if operator_id not in operator_user_ids:
            await bot.answer_callback_query(callback_query.id, text_no_available, show_alert=True)
            return

        # Извлекаем request_id из callback_data
        request_id = int(callback_query.data.split("_")[3])

        # Проверяем, относится ли заявка к этому оператору
        operator_requests = await assigned_manager.get_requests_for_operator(operator_id)
        if not any(assigned_request.request_id == request_id for assigned_request in operator_requests):
            await bot.answer_callback_query(callback_query.id, not_for_u, show_alert=True)
            return

        # Отправляем стикер пользователю
        await send_sticker_to_user(operator_id, request_id)

    if callback_query.data.startswith("select_request_v_"):
        operator_id = callback_query.from_user.id

        # Проверяем, является ли пользователь оператором
        if operator_id not in operator_user_ids:
            await bot.answer_callback_query(callback_query.id, text_no_available, show_alert=True)
            return

        # Извлекаем request_id из callback_data
        request_id = int(callback_query.data.split("_")[3])

        # Проверяем, относится ли заявка к этому оператору
        operator_requests = await assigned_manager.get_requests_for_operator(operator_id)
        if not any(assigned_request.request_id == request_id for assigned_request in operator_requests):
            await bot.answer_callback_query(callback_query.id, not_for_u, show_alert=True)
            return

        # Отправляем видео пользователю
        await send_video_to_user(operator_id, request_id)

    if callback_query.data.startswith("select_request_p_"):
        operator_id = callback_query.from_user.id

        # Проверяем, является ли пользователь оператором
        if operator_id not in operator_user_ids:
            await bot.answer_callback_query(callback_query.id, text_no_available, show_alert=True)
            return

        # Извлекаем request_id из callback_data
        request_id = int(callback_query.data.split("_")[3])

        # Проверяем, относится ли заявка к этому оператору
        operator_requests = await assigned_manager.get_requests_for_operator(operator_id)
        if not any(assigned_request.request_id == request_id for assigned_request in operator_requests):
            await bot.answer_callback_query(callback_query.id, not_for_u, show_alert=True)
            return

        # Отправляем сообщение пользователю
        await send_photo_to_user(operator_id, request_id)

    if callback_query.data.startswith("cancel_request_"):
        user_id = callback_query.from_user.id

        # Проверяем, является ли пользователь оператором
        if user_id not in operator_user_ids:
            await bot.answer_callback_query(callback_query.id, text=text_no_available,
                                            show_alert=True)
            return

        request_id = int(callback_query.data.split("_")[2])

        # Проверяем, принадлежит ли заявка этому оператору
        assigned_operator = await assigned_manager.get_operator_for_request(request_id)

        if assigned_operator != user_id:
            await bot.answer_callback_query(callback_query.id,
                text=u_can_not,
                show_alert=True)
            return

        # Удаляем заявку из закрепленных
        await assigned_manager.unassign_request(request_id)

        # Удаляем заявку из активных
        active_request = await manager.get_request_by_request_id(request_id)
        if active_request:
            user_id = active_request.user_id
            await manager.remove_request(active_request.user_id)

        # Проверяем, существует ли заявка в базе данных
        active_request_1 = await manager_a.get_request_by_id(request_id)

        if active_request_1:
            # Проверяем статус заявки, чтобы не менять статус у завершенной или отмененной заявки
            if active_request_1.status in [RequestStatus.NEW, RequestStatus.IN_PROGRESS]:
                # Меняем статус заявки на "CANCELED"
                await manager_a.update_status(request_id, RequestStatus.CANCELED.value)

        await state.finish()

        # Уведомляем оператора
        await bot.answer_callback_query(callback_query.id, await req_cancel(request_id=request_id), show_alert=True)

        await bot.send_message(user_id, await req_cancel(request_id=request_id))

    if callback_query.data.startswith("select_req_"):
        operator_id = callback_query.from_user.id

        # Проверяем, является ли пользователь оператором
        if operator_id not in operator_user_ids:
            await bot.answer_callback_query(callback_query.id, text_no_available, show_alert=True)
            return

        request_id = int(callback_query.data.split("_")[2])

        # Проверяем, относится ли заявка к этому оператору
        operator_requests = await assigned_manager.get_requests_for_operator(operator_id)
        if not any(assigned_request.request_id == request_id for assigned_request in operator_requests):
            await bot.answer_callback_query(callback_query.id, not_for_u, show_alert=True)
            return

        # Отправляем сообщение пользователю
        await send_message_to_user(operator_id, request_id)

    if callback_query.data.startswith("complete_request_"):
        user_id = callback_query.from_user.id

        # Проверяем, является ли пользователь оператором
        if user_id not in operator_user_ids:
            await bot.answer_callback_query(callback_query.id, text=text_no_available, show_alert=True)
            return

        # Извлекаем request_id из callback_data
        try:
            request_id = int(callback_query.data.split("_")[2])
        except (IndexError, ValueError):
            await bot.answer_callback_query(callback_query.id, text=unvailable_req, show_alert=True)
            return

        amount_send = await manager_a.get_amount_send(request_id=request_id)
        if amount_send:

            # Проверяем, принадлежит ли заявка этому оператору
            assigned_operator = await assigned_manager.get_operator_for_request(request_id)

            if assigned_operator != user_id:
                await bot.answer_callback_query(
                    callback_query.id,
                    text=u_can_not,
                    show_alert=True)
                return

            # Удаляем заявку из закрепленных
            await assigned_manager.unassign_request(request_id)

            # Удаляем заявку из активных
            active_request = await manager.get_request_by_request_id(request_id)
            if active_request:
                user_id = active_request.user_id
                await manager.remove_request(active_request.user_id)

            # Проверяем, существует ли заявка в базе данных
            active_request_1 = await manager_a.get_request_by_id(request_id)

            if active_request_1:
                # Проверяем статус заявки, чтобы не менять статус у завершенной или отмененной заявки
                if active_request_1.status in [RequestStatus.NEW, RequestStatus.IN_PROGRESS]:
                    # Меняем статус заявки на "COMPLETED"
                    await manager_a.update_status(request_id, RequestStatus.COMPLETED.value)


                await manager_users.update_user_totals(chat_id=user_id, amount=int(amount_send))

                # очищаем fsm
                await state.finish()

                # Уведомляем оператора
                await bot.answer_callback_query(callback_query.id, text=await req_complete(request_id=request_id), show_alert=True)
                await bot.send_message(user_id, await req_complete(request_id=request_id))
        else:
            # Уведомляем оператора
            await bot.answer_callback_query(callback_query.id, text=text_no_have, show_alert=True)

    if callback_query.data.startswith("take_request_"):
        operator_id = callback_query.from_user.id

        # Проверяем, является ли пользователь оператором
        if operator_id not in operator_user_ids:
            await bot.answer_callback_query(callback_query.id, text_no_available, show_alert=True)
            return

        # Извлекаем ID заявки из callback_data
        request_id = int(callback_query.data.split("_")[2])

        # Проверяем наличие заявки в базе данных
        active_request = await manager.get_request_by_request_id(request_id)
        if not active_request:
            await bot.answer_callback_query(
                callback_query.id,
                text=no_have_more,
                show_alert=True)
            return

        # Проверяем, не закреплена ли заявка за другим оператором
        assigned_operator = await assigned_manager.get_operator_for_request(request_id)
        if assigned_operator:
            await bot.answer_callback_query(
                callback_query.id,
                text=another_operator,
                show_alert=True)
            return

        # Закрепляем заявку за оператором
        await assigned_manager.assign_request(operator_id=operator_id, request_id=request_id, first_name=first_name)

        await manager_a.update_status(request_id, RequestStatus.IN_PROGRESS.value)

        # Add oper id to DB
        await manager_a.update_operator_id(request_id=request_id, operator_id=operator_id)

        # Уведомляем оператора о закреплении заявки
        await bot.answer_callback_query(callback_query.id, await take_req(request_id), show_alert=True)

        # Уведомляем оператора о закреплении заявки
        await bot.send_message(operator_id, close_or_cancel, reply_markup = await create_complete_request_kb(request_id))

        # Уведомляем пользователя
        await bot.send_message(active_request.user_id,  # Получаем user_id из записи заявки
            await wait_oper(request_id))

        # Уведомляем оператора о подтверждении
        await bot.send_message(operator_id, await take_req(request_id))

    if callback_query.data == 'usdt_2':
        user_data = await state.get_data()
        # Записываем в FSM sposob заявки
        data = user_data['entered_sum']
        rate_usdt = await get_usdt_to_thb()
        thb_amount = round(int(data) * rate_usdt)

        precise_usdt_amount = round(thb_amount / rate_usdt, 2)
        request_id = user_data['request_id']
        await manager_a.update_amount_come(request_id=request_id, amount_come=int(precise_usdt_amount))
        await state.update_data(amount_send_thb=thb_amount)
        await manager_a.update_amount_send(request_id=request_id, amount_send=int(thb_amount))
        await bot.send_message(chat_id, await generate_calculation_message(request_id, rate_usdt, precise_usdt_amount, thb_amount))
        await bot.send_message(chat_id, await text_pay_usd(), parse_mode="HTML")

    if callback_query.data == 'rub_online_2':
        user_data = await state.get_data()
        # Записываем в FSM sposob заявки
        await state.update_data(pay_way="RUBLI")
        data = user_data['entered_sum']

        rate_rus = await get_rub_and_thb()
        thb_amount = round(int(data) / rate_rus)
        # Уточняем сумму в рублях на основе округленного количества бат
        precise_rub_amount = round(thb_amount * rate_rus)
        number = int(precise_rub_amount)  # Преобразуем текст в число
        rounded_number = round(number / 10) * 10  # Округляем до ближайших 100
        request_id = user_data['request_id']
        await state.update_data(amount_send_thb=thb_amount)
        await manager_a.update_amount_come_rub(request_id=request_id, amount_come_rub=int(rounded_number))
        await manager_a.update_amount_send(request_id=request_id, amount_send=int(thb_amount))
        await bot.send_message(chat_id, await generate_rub_to_thb_calculation(request_id, rate_rus, rounded_number, thb_amount))
        for operator_id in operator_user_ids:
            try:
                # Отправляем сообщение с кнопкой
                await bot.send_message(
                    operator_id,
                    await new_request_notification_rub(callback_query, chat_id, request_id, rounded_number, thb_amount),
                    reply_markup=await create_take_request_kb(request_id))
            except Exception as e:
                logging.error(await error_send(operator_id, e))

    if callback_query.data == 'rub_online':
        user_data = await state.get_data()
        data = user_data['entered_sum']
        new_data = data
        rate_rus = await get_rub_and_thb()
        new_sum = round(int(data)*rate_rus)
        number = int(new_sum)  # Преобразуем текст в число
        rounded_number = round(number / 10) * 10  # Округляем до ближайших 100
        request_id = user_data['request_id']
        await state.update_data(amount_send_thb=new_data)
        await manager_a.update_amount_come_rub(request_id=request_id, amount_come_rub=int(rounded_number))
        await manager_a.update_amount_send(request_id=request_id, amount_send=int(new_data))
        await bot.send_message(chat_id, await generate_rub_to_thb_calculation(request_id, rate_rus, rounded_number, new_data))
        for operator_id in operator_user_ids:
            try:
                # Отправляем сообщение с кнопкой
                await bot.send_message(
                    operator_id,
                    await new_request_notification_rub(callback_query, chat_id, request_id, rounded_number, new_data),
                    reply_markup=await create_take_request_kb(request_id))
            except Exception as e:
                logging.error(await error_send(operator_id, e))

    if callback_query.data == 'usdt':
        user_data = await state.get_data()
        # Записываем в FSM sposob заявки
        await state.update_data(pay_way="USDT")
        data = user_data['entered_sum']
        new_data = data
        rate_usdt = await get_usdt_to_thb()
        new_sum = round(int(data) / rate_usdt, 2)
        # Записываем в FSM usdt заявки
        request_id = user_data['request_id']
        await state.update_data(amount_send_thb=new_data)
        await manager_a.update_amount_come(request_id=request_id, amount_come=int(new_sum))
        await manager_a.update_amount_send(request_id=request_id, amount_send=int(data))
        await bot.send_message(chat_id, await generate_calculation_message(request_id, rate_usdt, new_sum, data))
        await bot.send_message(chat_id, await text_pay_usd(), parse_mode="HTML")

    if callback_query.data == 'rules':
        await bot.send_message(chat_id, text_rules, reply_markup=await back())

    if callback_query.data == 'office':
        await bot.send_message(chat_id, office_text, reply_markup=await back(), disable_web_page_preview=True)

    if callback_query.data == 'ref':
        await bot.send_message(chat_id, ref_text, reply_markup=await ref_buttons())
    if callback_query.data == 'ref_link':
        await referral_handler(chat_id)
    if callback_query.data == 'my_refs':
        await my_referrals_handler(chat_id)
    if callback_query.data == 'back':
        await bot.send_message(chat_id, await start_text_2(), reply_markup=await main_menu_2(), disable_web_page_preview=True)
    if callback_query.data == 'start':
        await bot.send_message(chat_id, text_start_3)

async def reminder_task(user_id, chat_id, request_id, delay):
    """
    Отправляет напоминание о заявке, если истекает время.
    """
    await asyncio.sleep(delay)  # Ждем указанное время

    # Получаем активную заявку из базы данных
    active_request = await manager.get_request(user_id)

    if active_request and active_request.request_id == request_id:
        elapsed_time = (datetime.utcnow() - active_request.timestamp).total_seconds()
        remaining_time = 30 * 60 - elapsed_time

        # Если осталось менее 5 минут, отправляем напоминание
        if remaining_time <= 5 * 60:
            await bot.send_message(chat_id, await min_5(request_id))

async def delete_task(user_id, chat_id, request_id, delay):
    """
    Удаляет заявку из базы данных после истечения времени.
    """
    await asyncio.sleep(delay)  # Ждем указанное время

    # Проверяем, существует ли заявка в базе данных
    active_request = await manager.get_request(user_id)

    # Удаляем заявку из закрепленных
    try:
        await assigned_manager.unassign_request(request_id)
    except Exception:
        logging.info(no_have_ass)

    # Проверяем, существует ли заявка в базе данных
    active_request_1 = await manager_a.get_request_by_id(request_id)

    if active_request_1 and active_request_1.chat_id == chat_id:
        # Проверяем статус заявки, чтобы не менять статус у завершенной или отмененной заявки
        if active_request_1.status in [RequestStatus.NEW, RequestStatus.IN_PROGRESS]:
            # Меняем статус заявки на "CANCELED"
            await manager_a.update_status(request_id, RequestStatus.CANCELED.value)

    if active_request:
        await manager.remove_request(active_request.user_id)
        await bot.send_message(chat_id, await request_timeout_notification(request_id))

async def send_message_to_user(operator_id, request_id):
    # Проверяем, есть ли временное сообщение
    if operator_id not in TEMP_MESSAGES:
        await bot.send_message(operator_id, no_have_text)
        return

    # Ищем пользователя, связанного с заявкой
    user_chat_id = await manager.get_user_chat_id_by_request_id(request_id)

    if user_chat_id:
        # Отправляем сообщение пользователю
        text = TEMP_MESSAGES[operator_id]["text"]
        await bot.send_message(user_chat_id, await operator_message(request_id, text))
        await bot.send_message(operator_id, await send_to_user(request_id))
        del TEMP_MESSAGES[operator_id]  # Удаляем временное сообщение
    else:
        await bot.send_message(operator_id, no_have_user)

async def send_photo_to_user(operator_id, request_id):
    # Проверяем, есть ли временное сообщение
    if operator_id not in TEMP_MESSAGES:
        await bot.send_message(operator_id, no_photo)
        return

    # Ищем пользователя, связанного с заявкой
    user_chat_id = await manager.get_user_chat_id_by_request_id(request_id)

    if user_chat_id:
        # Отправляем сообщение пользователю
        photo_file_id = TEMP_MESSAGES[operator_id]["photo"]
        # Скачиваем файл
        file_info = await bot.get_file(photo_file_id)
        downloaded_file = await bot.download_file(file_info.file_path)

        # Получаем бинарные данные фото
        photo_bytes = downloaded_file.getvalue()

        # Сохраняем фото в базе данных через менеджер
        try:
            await request_photo_manager.save_photo(request_id=request_id, chat_id=user_chat_id,
                                                   image_data=photo_bytes)
        except ValueError as e:
            await bot.send_message(operator_id, str(e))
            return
        await bot.send_photo(
            chat_id=user_chat_id,
            photo=photo_file_id,
            caption=await operator_screenshot_notification(request_id))
        await bot.send_message(operator_id, await photo_to_user(request_id))
        del TEMP_MESSAGES[operator_id]  # Удаляем временное сообщение
    else:
        await bot.send_message(operator_id, no_have_user)

async def send_video_to_user(operator_id, request_id):
    # Проверяем, есть ли временное сообщение
    if operator_id not in TEMP_MESSAGES or "video" not in TEMP_MESSAGES[operator_id]:
        await bot.send_message(operator_id, no_video)
        return

    # Ищем пользователя, связанного с заявкой
    user_chat_id = await manager.get_user_chat_id_by_request_id(request_id)

    if user_chat_id:
        # Отправляем видео пользователю
        video_file_id = TEMP_MESSAGES[operator_id]["video"]

        await bot.send_video(
            chat_id=user_chat_id,
            video=video_file_id,
            caption=await operator_video_notification(request_id)
        )
        await bot.send_message(operator_id, await video_to_user(request_id))
        del TEMP_MESSAGES[operator_id]  # Удаляем временное сообщение
    else:
        await bot.send_message(operator_id, no_have_user)

async def send_sticker_to_user(operator_id, request_id):
    # Проверяем, есть ли временное сообщение
    if operator_id not in TEMP_MESSAGES or "sticker" not in TEMP_MESSAGES[operator_id]:
        await bot.send_message(operator_id, no_sticker)
        return

    # Ищем пользователя, связанного с заявкой
    user_chat_id = await manager.get_user_chat_id_by_request_id(request_id)

    if user_chat_id:
        # Отправляем стикер пользователю
        sticker_file_id = TEMP_MESSAGES[operator_id]["sticker"]

        await bot.send_sticker(
            chat_id=user_chat_id,
            sticker=sticker_file_id)
        await bot.send_message(
            chat_id=user_chat_id,
            text=await operator_sticker_notification(request_id))
        await bot.send_message(operator_id, await send_to_user(request_id))
        del TEMP_MESSAGES[operator_id]  # Удаляем временное сообщение
    else:
        await bot.send_message(operator_id, no_have_user)

async def send_voice_to_user(operator_id, request_id):
    # Проверяем, есть ли временное сообщение
    if operator_id not in TEMP_MESSAGES or "voice" not in TEMP_MESSAGES[operator_id]:
        await bot.send_message(operator_id, "Нет голосового сообщения для отправки")
        return

    # Ищем пользователя, связанного с заявкой
    user_chat_id = await manager.get_user_chat_id_by_request_id(request_id)

    if user_chat_id:
        # Отправляем голосовое сообщение пользователю
        voice_file_id = TEMP_MESSAGES[operator_id]["voice"]

        await bot.send_voice(
            chat_id=user_chat_id,
            voice=voice_file_id,
            caption=f"🔔 Поступило новое голосовое сообщение от оператора для заявки #{request_id}."
        )
        await bot.send_message(operator_id, f"Голосовое сообщение отправлено пользователю (заявка #{request_id}).")
        del TEMP_MESSAGES[operator_id]  # Удаляем временное сообщение
    else:
        await bot.send_message(operator_id, "Не удалось найти пользователя для этой заявки.")

# Обработчик для фото
@dp.message_handler(content_types=['photo'], state='*')
async def handle_photo(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    chat_id = message.chat.id
    full_name = message.from_user.full_name
    # Получаем файл ID для фото
    photo_file_id = message.photo[-1].file_id  # Берем последнюю (самую качественную) версию фото
    # Сохраняем фото в файл
    photo = message.photo[-1]
    timestamp = int(time.time())
    file_name = f"{timestamp}.jpg"
    file_path = os.path.join("media/uploads/attachments", file_name)
    # Убедимся, что директория существует
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except FileExistsError:
            pass  # Игнорируем ошибку, если директория уже создана

    await photo.download(destination=file_path)

    file_info = await bot.get_file(photo_file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    # Получение списка ID операторов из базы данных
    operator_user_ids = await manager_users.get_operator_user_ids()
    # Получаем бинарные данные фото
    photo_bytes = downloaded_file.getvalue()
    if chat_id in operator_user_ids:
        # Получаем заявки, закрепленные за оператором
        operator_requests = await assigned_manager.get_requests_for_operator(chat_id)
        if not operator_requests:
            await message.reply(no_have)
            return

        # Если у оператора несколько активных заявок, предлагаем выбрать
        if len(operator_requests) > 1:
            inline_kb = InlineKeyboardMarkup()
            for assigned_request in operator_requests:
                # Сохраняем photo в TEMP_MESSAGES

                TEMP_MESSAGES[chat_id] = {"photo": photo_file_id}

                inline_kb.add(
                    InlineKeyboardButton(
                        text=await request_number_message(assigned_request.request_id, assigned_request.first_name),
                        callback_data=f"select_request_p_{assigned_request.request_id}"))
            await message.reply(choose, reply_markup=inline_kb)
        else:
            # Если только одна заявка, отправляем сообщение напрямую
            request_id = operator_requests[0].request_id
            user_chat_id = await manager.get_user_chat_id_by_request_id(request_id)

            if user_chat_id:
                # Сохраняем фото в базе данных через менеджер
                try:
                    await request_photo_manager.save_photo(request_id=request_id, chat_id=user_chat_id,
                                                           image_data=photo_bytes)
                except ValueError as e:
                    await bot.send_message(chat_id, str(e))
                    return
                await bot.send_photo(
                    chat_id=user_chat_id,
                    photo=photo_file_id,
                    caption=await operator_screenshot_notification(request_id))
                await message.reply(await photo_to_user(request_id))
            else:
                await message.reply(no_have_user)

    else:
        # Проверяем, есть ли активная заявка
        active_request = await manager.get_request(user_id)

        if active_request:
            request_id = active_request.request_id
        else:
            request_id = None

        operator_id = await assigned_manager.get_operator_for_request(request_id)

        if operator_id:
            # Сохраняем фото в базе данных через менеджер
            try:
                await request_photo_manager.save_photo(request_id=request_id, chat_id=user_id, image_data=photo_bytes)
            except ValueError as e:
                await bot.send_message(chat_id, str(e))
                return
            await message_users.create_message(request_id=request_id,
                                               sender="user",
                                               content=message.caption or "",  # Сохраняем текст сообщения, если есть
                                               attachment=file_path)
            user_data = await state.get_data()

            entered_sum = user_data.get('entered_sum')
            await bot.send_photo(
                chat_id=operator_id,
                photo=photo_file_id,
                caption=await user_screenshot_notification(user_id, full_name, request_id, entered_sum),
                reply_markup=await create_complete_request_kb(request_id))
        else:
            if request_id is not None:
                # Сохраняем фото в базе данных через менеджер
                try:
                    await message_users.create_message(request_id=request_id,
                            sender="user",
                            content=message.caption or "",  # Сохраняем текст сообщения, если есть
                            attachment=file_path )
                    await request_photo_manager.save_photo(request_id=request_id, chat_id=user_id, image_data=photo_bytes)
                except ValueError as e:
                    await bot.send_message(chat_id, str(e))
                    return
                # Отправляем фото всем операторам
                for operator_id in operator_user_ids:
                    try:
                        await bot.send_photo(
                chat_id=operator_id,
                photo=photo_file_id,
                caption=await user_screenshot_notification2(user_id, full_name, request_id),
                reply_markup=await create_complete_request_kb(request_id))
                    except Exception as e:
                        logging.error(await error_send(operator_id, e))

                # Уведомляем пользователя
                await bot.send_message(chat_id, mes_send_to_oper)

# Обработчик для видео
@dp.message_handler(content_types=['video'], state='*')
async def handle_video(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    chat_id = message.chat.id
    full_name = message.from_user.full_name
    # Получаем файл ID для видео
    video_file_id = message.video.file_id
    # Получение списка ID операторов из базы данных
    operator_user_ids = await manager_users.get_operator_user_ids()

    if chat_id in operator_user_ids:
        # Получаем заявки, закрепленные за оператором
        operator_requests = await assigned_manager.get_requests_for_operator(chat_id)
        if not operator_requests:
            await message.reply(no_have)
            return

        # Если у оператора несколько активных заявок, предлагаем выбрать
        if len(operator_requests) > 1:
            inline_kb = InlineKeyboardMarkup()
            for assigned_request in operator_requests:
                # Сохраняем video в TEMP_MESSAGES
                TEMP_MESSAGES[chat_id] = {"video": video_file_id}

                inline_kb.add(
                    InlineKeyboardButton(
                        text=await request_number_message(assigned_request.request_id, assigned_request.first_name),
                        callback_data=f"select_request_v_{assigned_request.request_id}"))
            await message.reply(choose, reply_markup=inline_kb)
        else:
            # Если только одна заявка, отправляем сообщение напрямую
            request_id = operator_requests[0].request_id
            user_chat_id = await manager.get_user_chat_id_by_request_id(request_id)

            if user_chat_id:
                await bot.send_video(
                    chat_id=user_chat_id,
                    video=video_file_id,
                    caption=await operator_video_notification(request_id))
                await message.reply(await video_to_user(request_id))
            else:
                await message.reply(no_have_user)

    else:
        # Проверяем, есть ли активная заявка
        active_request = await manager.get_request(user_id)

        if active_request:
            request_id = active_request.request_id
        else:
            request_id = None

        operator_id = await assigned_manager.get_operator_for_request(request_id)

        if operator_id:
            user_data = await state.get_data()
            entered_sum = user_data.get('entered_sum')

            await bot.send_video(
                chat_id=operator_id,
                video=video_file_id,
                caption=await user_video_notification(user_id, full_name, request_id, entered_sum),
                reply_markup=await create_complete_request_kb(request_id))
        else:
            if request_id is not None:
                # Отправляем видео всем операторам
                for operator_id in operator_user_ids:
                    try:
                        await bot.send_video(
                            chat_id=operator_id,
                            video=video_file_id,
                            caption=await user_video_notification2(user_id, full_name, request_id),
                            reply_markup=await create_complete_request_kb(request_id))
                    except Exception as e:
                        logging.error(await error_send(operator_id, e))

                # Уведомляем пользователя
                await bot.send_message(chat_id, mes_send_to_oper)

# Обработчик для стикеров
@dp.message_handler(content_types=['sticker'], state='*')
async def handle_sticker(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    chat_id = message.chat.id
    full_name = message.from_user.full_name
    # Получаем файл ID для стикера
    sticker_file_id = message.sticker.file_id

    # Получение списка ID операторов из базы данных
    operator_user_ids = await manager_users.get_operator_user_ids()

    if chat_id in operator_user_ids:
        # Получаем заявки, закрепленные за оператором
        operator_requests = await assigned_manager.get_requests_for_operator(chat_id)
        if not operator_requests:
            await message.reply(no_have)
            return

        # Если у оператора несколько активных заявок, предлагаем выбрать
        if len(operator_requests) > 1:
            inline_kb = InlineKeyboardMarkup()
            for assigned_request in operator_requests:
                # Сохраняем sticker в TEMP_MESSAGES
                TEMP_MESSAGES[chat_id] = {"sticker": sticker_file_id}

                inline_kb.add(
                    InlineKeyboardButton(
                        text=await request_number_message(assigned_request.request_id, assigned_request.first_name),
                        callback_data=f"select_request_s_{assigned_request.request_id}"))
            await message.reply(choose, reply_markup=inline_kb)
        else:
            # Если только одна заявка, отправляем сообщение напрямую
            request_id = operator_requests[0].request_id
            user_chat_id = await manager.get_user_chat_id_by_request_id(request_id)

            if user_chat_id:
                await bot.send_sticker(
                    chat_id=user_chat_id,
                    sticker=sticker_file_id)
                await bot.send_message(user_chat_id, await operator_sticker_notification(request_id))
                await message.reply(await sticker_sent_to_user(request_id))
            else:
                await message.reply(no_have)

    else:
        # Проверяем, есть ли активная заявка
        active_request = await manager.get_request(user_id)

        if active_request:
            request_id = active_request.request_id
        else:
            request_id = None

        operator_id = await assigned_manager.get_operator_for_request(request_id)

        if operator_id:

            user_data = await state.get_data()
            entered_sum = user_data.get('entered_sum')

            await bot.send_sticker(
                chat_id=operator_id,
                sticker=sticker_file_id
            )
            await bot.send_message(
                chat_id=operator_id,
                text=await user_sticker_notification2(user_id, full_name, request_id, entered_sum),
                reply_markup=await create_complete_request_kb(request_id)
            )
        else:
            if request_id is not None:
                # Отправляем стикер всем операторам
                for operator_id in operator_user_ids:
                    try:
                        await bot.send_sticker(
                            chat_id=operator_id,
                            sticker=sticker_file_id)
                        await bot.send_message(
                            chat_id=operator_id,
                            text=await user_sticker_notification(user_id, full_name, request_id),
                            reply_markup=await create_complete_request_kb(request_id))
                    except Exception as e:
                        logging.error(await error_send(operator_id, e))

                # Уведомляем пользователя
                await bot.send_message(chat_id, mes_send_to_oper)

# Обработчик для голосовых сообщений
@dp.message_handler(content_types=['voice'], state='*')
async def handle_voice(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    chat_id = message.chat.id
    full_name= message.from_user.full_name

    # Получение списка ID операторов из базы данных
    operator_user_ids = await manager_users.get_operator_user_ids()

    # Получаем файл ID для голосового сообщения
    voice_file_id = message.voice.file_id

    if chat_id in operator_user_ids:
        # Получаем заявки, закрепленные за оператором
        operator_requests = await assigned_manager.get_requests_for_operator(chat_id)
        if not operator_requests:
            await message.reply(no_have)
            return

        # Если у оператора несколько активных заявок, предлагаем выбрать
        if len(operator_requests) > 1:
            inline_kb = InlineKeyboardMarkup()
            for assigned_request in operator_requests:
                # Сохраняем voice в TEMP_MESSAGES
                TEMP_MESSAGES[chat_id] = {"voice": voice_file_id}

                inline_kb.add(
                    InlineKeyboardButton(
                        text=await request_number_message(assigned_request.request_id, assigned_request.first_name),
                        callback_data=f"select_request_vo_{assigned_request.request_id}"
                    ))
            await message.reply(choose, reply_markup=inline_kb)
        else:
            # Если только одна заявка, отправляем сообщение напрямую
            request_id = operator_requests[0].request_id
            user_chat_id = await manager.get_user_chat_id_by_request_id(request_id)

            if user_chat_id:
                await bot.send_voice(
                    chat_id=user_chat_id,
                    voice=voice_file_id,
                    caption=await operator_voice_message_notification(request_id))
                await message.reply(await gs_to_user(request_id))
            else:
                await message.reply(no_have_user)

    else:
        # Проверяем, есть ли активная заявка
        active_request = await manager.get_request(user_id)

        if active_request:
            request_id = active_request.request_id
        else:
            request_id = None

        operator_id = await assigned_manager.get_operator_for_request(request_id)

        if operator_id:
            user_data = await state.get_data()
            entered_sum = user_data.get('entered_sum')

            await bot.send_voice(
                chat_id=operator_id,
                voice=voice_file_id,
            )
            await bot.send_message(
                chat_id=operator_id,
                text=await voice_message_notification(user_id, full_name, request_id, entered_sum),
                reply_markup=await create_complete_request_kb(request_id))
        else:
            if request_id is not None:
                user_data = await state.get_data()
                entered_sum = user_data.get('entered_sum')

                # Отправляем голосовое всем операторам
                for operator_id in operator_user_ids:
                    try:
                        await bot.send_voice(
                            chat_id=operator_id,
                            voice=voice_file_id
                        )
                        await bot.send_message(
                            chat_id=operator_id,
                            text=await voice_message_notification(user_id, full_name, request_id, entered_sum),
                            reply_markup=await create_complete_request_kb(request_id))
                    except Exception as e:
                        logging.error(await error_send(operator_id, e))

                # Уведомляем пользователя
                await bot.send_message(chat_id, mes_send_to_oper)


async def referral_handler(chat_id):
    referral_link = f"https://t.me/{settings.BOT_USERNAME}?start={chat_id}"
    await bot.send_message(chat_id, await send_referral_message(referral_link))

async def my_referrals_handler(chat_id):
    referral_count = await manager_users.get_referral_count(chat_id)
    await bot.send_message(chat_id, await my_ref_text(referral_count))

# Запуск бота
async def on_startup(dp):
    await bot.delete_webhook()
    new = f"{settings.WEBHOOK_HOST}{settings.WEBHOOK_PATH_2}"
    await bot.set_webhook(new)

async def on_shutdown(dp):
    logging.warning('Shutting down..')
    await bot.delete_webhook()

if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=settings.WEBHOOK_PATH_2,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=settings.WEBAPP_HOST,
        port=settings.WEBAPP_PORT_2,
    )
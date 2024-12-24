

async def my_ref_text(referral_count):
    my_ref_text=f"Вы пригласили {referral_count} пользователей."
    return my_ref_text


async def req_cancel(request_id):
    req_cancel = f"Заявка #{request_id} успешно ОТМЕНЕНА."
    return req_cancel


async def req_complete(request_id):
    req_complete = f"Заявка #{request_id} успешно ЗАВЕРШЕНА."
    return req_complete


async def send_to_user(request_id):
    send_to_user = f"Сообщение отправлено пользователю (заявка #{request_id})."
    return send_to_user


async def take_req(request_id):
    take_req = f"Вы взяли заявку #{request_id}."
    return take_req


async def wait_oper(request_id):
    wait_oper = f"Вашей заявкой #{request_id} занимается оператор. Пожалуйста, ожидайте."
    return wait_oper


async def min_5(request_id):
    min_5 = f"""
⏳ Напоминаем, что ваша заявка #{request_id} скоро завершится.

У вас осталось менее 5 минут, чтобы отправить скриншот.

Если время истечёт, нужно будет создать новую заявку.
                """
    return min_5


async def photo_to_user(request_id):
    photo_to_user = f"Сообщение отправлено пользователю (заявка #{request_id})."
    return photo_to_user

async def video_to_user(request_id):
    video_to_user = f"Сообщение отправлено пользователю (заявка #{request_id})."
    return video_to_user

async def gs_to_user(request_id):
    gs_to_user = f"Сообщение отправлено пользователю (заявка #{request_id})."
    return gs_to_user

async def send_referral_message(referral_link):
    message = f"Приглашайте друзей с помощью этой ссылки и получайте бонусы:\n{referral_link}"
    return message

async def create_payment_message(entered_sum, request_id):
    message = f"""
Пожалуйста, выберите способ оплаты.

Сумма к оплате: {entered_sum} 

Номер вашей заявки: #{request_id}
    """
    return message

async def build_new_request_message(message, user_id, text, request_id):
    return f"""
🔔 Новый запрос от пользователя {message.from_user.full_name} (ID: {user_id}):

📩 Сообщение: {text}

Пожалуйста, нажмите кнопку ниже, чтобы взять эту заявку #{request_id}.
"""

async def user_message_to_log(user_id, full_name, text, request_id):
    formatted_message = f"Сообщение от пользователя {full_name} (ID: {user_id}) ЗАЯВКА {request_id}:\n\n{text}"
    return formatted_message


async def payment_prompt(request_id, text):
    message = f"""
Пожалуйста, выберите способ оплаты.

Сумма к получению: {text} бат

Номер вашей заявки: #{request_id}
    """
    return message


async def new_request_notification(user_id, full_name, text):
    notification = f"""
🔔 Новый запрос от пользователя {full_name} (ID: {user_id}):

📩 Сообщение: {text}

Пожалуйста, нажмите кнопку ниже, чтобы взять эту заявку.
    """
    return notification

async def new_message_notification(user_id, full_name, request_id, data, pay_way, text):
    notification = f"""
🔔 Поступило новое сообщение от пользователя {full_name} (ID: {user_id}) для заявки #{request_id}.
Сумма: {data}
Способ: {pay_way}
Текст: {text}
Пожалуйста, обработайте его.
    """
    return notification

async def operator_message(request_id, text):
    message = f"(заявка #{request_id}) Сообщение от оператора:\n\n{text}"
    return message

async def request_timeout_notification(request_id):
    message = f"""
❌ Заявка #{request_id} была удалена, так как истекло время ожидания.

Если вам всё ещё нужно продолжить, создайте новую заявку.
    """
    return message

async def generate_calculation_message(request_id, rate_usdt, precise_usdt_amount, thb_amount):
    message = f'''
Ваш расчёт:
Номер заявки {request_id}
Курс: {rate_usdt}

Вы отправляете: {precise_usdt_amount} USDT
К получению: {thb_amount} бат

🚨 Обратите внимание! Расчет действителен в течение 15 минут.

Доступные ATM для снятия: 🟩 Kasikorn до 500,000 THB | 🟦 BangkokBank до 200,000 THB | 🟪 SCB до 5,000 THB
    '''
    return message

async def generate_rub_to_thb_calculation(request_id, rate_rus, precise_rub_amount, thb_amount):
    message = f'''
Ваш расчёт:
Номер заявки {request_id}
Курс: {rate_rus}

Вы отправляете: {precise_rub_amount} RUB Bank
К получению: {thb_amount} бат

🚨 Обратите внимание! Расчет действителен в течение 15 минут.

Доступные ATM для снятия: 🟩 Kasikorn до 500,000 THB | 🟦 BangkokBank до 200,000 THB | 🟪 SCB до 5,000 THB
    '''
    return message

async def new_request_notification_rub(callback_query, chat_id, request_id, precise_rub_amount, thb_amount):
    message = f"""
        🔔 Новый запрос от пользователя {callback_query.from_user.full_name} (ID: {chat_id}):

        📩 Сообщение: 
            Номер заявки {request_id}
            Сумма: {precise_rub_amount} отправляет рублей
            К получению: {thb_amount} бат
        Пожалуйста, нажмите кнопку ниже, чтобы взять эту заявку.
    """
    return message

async def voice_message_notification(user_id, full_name, request_id, entered_sum):
    message = f"""
🔔 Поступило новое голосовое сообщение от пользователя {full_name} (ID: {user_id}) для заявки #{request_id}.
Сумма: {entered_sum}
Пожалуйста, обработайте его.
    """
    return message

async def operator_video_notification(request_id):
    message = f"""
🔔 Поступило новое видео от оператора для заявки #{request_id}.
Пожалуйста, обработайте его.
    """
    return message

async def user_video_notification(user_id, full_name, request_id, entered_sum):
    message = f"""
🔔 Поступило новое видео от пользователя {full_name} (ID: {user_id}) для заявки #{request_id}.
Сумма: {entered_sum}
Пожалуйста, обработайте его.
    """
    return message

async def user_video_notification2(user_id, full_name, request_id):
    message = f"""
🔔 Поступило новое видео от пользователя {full_name} (ID: {user_id}) для заявки #{request_id}.
Пожалуйста, обработайте его.
    """
    return message

async def user_screenshot_notification(user_id, full_name, request_id, entered_sum):
    message = f"""
🔔 Поступил новый скриншот от пользователя {full_name} (ID: {user_id}) для заявки #{request_id}.
Сумма: {entered_sum}
Пожалуйста, обработайте его.
    """
    return message

async def user_screenshot_notification2(user_id, full_name, request_id):
    message = f"""
🔔 Поступил новый скриншот от пользователя {full_name} (ID: {user_id}) для заявки #{request_id}.
Пожалуйста, обработайте его.
    """
    return message

async def operator_screenshot_notification(request_id):
    message = f"""
🔔 Поступил новый скриншот от оператора для заявки #{request_id}.
Пожалуйста, обработайте его.
    """
    return message

async def user_sticker_notification(user_id, full_name, request_id):
    message = f"""
🔔 Поступил новый стикер от пользователя {full_name} (ID: {user_id}) для заявки #{request_id}.
Пожалуйста, обработайте его.
    """
    return message

async def user_sticker_notification2(user_id, full_name, request_id, entered_sum):
    message = f"""
🔔 Поступил новый стикер от пользователя {full_name} (ID: {user_id}) для заявки #{request_id}.
Сумма: {entered_sum}
Пожалуйста, обработайте его.
    """
    return message

async def operator_sticker_notification(request_id):
    message = f"🔔 Поступил новый стикер от оператора для заявки #{request_id}."
    return message

async def request_number_message(request_id, first_name):
    message = f"Заявка #{request_id} Name {first_name}"
    return message

async def operator_voice_message_notification(request_id):
    message = f"🔔 Поступило новое голосовое сообщение от оператора для заявки #{request_id}."
    return message

async def sticker_sent_to_user(request_id):
    message = f"Стикер отправлен пользователю (заявка #{request_id})."
    return message



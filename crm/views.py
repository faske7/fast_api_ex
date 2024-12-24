from django.shortcuts import render, get_object_or_404, redirect
from .models import Requests, Message, RequestStatus
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import requests
import logging
from django.contrib.auth.models import User
from bot_thb_24 import bot
from asgiref.sync import sync_to_async
from texts.texts import text_finish
from django.urls import reverse

from django.http import HttpResponseRedirect
from db_worker import UsersManager, RequestsManager, ActiveRequestsManager, AssignedRequestsManager
from django.contrib import messages
from sqlalchemy.exc import NoResultFound
from django.utils.decorators import async_only_middleware


# Создаем менеджер активных заявок
manager = ActiveRequestsManager()
# Создаем менеджер закрепленных заявок
assigned_manager = AssignedRequestsManager()
# Создаем менеджер users
manager_users = UsersManager()
# Создаем менеджер заявок
manager_a = RequestsManager()
# Настройка логирования
logging.basicConfig(filename='app_24_bot.log', filemode='w',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

@login_required
async def request_list(request):
    """
    Список всех заявок, назначенных текущему оператору.
    # """
    # requests = Requests.objects.filter(operator_id=request.user.id).exclude(
    #     status__in=[RequestStatus.CANCELED, RequestStatus.COMPLETED]
    # ).order_by("-timestamp")
    return render(request, "request_list.html", {})

@login_required
def request_detail(request, request_id):
    """
    Просмотр деталей заявки и отправка сообщения.
    """
    user_request = get_object_or_404(Requests, id=request_id)
    messages = user_request.messages.all().order_by("created_at")
    chat_id = user_request.chat_id

    # Проверяем, что request.user - это экземпляр User
    operator_id = None
    if isinstance(request.user, User):
        try:
            operator_id = int(request.user.first_name)  # Предполагаем, что first_name - число
        except (ValueError, TypeError):
            operator_id = None

    if request.method == "POST":
        content = request.POST.get("message")
        attachment = request.FILES.get("attachment")
        if user_request.operator_id:
            return redirect("crm:request_detail", request_id=user_request.id)

        if content:
            Message.objects.create(
                request_id=user_request.id,
                sender="operator",  # Предполагается, что отправитель — оператор
                content=content,
                attachment=attachment  # Если attachment None, поле останется пустым
            )

            user_request.status = RequestStatus.IN_PROGRESS
            user_request.timestamp = timezone.now()  # Обновляем время последнего действия
            if operator_id is not None:
                user_request.operator_id = operator_id
            user_request.save()

            send_data = {
                "request_id": user_request.id,
                "message": content,
                "sender": "operator",
                "chat_id": chat_id
            }

            # Подготовка файловых данных, если есть вложение
            files = {}
            if attachment:
                file_content = attachment.read()  # Читаем содержимое файла
                files['attachment'] = (attachment.name, file_content, attachment.content_type)

            # Отправляем всегда как multipart/form-data
            try:
                response = requests.post(
                    "https://thb24.name/bot/send_user/",
                    data=send_data,
                    files=files if files else None
                )
                response.raise_for_status()  # Проверяем статус ответа
            except requests.RequestException as e:
                logging.error("Ошибка отправки сообщения в Telegram: %s", e)
                return redirect("crm:request_detail", request_id=user_request.id)

            return redirect("crm:request_detail", request_id=user_request.id)

    return render(request, "request_detail.html", {"request": user_request, "messages": messages})


@async_only_middleware
async def close_request(request, request_id):
    """
    Закрытие заявки (установка статуса CANCELED или COMPLETED).
    """
    # Проверка авторизации
    # Проверка авторизации
    # Проверка авторизации
    is_authenticated = await sync_to_async(lambda: request.user.is_authenticated)()
    if not is_authenticated:
        # Перенаправление для неавторизованных пользователей
        return await sync_to_async(HttpResponseRedirect)("/login/")

        # Асинхронное получение объекта
    user_request = await manager_a.get_request_by_id(request_id)

    # 3. Получаем user_id (оператор), который пытается закрыть заявку
    user_id = user_request.operator_id


    amount_send = await manager_a.get_amount_send(request_id=request_id)

    if amount_send is not None:
        # Проверяем, принадлежит ли заявка этому оператору
        assigned_operator = await assigned_manager.get_operator_for_request(request_id)
        if assigned_operator != user_id:
            # Аналог "u_can_not"
            # В контексте Django вместо answer_callback_query можно
            # вернуть уведомление, отрендерить страницу ошибки или сделать редирект:
            # например:
            return await sync_to_async(HttpResponseRedirect)("/crm/error_no_access/")

        # Удаляем заявку из закрепленных
        await assigned_manager.unassign_request(request_id)

        # Удаляем заявку из "активных"
        active_request = await manager.get_request_by_request_id(request_id)
        if active_request:
            # Здесь в `active_request` у нас может быть поле user_id
            # Удаляем это из менеджера активных
            await manager.remove_request(active_request.user_id)

        # Проверяем, существует ли заявка в базе данных через manager_a
        active_request_1 = await manager_a.get_request_by_id(request_id)
        if active_request_1:
            if active_request_1:
                # Проверяем статус заявки, чтобы не менять статус у завершенной или отмененной заявки
                if active_request_1.status in [RequestStatus.NEW, RequestStatus.IN_PROGRESS]:
                    # Меняем статус заявки на "COMPLETED"
                    await manager_a.update_status(request_id, RequestStatus.COMPLETED.value)

            # Обновляем "тоты" пользователя (например, баланс, счётчики и т. д.)
            await manager_users.update_user_totals(chat_id=user_id, amount=int(amount_send))
            await sync_to_async(messages.add_message)(
                request,
                messages.SUCCESS,
                "Заявка успешно завершена!"
            )

        # Отправка сообщения через бота
        await bot.send_message(user_request.chat_id, text_finish)

        return await sync_to_async(HttpResponseRedirect)("/crm/crm/requests/")

    else:
        return await sync_to_async(HttpResponseRedirect)(f"/crm/requests2/{request_id}/")



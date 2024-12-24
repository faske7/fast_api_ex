from fastapi import FastAPI, APIRouter, Depends, HTTPException, File, UploadFile, Form, Query
from exchange.models import Rates, ExchangeData, MessageCreateData
import uuid
from config import settings
import logging
from db_worker import RequestsManager, ActiveRequestsManager, UsersManager, MessagesManager
import os
from fastapi.responses import JSONResponse
from typing import Optional
import httpx
from pydantic import BaseModel
from bot_thb_24 import bot
import time




# Настройка логирования
logging.basicConfig(filename='app_API.log', filemode='w',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)


router = APIRouter(prefix='/bot', tags=['Bot'])

# Создаем менеджер заявок
manager_a = RequestsManager()
# Создаем менеджер заявок
manager = ActiveRequestsManager()
# Создаем менеджер users
manager_users = UsersManager()




@router.post("/send/")
async def send_message(data: ExchangeData):
    try:
        # Создаем новую заявку
        request_id = await manager_a.create_request(chat_id=data.tg_id, amount=data.amount_to, first_name=str(data.first_name))
        if data.currency_from != 'USDT':
            await manager_a.update_amount_come_rub(request_id=request_id, amount_come_rub=data.amount_from)
            await manager_a.update_amount_send(request_id=request_id, amount_send=data.amount_to)
            text_u = f"""
Номер заявки {request_id}
Сумма к получению {data.amount_to} Бат
Вы отправляете {data.amount_from} Рублей
        """
        else:
            await manager_a.update_amount_come(request_id=request_id, amount_come=data.amount_from)
            await manager_a.update_amount_send(request_id=request_id, amount_send=data.amount_to)
            text_u = f"""
Номер заявки {request_id}
Сумма к получению {data.amount_to} Бат
Вы отправляете {data.amount_from} USDT
                    """
        # Добавляем заявку в БД
        await manager.add_request(user_id=data.tg_id, request_id=request_id, entered_sum=data.amount_to)

        await bot.send_message(data.tg_id, text_u)
        return {"request_id": request_id}
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при создании заявки: {str(e)}")


@router.post("/send_user/")
async def send_message(
        request_id: int = Form(...),
        message: str = Form(...),
        sender: str = Form(...),
        chat_id: str = Form(...),
        attachment: Optional[UploadFile] = File(None),
):
    """
    Отправка сообщения и опционального файла пользователю в Telegram.
    """
    # Формируем текст сообщения
    full_message = f"{sender}:\n{message}"

    # URL для отправки сообщений через Telegram Bot API
    telegram_url = f"https://api.telegram.org/bot{settings.TG_TOKEN2}/sendMessage"

    # Параметры запроса для отправки текстового сообщения
    payload = {
        "chat_id": chat_id,
        "text": full_message
    }

    try:
        # Отправляем текстовое сообщение
        async with httpx.AsyncClient() as client:
            response = await client.post(telegram_url, json=payload)
            response_data = response.json()

        if not response_data.get("ok"):
            error_description = response_data.get("description", "Неизвестная ошибка")
            logger.error(f"Ошибка Telegram при отправке сообщения: {error_description}")
            raise HTTPException(status_code=500, detail=f"Ошибка Telegram: {error_description}")

        logger.info(f"Сообщение отправлено в Telegram: {full_message}")

        # Если есть вложение, отправляем его
        if attachment:
            # Определяем тип вложения
            content_type = attachment.content_type
            filename = attachment.filename

            # Генерируем уникальное имя файла
            unique_id = int(time.time())  # Используем текущий timestamp
            # Или используйте UUID: unique_id = uuid.uuid4().hex
            file_extension = os.path.splitext(filename)[-1]  # Получаем расширение файла
            new_filename = f"{unique_id}{file_extension}"  # Уникальное имя файла с сохранением расширения

            # Сохраняем файл во временную директорию
            temp_dir = "/tmp/telegram_attachments"
            os.makedirs(temp_dir, exist_ok=True)  # Создаем директорию, если её ещё нет
            file_path = os.path.join(temp_dir, new_filename)

            with open(file_path, "wb") as f:
                content = await attachment.read()
                f.write(content)

            # Выбираем соответствующий метод Telegram API в зависимости от типа файла
            if content_type.startswith("image/"):
                send_method = "sendPhoto"
            elif content_type in ["application/pdf", "application/msword",
                                  "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                send_method = "sendDocument"
            elif content_type.startswith("video/"):
                send_method = "sendVideo"
            else:
                # Для неподдерживаемых типов можно использовать sendDocument
                send_method = "sendDocument"

            # URL для отправки файла
            file_url = f"https://api.telegram.org/bot{settings.TG_TOKEN2}/{send_method}"

            with open(file_path, "rb") as file_to_send:
                files = {
                    "chat_id": (None, chat_id),
                    "caption": (None, f"{sender} прикрепил файл: {filename}") if send_method == "sendPhoto" else (
                    None, f"{sender} прикрепил документ: {filename}")
                }
                if send_method == "sendPhoto":
                    files["photo"] = (filename, file_to_send, content_type)
                else:
                    files["document"] = (filename, file_to_send, content_type)

                # Отправляем файл
                async with httpx.AsyncClient() as client:
                    file_response = await client.post(file_url, files=files)
                file_response_data = file_response.json()

                if not file_response_data.get("ok"):
                    error_description = file_response_data.get("description", "Неизвестная ошибка")
                    logger.error(f"Ошибка Telegram при отправке файла: {error_description}")
                    raise HTTPException(status_code=500,
                                        detail=f"Ошибка Telegram при отправке файла: {error_description}")

                logger.info(f"Файл отправлен в Telegram: {filename}")

            # Удаляем временный файл после отправки
            os.remove(file_path)

        return JSONResponse(status_code=200, content={"message": "Сообщение и файл отправлены успешно."})

    except HTTPException as http_exc:
        # Повторно поднимаем HTTPException для обработки FastAPI
        raise http_exc
    except Exception as e:
        # Логируем и возвращаем ошибку
        logger.error(f"Ошибка при отправке сообщения или файла: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при отправке сообщения или файла: {str(e)}")

@router.get("/userExists/")
async def check_user_exists(tg_id: int=Query(..., ge=0, example=12345)):
    """Проверяет наличие пользователя в БД."""
    try:
        user = await manager_users.get_user_by_chat_id(tg_id)
        if user:
            return JSONResponse(status_code=200, content={"exists": True})
        else:
            return JSONResponse(status_code=200, content={"exists": False})
    except Exception as e:
        logging.error(f"Ошибка при проверке пользователя {tg_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при проверке пользователя.")


class StoreUserRequest(BaseModel):
    tg_id: int
    phone_number: int
    first_name: Optional[str] = None

@router.post("/storeUser/")
async def store_user(data: StoreUserRequest):
    """Сохраняет нового пользователя в БД."""
    logging.info("1111")
    try:
        tg_id = data.tg_id
        phone_number = data.phone_number
        first_name = data.first_name
        if not tg_id or not phone_number:
            raise HTTPException(status_code=400, detail="tg_id и phone_number обязательны.")

        await manager_users.add_or_update_user(
            chat_id=tg_id,
            username=None,
            first_name=first_name,
            last_name=None,
            total_amount=0,
            referrer_id=None,
            phone=int(phone_number)
        )
        return JSONResponse(status_code=200, content={"status": "success"})
    except Exception as e:
        logging.error(f"Ошибка при сохранении пользователя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при сохранении пользователя.")
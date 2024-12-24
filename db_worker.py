from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import asyncpg
from exchange.models import *
from config import settings, correction_factors2, correction_factors_night
import asyncio
from core.update_rates import get_list  # Импорт функции get_list
from core.engine import save_correction_factors, save_correction_factors_night
from sqlalchemy.future import select
import pytz
import logging
from sqlalchemy import func


DATABASE_URL=f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}/{settings.DB_NAME}"
# Создание асинхронного движка для работы с PostgreSQL
engine = create_async_engine(DATABASE_URL, echo=True)
# Создание сессии
async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)



class MessagesManager:
    """Менеджер для работы с сообщениями."""

    async def create_message(self, request_id: int, sender: str, content: str, attachment: str = None) -> int:
        """Создает новое сообщение и возвращает его ID."""
        new_message = Message(
            request_id=request_id,
            sender=sender,
            content=content,
            attachment=attachment,
            created_at=datetime.now(pytz.timezone('Asia/Bangkok')).replace(tzinfo=None)
        )
        async with async_session() as session:
            session.add(new_message)
            await session.commit()
            await session.refresh(new_message)
            return new_message.id



    async def get_messages_by_request_id(self, request_id: int) -> List[Message]:
        """Получает все сообщения для заданного request_id, отсортированные по времени."""
        async with async_session() as session:
            result = await session.execute(
                select(Message).filter_by(request_id=request_id).order_by(Message.created_at.asc())
            )
            return result.scalars().all()

    async def get_message_by_id(self, message_id: int) -> Optional[Message]:
        """Получает сообщение по его ID."""
        async with async_session() as session:
            result = await session.execute(select(Message).filter_by(id=message_id))
            return result.scalar_one_or_none()

    async def delete_message(self, message_id: int) -> None:
        """Удаляет сообщение по его ID."""
        async with async_session() as session:
            result = await session.execute(select(Message).filter_by(id=message_id))
            message = result.scalar_one_or_none()
            if message:
                await session.delete(message)
                await session.commit()

    async def update_message_content(self, message_id: int, content: str) -> None:
        """Обновляет содержимое сообщения."""
        async with async_session() as session:
            result = await session.execute(select(Message).filter_by(id=message_id))
            message = result.scalar_one_or_none()
            if message:
                message.content = content
                await session.commit()

    async def update_message_att(self, request_id: int, attachment: str) -> None:
        """Обновляет содержимое сообщения."""
        async with async_session() as session:
            result = await session.execute(select(Message).filter_by(request_id=request_id))
            message = result.scalar_one_or_none()
            if message:
                message.attachment = attachment
                await session.commit()

class UsersManager:
    """Менеджер для работы с пользователями."""

    async def get_user_by_chat_id(self, chat_id: int) -> Optional['Users']:
        """Получает пользователя по chat_id."""
        async with async_session() as session:
            result = await session.execute(select(Users).filter_by(chat_id=chat_id))
            return result.scalar_one_or_none()

    async def add_or_update_user(
            self, chat_id: int, username: Optional[str], first_name: Optional[str], phone: Optional[int], last_name: Optional[str], total_amount: Optional[int], referrer_id: Optional[int]
    ) -> None:
        # Предотвращаем самореферал
        if referrer_id == chat_id:
            referrer_id = None
        """Добавляет нового пользователя или обновляет существующего."""
        async with async_session() as session:
            user = await self.get_user_by_chat_id(chat_id)
            current_time = datetime.utcnow()

            if user:
                # Обновление существующего пользователя
                user.username = username
                user.first_name = first_name
                user.last_name = last_name
                user.total_amount = total_amount
                user.referrer_id = referrer_id
                user.phone = phone
            else:
                # Создание нового пользователя
                user = Users(
                    chat_id=chat_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    registration_date=current_time,
                    total_amount=0,
                    total_req=0,
                    referrer_id=referrer_id,
                    bonus=0,
                    phone=phone,
                )
                session.add(user)

            await session.commit()

    async def update_user_totals(self, chat_id: int, amount: int) -> None:
        """Обновляет общую сумму и количество заказов пользователя."""
        async with async_session() as session:
            try:
                result = await session.execute(select(Users).filter_by(chat_id=chat_id))
                user = result.scalar_one_or_none()
                if user:
                    user.total_req += 1
                    user.total_amount += amount
                    await session.commit()


                # Начисляем бонус рефереру, если он существует
                    if user.referrer_id:
                        await self.reward_referrer(user.referrer_id, amount)
            except Exception as e:
                logging.error(str(e))

    async def get_referral_count(self, user_id: int) -> int:
        """Получает количество пользователей, приглашенных данным пользователем."""
        async with async_session() as session:
            result = await session.execute(
                select(func.count()).select_from(Users).filter_by(referrer_id=user_id)
            )
            count = result.scalar()
            return count if count is not None else 0

    async def reward_referrer(self, referrer_id: int, amount: int) -> None:
        """Начисляет бонус рефереру."""
        async with async_session() as session:
            result = await session.execute(select(Users).filter_by(chat_id=referrer_id))
            referrer = result.scalar_one_or_none()
            if referrer:
                # бонус — это определенный процент от суммы
                bonus_percentage = 0.003  # 0.3% бонус
                bonus_amount = amount * bonus_percentage
                referrer.bonus += bonus_amount
                await session.commit()

    async def get_operator_user_ids(self) -> List[int]:
        """Получает список ID операторов."""
        async with async_session() as session:
            result = await session.execute(select(Operator.user_chat_id))
            operator_ids = result.scalars().all()
            return operator_ids

class RequestsManager:
    """Менеджер для работы с заявками."""

    async def create_request(self, chat_id: int, amount: int, first_name: str) -> int:
        """Создает новую заявку и возвращает её ID."""
        new_request = Request(
            chat_id=chat_id,
            amount=int(amount),
            timestamp=datetime.now(pytz.timezone('Asia/Bangkok')).replace(tzinfo=None),
            first_name=first_name
        )
        async with async_session() as session:
            session.add(new_request)
            await session.commit()
            await session.refresh(new_request)
            return new_request.id

    async def get_request_by_id(self, request_id: int) -> Optional[Request]:
        """Получает заявку по её ID."""
        async with async_session() as session:
            result = await session.execute(select(Request).filter_by(id=request_id))
            return result.scalar_one_or_none()

    async def update_request(self, request_id: int, chat_id: Optional[int] = None, amount: Optional[int] = None) -> None:
        """Обновляет данные существующей заявки."""
        async with async_session() as session:
            result = await session.execute(select(Request).filter_by(id=request_id))
            request = result.scalar_one_or_none()
            if request:
                if chat_id is not None:
                    request.chat_id = chat_id
                if amount is not None:
                    request.amount = amount
                request.timestamp = datetime.now(pytz.timezone('Asia/Bangkok')).replace(tzinfo=None)
                await session.commit()

    async def delete_request(self, request_id: int) -> None:
        """Удаляет заявку по её ID."""
        async with async_session() as session:
            result = await session.execute(select(Request).filter_by(id=request_id))
            request = result.scalar_one_or_none()
            if request:
                await session.delete(request)
                await session.commit()

    async def get_requests_by_chat_id(self, chat_id: int) -> List[Request]:
        """Получает все заявки для заданного chat_id."""
        async with async_session() as session:
            result = await session.execute(select(Request).filter_by(chat_id=chat_id))
            return result.scalars().all()

    async def update_status(self, request_id: int, status: str) -> None:
        """Обновляет статус заявки."""
        async with async_session() as session:
            result = await session.execute(select(Request).filter_by(id=request_id))
            request = result.scalar_one_or_none()
            if request:
                request.status = RequestStatus(status)  # Преобразуем строку в Enum
                await session.commit()

    async def update_amount_send(self, request_id: int, amount_send: int) -> None:
        """Обновляет сумму отправленных средств."""
        async with async_session() as session:
            result = await session.execute(select(Request).filter_by(id=request_id))
            request = result.scalar_one_or_none()
            if request:
                request.amount_send = amount_send
                await session.commit()

    async def update_amount_come(self, request_id: int, amount_come: int) -> None:
        """Обновляет сумму полученных средств."""
        async with async_session() as session:
            result = await session.execute(select(Request).filter_by(id=request_id))
            request = result.scalar_one_or_none()
            if request:
                request.amount_come = amount_come
                await session.commit()

    async def update_amount_come_rub(self, request_id: int, amount_come_rub: int) -> None:
        """Обновляет сумму полученных средств."""
        async with async_session() as session:
            result = await session.execute(select(Request).filter_by(id=request_id))
            request = result.scalar_one_or_none()
            if request:
                request.amount_come_rub = amount_come_rub
                await session.commit()

    async def get_amount_send(self, request_id: int):
        """Возвращает сумму отправленных средств по request_id."""
        async with async_session() as session:
            result = await session.execute(select(Request).filter_by(id=request_id))
            request = result.scalar_one_or_none()
            if request:
                return request.amount_send
            return None

    async def update_operator_id(self, request_id: int, operator_id: int) -> None:
        """Обновляет oper id ."""
        async with async_session() as session:
            result = await session.execute(select(Request).filter_by(id=request_id))
            request = result.scalar_one_or_none()
            if request:
                request.operator_id = operator_id
                await session.commit()
# --- CLASS: RequestPhotoManager ---
class RequestPhotoManager:
    """Менеджер для работы с фотографиями заявок."""

    async def save_photo(self, request_id: int, chat_id: int, image_data: bytes) -> None:
        """Сохраняет фотографию в базу данных."""
        async with async_session() as session:
            # Получаем заявку
            result = await session.execute(select(Request).filter_by(id=request_id))
            request_obj = result.scalar_one_or_none()
            if request_obj:
                # Создаем объект RequestPhoto
                photo_instance = RequestPhoto(
                    request_id=request_id,
                    chat_id=chat_id,
                    image_data=image_data,
                    uploaded_at=datetime.now(pytz.timezone('Asia/Bangkok')).replace(tzinfo=None)
                )
                session.add(photo_instance)
                await session.commit()
            else:
                # Если заявка не найдена, можно выбросить исключение или обработать ошибку
                raise ValueError(f"Заявка с ID {request_id} не найдена.")
# --- CLASS: AssignedRequestsManager ---
class AssignedRequestsManager:
    """Менеджер для работы с закрепленными заявками."""

    async def assign_request(self, operator_id: int, request_id: int, first_name: str) -> None:
        """Закрепляет заявку за оператором."""
        current_time = datetime.now(pytz.timezone('Asia/Bangkok')).replace(tzinfo=None)
        async with async_session() as session:
            assigned_request = AssignedRequest(
                operator_id=int(operator_id),
                request_id=int(request_id),
                assigned_at=current_time,
                first_name=first_name)
            session.add(assigned_request)
            await session.commit()

    async def get_requests_for_operator(self, operator_id: int) -> List[AssignedRequest]:
        """Получает все заявки, закрепленные за оператором."""
        async with async_session() as session:
            result = await session.execute(select(AssignedRequest).filter_by(operator_id=operator_id))
            return result.scalars().all()

    async def get_operator_for_request(self, request_id: int) -> Optional[int]:
        """Получает ID оператора, которому закреплена заявка."""
        async with async_session() as session:
            result = await session.execute(select(AssignedRequest).filter_by(request_id=request_id))
            assigned_request = result.scalar_one_or_none()
            return assigned_request.operator_id if assigned_request else None

    async def unassign_request(self, request_id: int) -> None:
        """Снимает закрепление заявки."""
        async with async_session() as session:
            result = await session.execute(select(AssignedRequest).filter_by(request_id=request_id))
            assigned_request = result.scalar_one_or_none()
            if assigned_request:
                await session.delete(assigned_request)
                await session.commit()
# --- CLASS: ActiveRequestsManager ---
class ActiveRequestsManager:
    """Менеджер для работы с активными заявками."""

    async def get_request_by_request_id(self, request_id: int) -> Optional[ActiveRequest]:
        """Получает активную заявку по request_id."""
        async with async_session() as session:
            result = await session.execute(select(ActiveRequest).filter_by(request_id=request_id))
            return result.scalar_one_or_none()

    async def get_user_chat_id_by_request_id(self, request_id: int) -> Optional[int]:
        """Получает user_id по request_id."""
        async with async_session() as session:
            result = await session.execute(select(ActiveRequest).filter_by(request_id=request_id))
            request = result.scalar_one_or_none()
            return request.user_id if request else None

    async def add_request(self, user_id: int, request_id: int, entered_sum: int) -> None:
        """Добавляет новую заявку в БД или обновляет существующую."""
        async with async_session() as session:
            result = await session.execute(select(ActiveRequest).filter_by(user_id=user_id))
            request = result.scalar_one_or_none()
            current_time = datetime.now(pytz.timezone('Asia/Bangkok')).replace(tzinfo=None)
            if request:
                request.request_id = request_id
                request.entered_sum = entered_sum
                request.timestamp = current_time
            else:
                request = ActiveRequest(
                    user_id=int(user_id),
                    request_id=int(request_id),
                    entered_sum=int(entered_sum),
                    timestamp=current_time,
                )
                session.add(request)
            await session.commit()

    async def get_request(self, user_id: int) -> Optional[ActiveRequest]:
        """Получает заявку по user_id."""
        async with async_session() as session:
            result = await session.execute(select(ActiveRequest).filter_by(user_id=user_id))
            return result.scalar_one_or_none()

    async def remove_request(self, user_id: int) -> None:
        """Удаляет заявку по user_id."""
        async with async_session() as session:
            result = await session.execute(select(ActiveRequest).filter_by(user_id=user_id))
            request = result.scalar_one_or_none()
            if request:
                await session.delete(request)
                await session.commit()
# менеджер для работы с моделью Wallet
class WalletManager:
    """Менеджер для работы с кошельками."""

    async def get_wallet(self) -> Optional[Wallet]:
        """Получает объект Wallet по user_id."""
        async with async_session() as session:
            result = await session.execute(select(Wallet).filter_by(user_id=1))
            wallet = result.scalar_one_or_none()
            return wallet
# Функция для инициализации базы данных
async def init_db():
    # Создаем все таблицы, если их нет
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
# Функция для создания базы данных
async def create_database():
    try:
        conn = await asyncpg.connect(user=settings.DB_USER, password=settings.DB_PASSWORD, database=settings.DB_TYPE, host=settings.DB_HOST)
        # Проверка, существует ли база данных
        result = await conn.fetchval(f"SELECT 1 FROM pg_database WHERE datname='{settings.DB_NAME}'")
        if not result:
            # Если база данных не существует, создаем её
            await conn.execute(f'CREATE DATABASE "{settings.DB_NAME}"')
            print(f"Database '{settings.DB_NAME}' created.")
        await conn.close()
    except Exception as e:
        print(f"Error while creating database: {e}")
# Зависимость для сессии
async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
# Функция для обновления курсов в базе данных
async def update_rates():
    # Получаем новые курсы из функции get_list
    new_rates = await get_list()

    # Открываем сессию для работы с базой данных
    async for session in get_db():
        # Проверяем, есть ли уже записи в таблице Rates
        result = await session.execute(select(Rates))
        existing_rate = result.scalars().first()

        if existing_rate:
            # Обновляем существующую запись
            existing_rate.rub_tra = new_rates.rub_tra
            existing_rate.rub_cash = new_rates.rub_cash
            existing_rate.usd_100 = new_rates.usd_100
            existing_rate.usd_50 = new_rates.usd_50
            existing_rate.eur_thb = new_rates.eur_thb
            existing_rate.gbp_thb = new_rates.gbp_thb
            existing_rate.aed_thb = new_rates.aed_thb
            existing_rate.rub_tra_sell = new_rates.rub_tra_sell
            existing_rate.rub_cash_sell = new_rates.rub_cash_sell
            existing_rate.usd_100_sell = new_rates.usd_100_sell
            existing_rate.usd_50_sell = new_rates.usd_50_sell
            existing_rate.eur_thb_sell = new_rates.eur_thb_sell
            existing_rate.gbp_thb_sell = new_rates.gbp_thb_sell
            existing_rate.aed_thb_sell = new_rates.aed_thb_sell
            existing_rate.usdt_bot = new_rates.usdt_bot
            existing_rate.usdt_bot_sell = new_rates.usdt_bot_sell

            # Обновляем новые поля
            existing_rate.kwd_thb = new_rates.kwd_thb
            existing_rate.bhd_thb = new_rates.bhd_thb
            existing_rate.bnd_thb = new_rates.bnd_thb
            existing_rate.twd_thb = new_rates.twd_thb
            existing_rate.qar_thb = new_rates.qar_thb
            existing_rate.omr_thb = new_rates.omr_thb
            existing_rate.jpy_thb = new_rates.jpy_thb
            existing_rate.zar_thb = new_rates.zar_thb
            existing_rate.idr_thb = new_rates.idr_thb
            existing_rate.chf_thb = new_rates.chf_thb
            existing_rate.php_thb = new_rates.php_thb
            existing_rate.cny_thb = new_rates.cny_thb
            existing_rate.krw_thb = new_rates.krw_thb
            existing_rate.sgd_thb = new_rates.sgd_thb
            existing_rate.myr_thb = new_rates.myr_thb
            existing_rate.hkd_thb = new_rates.hkd_thb
            existing_rate.aud_thb = new_rates.aud_thb
            existing_rate.inr_thb = new_rates.inr_thb
            existing_rate.sar_thb = new_rates.sar_thb
            existing_rate.cad_thb = new_rates.cad_thb
            existing_rate.nzd_thb = new_rates.nzd_thb
            existing_rate.kzt_thb = new_rates.kzt_thb

            # Обновляем новые sell поля
            existing_rate.kwd_thb_sell = new_rates.kwd_thb_sell
            existing_rate.bhd_thb_sell = new_rates.bhd_thb_sell
            existing_rate.bnd_thb_sell = new_rates.bnd_thb_sell
            existing_rate.twd_thb_sell = new_rates.twd_thb_sell
            existing_rate.qar_thb_sell = new_rates.qar_thb_sell
            existing_rate.omr_thb_sell = new_rates.omr_thb_sell
            existing_rate.jpy_thb_sell = new_rates.jpy_thb_sell
            existing_rate.zar_thb_sell = new_rates.zar_thb_sell
            existing_rate.idr_thb_sell = new_rates.idr_thb_sell
            existing_rate.chf_thb_sell = new_rates.chf_thb_sell
            existing_rate.php_thb_sell = new_rates.php_thb_sell
            existing_rate.cny_thb_sell = new_rates.cny_thb_sell
            existing_rate.krw_thb_sell = new_rates.krw_thb_sell
            existing_rate.sgd_thb_sell = new_rates.sgd_thb_sell
            existing_rate.myr_thb_sell = new_rates.myr_thb_sell
            existing_rate.hkd_thb_sell = new_rates.hkd_thb_sell
            existing_rate.aud_thb_sell = new_rates.aud_thb_sell
            existing_rate.inr_thb_sell = new_rates.inr_thb_sell
            existing_rate.sar_thb_sell = new_rates.sar_thb_sell
            existing_rate.cad_thb_sell = new_rates.cad_thb_sell
            existing_rate.nzd_thb_sell = new_rates.nzd_thb_sell
            existing_rate.kzt_thb_sell = new_rates.kzt_thb_sell

        else:
            # Если записи нет, добавляем новую
            session.add(new_rates)

        # Сохраняем изменения
        await session.commit()
        break  # Завершаем итерацию после одного использования сессии
# Запускаем периодическое обновление каждые 30 минут
async def periodic_rate_update():
    while True:
        await update_rates()
        await asyncio.sleep(1800)  # 30 минут
# Главная функция для запуска инициализации базы данных
async def main():
    # Сначала проверяем и создаём базу данных при необходимости
    await create_database()
    # Далее создаём таблицы
    await init_db()

    await save_correction_factors(correction_factors2)
    await save_correction_factors_night(correction_factors_night)

    await periodic_rate_update()
# Запускаем событие
if __name__ == "__main__":
    asyncio.run(main())

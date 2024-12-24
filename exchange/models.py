from pydantic import BaseModel
from typing import Dict, Union, List, Optional
from sqlalchemy.orm import declarative_base
from sqlalchemy import Float, Column, Integer, String, BigInteger, DateTime, Enum, ForeignKey, LargeBinary, Text
from datetime import datetime
import enum
from sqlalchemy.orm import relationship

# SQLAlchemy базовый класс для моделей
Base = declarative_base()

class RateInfo(BaseModel):
    buy: Union[float, str]  # Может быть числом или строкой
    sell: Union[float, str]  # Может быть числом или строкой
    flag: str  # Путь к изображению флага
    bank_logos: Optional[List[str]] = None  # Список логотипов банков, опционально
    is_transfer: Optional[bool] = False  # Флаг для перевода, опционально

class LisExchangeResponse(BaseModel):
    rates: Dict[str, RateInfo]

# SQLAlchemy модель пользователя
class Rates(Base):
    __tablename__ = "rates"

    id = Column(Integer, primary_key=True)  # Указание первичного ключа
    aed_thb = Column(Float)
    gbp_thb = Column(Float)
    eur_thb = Column(Float)
    usd_100 = Column(Float)
    usd_50 = Column(Float)
    rub_cash = Column(Float)
    rub_tra = Column(Float)
    aed_thb_sell = Column(Float)
    gbp_thb_sell = Column(Float)
    eur_thb_sell = Column(Float)
    usd_100_sell = Column(Float)
    usd_50_sell = Column(Float)
    rub_cash_sell = Column(Float)
    rub_tra_sell = Column(Float)
    usdt_bot = Column(Float)
    usdt_bot_sell = Column(Float)

    kwd_thb = Column(Float)
    bhd_thb = Column(Float)
    bnd_thb = Column(Float)
    twd_thb = Column(Float)
    qar_thb = Column(Float)
    omr_thb = Column(Float)
    jpy_thb = Column(Float)
    zar_thb = Column(Float)
    idr_thb = Column(Float)
    chf_thb = Column(Float)
    php_thb = Column(Float)
    cny_thb = Column(Float)
    krw_thb = Column(Float)
    sgd_thb = Column(Float)
    myr_thb = Column(Float)
    hkd_thb = Column(Float)
    aud_thb = Column(Float)
    inr_thb = Column(Float)
    sar_thb = Column(Float)
    cad_thb = Column(Float)
    nzd_thb = Column(Float)
    kzt_thb = Column(Float)

    kwd_thb_sell = Column(Float)
    bhd_thb_sell = Column(Float)
    bnd_thb_sell = Column(Float)
    twd_thb_sell = Column(Float)
    qar_thb_sell = Column(Float)
    omr_thb_sell = Column(Float)
    jpy_thb_sell = Column(Float)
    zar_thb_sell = Column(Float)
    idr_thb_sell = Column(Float)
    chf_thb_sell = Column(Float)
    php_thb_sell = Column(Float)
    cny_thb_sell = Column(Float)
    krw_thb_sell = Column(Float)
    sgd_thb_sell = Column(Float)
    myr_thb_sell = Column(Float)
    hkd_thb_sell = Column(Float)
    aud_thb_sell = Column(Float)
    inr_thb_sell = Column(Float)
    sar_thb_sell = Column(Float)
    cad_thb_sell = Column(Float)
    nzd_thb_sell = Column(Float)
    kzt_thb_sell = Column(Float)

# Определяем модель таблицы
class CorrectionFactor(Base):
    __tablename__ = "correction_factors"

    factor_key = Column(String, primary_key=True, index=True)
    buy_factor = Column(Float, nullable=False)
    sell_factor = Column(Float, nullable=False)

# Определяем Enum для состояния заявки
class RequestStatus(enum.Enum):
    NEW = "новая"
    IN_PROGRESS = "в процессе"
    COMPLETED = "завершена"
    CANCELED = "отменена"

class RequestPhoto(Base):
    __tablename__ = 'request_photos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(Integer, ForeignKey('requests.id'), nullable=False)
    chat_id = Column(BigInteger, ForeignKey('users.chat_id'), nullable=False)
    image_data = Column(LargeBinary, nullable=False)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    request = relationship(
        'Request',
        back_populates='photos',
        foreign_keys=[request_id]
    )
    user = relationship(
        'Users',
        back_populates='photos',
        foreign_keys=[chat_id]
    )

# Модель заявки
class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, autoincrement=True)  # Автоинкрементирующий номер
    chat_id = Column(BigInteger, nullable=False)               # ID чата пользователя
    operator_id = Column(BigInteger, nullable=True)  # ID чата operatora
    amount = Column(Integer, nullable=False)                   # Сумма
    amount_send = Column(Integer, nullable=True)               # Сумма отправленных
    amount_come = Column(Integer, nullable=True)               # Сумма полученных
    amount_come_rub = Column(Integer, nullable=True)           # Сумма полученных рублей
    first_name = Column(String, nullable=True)                 # Имя пользователя
    timestamp = Column(DateTime, nullable=False)               # Время создания заявки
    status = Column(Enum(RequestStatus), nullable=False, default=RequestStatus.NEW)  # Состояние заявки
    # Добавляем связь с фотографиями
    photos = relationship('RequestPhoto', back_populates='request', cascade='all, delete-orphan')
    # Связь с Message
    messages = relationship("Message", back_populates="request")


class AssignedRequest(Base):
    __tablename__ = 'assigned_requests'

    id = Column(Integer, primary_key=True, autoincrement=True)
    operator_id = Column(BigInteger, nullable=False, index=True)  # ID оператора
    request_id = Column(Integer, nullable=False, unique=True)  # ID заявки
    assigned_at = Column(DateTime, nullable=False)  # Время назначения
    first_name = Column(String, nullable=False)  # Имя пользователя



# Определяем модель ActiveRequest
class ActiveRequest(Base):
    __tablename__ = 'active_requests'

    user_id = Column(BigInteger, primary_key=True, index=True)
    request_id = Column(Integer, nullable=False)
    entered_sum = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False)


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True) # Автоинкрементирующий ID пользователя
    chat_id = Column(BigInteger, nullable=False, unique=True)  # Уникальный ID чата пользователя
    username = Column(String, nullable=True)                   # Имя пользователя (если доступно)
    first_name = Column(String, nullable=True)                 # Имя пользователя
    last_name = Column(String, nullable=True)                  # Фамилия пользователя
    registration_date = Column(DateTime, nullable=False)       # Дата регистрации
    total_amount = Column(Integer, nullable=False)             # Общая Сумма
    total_req = Column(Integer, nullable=False)                # Кол-во заказов
    referrer_id = Column(BigInteger, nullable=True)            # Ref ID
    bonus = Column(Float, nullable=True)                       # Bonus
    phone = Column(BigInteger, nullable=True, unique=True)     # phone

    # Указываем, что отношение 'operator_profile' использует внешний ключ 'user_id'
    operator_profile = relationship(
        "Operator",
        back_populates="user",
        foreign_keys="Operator.user_id"
    )

    # Relationship to RequestPhoto
    photos = relationship(
        'RequestPhoto',
        back_populates='user',
        cascade='all, delete-orphan'
    )

# Определяем модель Wallet
class Wallet(Base):
    __tablename__ = 'wallet'

    user_id = Column(BigInteger, primary_key=True, index=True)
    wallet = Column(String, nullable=False)

class Operator(Base):
    __tablename__ = "operators"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    user_chat_id = Column(BigInteger, ForeignKey("users.chat_id"))
    # Добавьте дополнительные поля, если необходимо
    # Например:
    role = Column(String, nullable=True)

    # Явно указываем, что связь 'user' использует внешний ключ 'user_id'
    user = relationship(
        "Users",
        back_populates="operator_profile",
        foreign_keys=[user_id]
    )

    def __repr__(self):
        return f"<Operator(user_id={self.user_id})>"

class ExchangeData(BaseModel):
    amount_from: float
    amount_to: float
    currency_from: str
    currency_to: str
    first_name: str
    tg_id: int

class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(Integer, ForeignKey('requests.id'), nullable=False)  # Связь с таблицей Requests
    sender = Column(String(50), nullable=False)  # Отправитель ("operator" или "user")
    content = Column(Text, nullable=False)  # Содержимое сообщения
    attachment = Column(String, nullable=True)  # Сохраняет путь к файлу
    created_at = Column(DateTime, default=datetime.utcnow)  # Время создания

    # Связь с Requests
    request = relationship("Request", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, request_id={self.request_id}, sender='{self.sender}')>"

class MessageCreateData(BaseModel):
    request_id: int
    message: str
    sender: str
    chat_id: int

# Определяем модель таблицы
class CorrectionFactor2(Base):
    __tablename__ = "correction_factors_night"

    factor_key = Column(String, primary_key=True, index=True)
    buy_factor = Column(Float, nullable=False)
    sell_factor = Column(Float, nullable=False)
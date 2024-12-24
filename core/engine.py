from exchange.models import CorrectionFactor, CorrectionFactor2
from sqlalchemy.future import select
import pytz
from datetime import datetime


async def load_correction_factors():
    """
    Загрузить все коэффициенты из базы данных.
    """
    from db_worker import get_db
    async for session in get_db():
        result = await session.execute(select(CorrectionFactor))
        factors = result.scalars().all()
        return {factor.factor_key: [factor.buy_factor, factor.sell_factor] for factor in factors}

async def load_correction_factors_2():
    """
    Загрузить все коэффициенты из базы данных.
    """
    from db_worker import get_db
    async for session in get_db():
        result = await session.execute(select(CorrectionFactor2))
        factors = result.scalars().all()
        return {factor.factor_key: [factor.buy_factor, factor.sell_factor] for factor in factors}

async def save_correction_factors(correction_factors):
    """
    Сохранить коэффициенты в базу данных.
    """
    from db_worker import get_db
    async for session in get_db():
        async with session.begin():  # Контекстный менеджер для транзакции
            for key, (buy_factor, sell_factor) in correction_factors.items():
                # Проверяем, существует ли запись
                result = await session.execute(
                    select(CorrectionFactor).filter_by(factor_key=key)
                )
                db_factor = result.scalars().first()
                if db_factor:
                    # Обновляем существующую запись
                    db_factor.buy_factor = buy_factor
                    db_factor.sell_factor = sell_factor
                else:
                    # Если записи нет, создаем новую
                    new_factor = CorrectionFactor(
                        factor_key=key,
                        buy_factor=buy_factor,
                        sell_factor=sell_factor
                    )
                    session.add(new_factor)
            # Изменения фиксируются автоматически при выходе из async with

async def save_correction_factors_night(correction_factors):
    """
    Сохранить коэффициенты в базу данных.
    """
    from db_worker import get_db
    async for session in get_db():
        async with session.begin():  # Контекстный менеджер для транзакции
            for key, (buy_factor, sell_factor) in correction_factors.items():
                # Проверяем, существует ли запись
                result = await session.execute(
                    select(CorrectionFactor2).filter_by(factor_key=key)
                )
                db_factor = result.scalars().first()
                if db_factor:
                    # Обновляем существующую запись
                    db_factor.buy_factor = buy_factor
                    db_factor.sell_factor = sell_factor
                else:
                    # Если записи нет, создаем новую
                    new_factor = CorrectionFactor2(
                        factor_key=key,
                        buy_factor=buy_factor,
                        sell_factor=sell_factor
                    )
                    session.add(new_factor)
            # Изменения фиксируются автоматически при выходе из async with

# Определяем функцию для генерации времени суток
async def get_greeting():
    tz = pytz.timezone('Asia/Bangkok')  # Задаем таймзону
    current_hour = datetime.now(tz).hour
    if 5 <= current_hour < 12:
        return "Доброе утро!"
    elif 12 <= current_hour < 18:
        return "Добрый день!"
    else:
        return "Добрый вечер!"
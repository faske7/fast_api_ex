import aiohttp
from config import settings
import logging

logging.basicConfig(level=logging.INFO)


async def get_usdt_to_rub_and_thb():
    # Получение курса USDT к RUB
    url_rub = "https://garantex.org/rates"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url_rub, timeout=3000) as response:
                response.raise_for_status()  # Проверяет наличие HTTP ошибок
                data = await response.json()
                usdt_to_rub = data.get("usdtrub", {}).get("sell")
                if usdt_to_rub is not None:
                    return float(usdt_to_rub)
                else:
                    logging.error("Не удалось получить курс USDT к RUB")
                    return None
        except aiohttp.ClientError as e:
            logging.error("Ошибка при запросе к Garantex: %s", e)
            return None


async def get_usdt_rate(target_currency, source_currency="USD"):
    """
    Получение курса USDT к указанной валюте.
    :param target_currency: Целевая валюта (например, THB).
    :param source_currency: Исходная валюта (по умолчанию USD).
    :return: Курс или None, если произошла ошибка.
    """
    url = (
        f"https://apilayer.net/api/live?"
        f"access_key={settings.API_KEY_RATE}&"
        f"currencies={target_currency}&"
        f"source={source_currency}&format=1"
    )

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=30) as response:
                response.raise_for_status()
                data = await response.json()
                if data.get("success"):
                    rate_key = f"{source_currency}{target_currency}"
                    rate = data.get("quotes", {}).get(rate_key)
                    if rate is not None:
                        logging.info("Курс %s к %s успешно получен: %s", source_currency, target_currency, rate)
                        return float(rate)
                    else:
                        logging.error("Курс %s к %s отсутствует в ответе API: %s", source_currency, target_currency,
                                      data)
                        return None
                else:
                    logging.error("Ошибка в ответе API: %s", data)
                    return None
        except aiohttp.ClientTimeout:
            logging.error("Превышено время ожидания при запросе к API для %s -> %s", source_currency, target_currency)
            return None
        except aiohttp.ClientError as e:
            logging.error("Ошибка при запросе к API: %s", e)
            return None
        except Exception as e:
            logging.error("Неизвестная ошибка: %s", e)
            return None


async def get_rub_and_thb():
    """Получить курс USDT к рублю."""
    headers = {
        "Referer": "http://localhost"  # Указать допустимый реферер
    }
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(settings.API_RATES) as response:
                response.raise_for_status()  # Проверить наличие HTTP ошибок
                data = await response.json()

                # Извлечь курс рубля
                if 'rates' in data and 'RUB (online)' in data['rates']:
                    ruble_rate = data['rates']['RUB (online)']['buy']
                    return ruble_rate
                else:
                    return None  # Вернуть None, если курс рубля не найден
    except aiohttp.ClientError as e:
        logging.error(f"Error fetching RUB data: {e}")
        return None


async def get_usdt_to_thb():
    """Получить курс USDT к тайскому бату."""
    headers = {
        "Referer": "http://localhost"  # Указать допустимый реферер
    }
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(settings.API_RATES) as response:
                response.raise_for_status()  # Проверить наличие HTTP ошибок
                data = await response.json()

                # Извлечь курс  бата
                if 'rates' in data and 'USDT' in data['rates']:
                    thb_rate = data['rates']['USDT']['buy']
                    return thb_rate
                else:
                    return None  # Вернуть None, если курс  бата не найден
    except aiohttp.ClientError as e:
        logging.error(f"Error fetching THB data: {e}")
        return None

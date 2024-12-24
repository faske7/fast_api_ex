from .models import LisExchangeResponse
from fastapi import FastAPI, APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from exchange.models import Rates, ExchangeData
from db_worker import get_db
from sqlalchemy import select
import uuid
import requests
from config import settings
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter(prefix='/rates', tags=['Rates'])

# Получение курсов
@router.get("/", response_model=LisExchangeResponse)
async def get_list(db: AsyncSession = Depends(get_db)):
    # Запрос данных из таблицы Rates
    result = await db.execute(select(Rates))
    rates_data = result.scalars().first()

    # Проверка на наличие данных
    if not rates_data:
        return LisExchangeResponse(rates={})

    # Формирование словаря с результатами из данных БД
    rates = {
        "RUB (online)": {
            "buy": rates_data.rub_tra,
            "sell": rates_data.rub_tra_sell if rates_data.rub_tra_sell is not None else "-",
            "flag": "./flags/1x1/ru.svg",
            "bank_logos": ["./images/sberbank-logo.png", "./images/tinkoff-logo.png"],
            "is_transfer": True
        },
        "RUB (cash)": {
            "buy": rates_data.rub_cash,
            "sell": rates_data.rub_cash_sell if rates_data.rub_cash_sell is not None else "-",
            "flag": "./flags/1x1/ru.svg",
            "is_transfer": False
        },
        "USD 100-50": {
            "buy": rates_data.usd_100,
            "sell": rates_data.usd_100_sell,
            "flag": "./flags/1x1/us.svg",
            "is_transfer": False
        },
        "USD 1-20": {
            "buy": rates_data.usd_50,
            "sell": rates_data.usd_50_sell,
            "flag": "./flags/1x1/us.svg",
            "is_transfer": False
        },
        "EUR": {
            "buy": rates_data.eur_thb,
            "sell": rates_data.eur_thb_sell,
            "flag": "./flags/1x1/eu.svg",
            "is_transfer": False
        },
        "GBP": {
            "buy": rates_data.gbp_thb,
            "sell": rates_data.gbp_thb_sell,
            "flag": "./flags/1x1/gb.svg",
            "is_transfer": False
        },
        "AED": {
            "buy": rates_data.aed_thb,
            "sell": rates_data.aed_thb_sell,
            "flag": "./flags/1x1/ae.svg",
            "is_transfer": False
        },
        "USDT": {
            "buy": rates_data.usdt_bot,
            "sell": rates_data.usdt_bot_sell,
            "flag": "./flags/1x1/us.svg",
            "is_transfer": False
        },
        "KWD": {
            "buy": rates_data.kwd_thb,
            "sell": rates_data.kwd_thb_sell,
            "flag": "./flags/1x1/kw.svg",
            "is_transfer": False
        },
        "BHD": {
            "buy": rates_data.bhd_thb,
            "sell": rates_data.bhd_thb_sell,
            "flag": "./flags/1x1/bh.svg",
            "is_transfer": False
        },
        "BND": {
            "buy": rates_data.bnd_thb,
            "sell": rates_data.bnd_thb_sell,
            "flag": "./flags/1x1/bn.svg",
            "is_transfer": False
        },
        "TWD": {
            "buy": rates_data.twd_thb,
            "sell": rates_data.twd_thb_sell,
            "flag": "./flags/1x1/tw.svg",
            "is_transfer": False
        },
        "QAR": {
            "buy": rates_data.qar_thb,
            "sell": rates_data.qar_thb_sell,
            "flag": "./flags/1x1/qa.svg",
            "is_transfer": False
        },
        "OMR": {
            "buy": rates_data.omr_thb,
            "sell": rates_data.omr_thb_sell,
            "flag": "./flags/1x1/om.svg",
            "is_transfer": False
        },
        "JPY": {
            "buy": rates_data.jpy_thb,
            "sell": rates_data.jpy_thb_sell,
            "flag": "./flags/1x1/jp.svg",
            "is_transfer": False
        },
        "ZAR": {
            "buy": rates_data.zar_thb,
            "sell": rates_data.zar_thb_sell,
            "flag": "./flags/1x1/za.svg",
            "is_transfer": False
        },
        "IDR": {
            "buy": rates_data.idr_thb,
            "sell": rates_data.idr_thb_sell,
            "flag": "./flags/1x1/id.svg",
            "is_transfer": False
        },
        "CHF": {
            "buy": rates_data.chf_thb,
            "sell": rates_data.chf_thb_sell,
            "flag": "./flags/1x1/ch.svg",
            "is_transfer": False
        },
        "PHP": {
            "buy": rates_data.php_thb,
            "sell": rates_data.php_thb_sell,
            "flag": "./flags/1x1/ph.svg",
            "is_transfer": False
        },
        "CNY": {
            "buy": rates_data.cny_thb,
            "sell": rates_data.cny_thb_sell,
            "flag": "./flags/1x1/cn.svg",
            "is_transfer": False
        },
        "KRW": {
            "buy": rates_data.krw_thb,
            "sell": rates_data.krw_thb_sell,
            "flag": "./flags/1x1/kr.svg",
            "is_transfer": False
        },
        "SGD": {
            "buy": rates_data.sgd_thb,
            "sell": rates_data.sgd_thb_sell,
            "flag": "./flags/1x1/sg.svg",
            "is_transfer": False
        },
        "MYR": {
            "buy": rates_data.myr_thb,
            "sell": rates_data.myr_thb_sell,
            "flag": "./flags/1x1/my.svg",
            "is_transfer": False
        },
        "HKD": {
            "buy": rates_data.hkd_thb,
            "sell": rates_data.hkd_thb_sell,
            "flag": "./flags/1x1/hk.svg",
            "is_transfer": False
        },
        "AUD": {
            "buy": rates_data.aud_thb,
            "sell": rates_data.aud_thb_sell,
            "flag": "./flags/1x1/au.svg",
            "is_transfer": False
        },
        "INR": {
            "buy": rates_data.inr_thb,
            "sell": rates_data.inr_thb_sell,
            "flag": "./flags/1x1/in.svg",
            "is_transfer": False
        },
        "SAR": {
            "buy": rates_data.sar_thb,
            "sell": rates_data.sar_thb_sell,
            "flag": "./flags/1x1/sa.svg",
            "is_transfer": False
        },
        "CAD": {
            "buy": rates_data.cad_thb,
            "sell": rates_data.cad_thb_sell,
            "flag": "./flags/1x1/ca.svg",
            "is_transfer": False
        },
        "NZD": {
            "buy": rates_data.nzd_thb,
            "sell": rates_data.nzd_thb_sell,
            "flag": "./flags/1x1/nz.svg",
            "is_transfer": False
        },
        "KZT": {
            "buy": rates_data.kzt_thb,
            "sell": rates_data.kzt_thb_sell,
            "flag": "./flags/1x1/kz.svg",
            "is_transfer": False
        }
    }

    return LisExchangeResponse(rates=rates)

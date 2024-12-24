from core.api_rates import *
from exchange.models import Rates
import logging
import datetime



async def get_list():
    from core.engine import load_correction_factors, load_correction_factors_2
    # Получаем текущее время
    now = datetime.datetime.now()
    #
    # Проверяем, попадает ли текущее время в диапазон от 00:00 до 06:00
    if 0 <= now.hour < 6:
        correction_factors = await load_correction_factors_2()
    else:
        correction_factors = await load_correction_factors()

    # correction_factors = await load_correction_factors()

    usdt_to_rub = await get_usdt_to_rub_and_thb()
    usdt_to_thb = await get_usdt_rate("THB")
    usdt_to_eur = await get_usdt_rate("THB", "EUR")
    usdt_to_gbp = await get_usdt_rate("THB", "GBP")
    usdt_to_aed = await get_usdt_rate("THB", "AED")
    thb_to_kwd = await get_usdt_rate("THB", "KWD")
    thb_to_bhd = await get_usdt_rate("THB", "BHD")
    thb_to_bnd = await get_usdt_rate("THB", "BND")
    thb_to_twd = await get_usdt_rate("THB", "TWD")
    thb_to_qar = await get_usdt_rate("THB", "QAR")
    thb_to_omr = await get_usdt_rate("THB", "OMR")
    thb_to_jpy = await get_usdt_rate("THB", "JPY")
    thb_to_zar = await get_usdt_rate("THB", "ZAR")
    thb_to_idr = await get_usdt_rate("THB", "IDR")
    thb_to_chf = await get_usdt_rate("THB", "CHF")
    thb_to_php = await get_usdt_rate("THB", "PHP")
    thb_to_cny = await get_usdt_rate("THB", "CNY")
    thb_to_krw = await get_usdt_rate("THB", "KRW")
    thb_to_sgd = await get_usdt_rate("THB", "SGD")
    thb_to_myr = await get_usdt_rate("THB", "MYR")
    thb_to_hkd = await get_usdt_rate("THB", "HKD")
    thb_to_aud = await get_usdt_rate("THB", "AUD")
    thb_to_inr = await get_usdt_rate("THB", "INR")
    thb_to_sar = await get_usdt_rate("THB", "SAR")
    thb_to_cad = await get_usdt_rate("THB", "CAD")
    thb_to_nzd = await get_usdt_rate("THB", "NZD")
    thb_to_kzt = await get_usdt_rate("THB", "KZT")

    rates = {
        'usdt_to_gbp': usdt_to_gbp,
        'usdt_to_aed': usdt_to_aed,
        'usdt_to_thb': usdt_to_thb,
        'usdt_to_eur': usdt_to_eur,
        'usdt_to_rub': usdt_to_rub,
        'thb_to_kwd': thb_to_kwd,
        'thb_to_bhd': thb_to_bhd,
        'thb_to_bnd': thb_to_bnd,
        'thb_to_twd': thb_to_twd,
        'thb_to_qar': thb_to_qar,
        'thb_to_omr': thb_to_omr,
        'thb_to_jpy': thb_to_jpy,
        'thb_to_zar': thb_to_zar,
        'thb_to_idr': thb_to_idr,
        'thb_to_chf': thb_to_chf,
        'thb_to_php': thb_to_php,
        'thb_to_cny': thb_to_cny,
        'thb_to_krw': thb_to_krw,
        'thb_to_sgd': thb_to_sgd,
        'thb_to_myr': thb_to_myr,
        'thb_to_hkd': thb_to_hkd,
        'thb_to_aud': thb_to_aud,
        'thb_to_inr': thb_to_inr,
        'thb_to_sar': thb_to_sar,
        'thb_to_cad': thb_to_cad,
        'thb_to_nzd': thb_to_nzd,
        'thb_to_kzt': thb_to_kzt,
    }

    # Функция для корректировки курса
    def apply_correction(rate, correction_factor_buy, correction_factor_sell):
        corrected_buy = float(rate) * correction_factor_buy
        corrected_sell = float(rate) * correction_factor_sell
        return corrected_buy, corrected_sell

    # Применение корректировки к курсам
    usdt_to_gbp_corrected, usdt_to_gbp_corrected_sell = apply_correction(rates['usdt_to_gbp'], *correction_factors["usdt_to_gbp"])
    usdt_to_aed_corrected, usdt_to_aed_corrected_sell = apply_correction(rates['usdt_to_aed'], *correction_factors["usdt_to_aed"])
    usdt_to_thb_corrected, usdt_to_thb_corrected_sell = apply_correction(rates['usdt_to_thb'], *correction_factors["usdt_to_thb"])
    usdt_to_thb_corrected_50, usdt_to_thb_corrected_sell_50 = apply_correction(rates['usdt_to_thb'], *correction_factors["usdt_to_thb_50"])
    usdt_to_eur_corrected, usdt_to_eur_corrected_sell = apply_correction(rates['usdt_to_eur'], *correction_factors["usdt_to_eur"])

    # Добавление недостающих валют
    thb_to_kwd_corrected, thb_to_kwd_corrected_sell = apply_correction(rates['thb_to_kwd'],
                                                                       *correction_factors["thb_to_kwd"])
    thb_to_bhd_corrected, thb_to_bhd_corrected_sell = apply_correction(rates['thb_to_bhd'],
                                                                       *correction_factors["thb_to_bhd"])
    thb_to_bnd_corrected, thb_to_bnd_corrected_sell = apply_correction(rates['thb_to_bnd'],
                                                                       *correction_factors["thb_to_bnd"])
    thb_to_twd_corrected, thb_to_twd_corrected_sell = apply_correction(rates['thb_to_twd'],
                                                                       *correction_factors["thb_to_twd"])
    thb_to_qar_corrected, thb_to_qar_corrected_sell = apply_correction(rates['thb_to_qar'],
                                                                       *correction_factors["thb_to_qar"])
    thb_to_omr_corrected, thb_to_omr_corrected_sell = apply_correction(rates['thb_to_omr'],
                                                                       *correction_factors["thb_to_omr"])
    thb_to_jpy_corrected, thb_to_jpy_corrected_sell = apply_correction(rates['thb_to_jpy'],
                                                                       *correction_factors["thb_to_jpy"])
    thb_to_zar_corrected, thb_to_zar_corrected_sell = apply_correction(rates['thb_to_zar'],
                                                                       *correction_factors["thb_to_zar"])
    thb_to_idr_corrected, thb_to_idr_corrected_sell = apply_correction(rates['thb_to_idr'],
                                                                       *correction_factors["thb_to_idr"])
    thb_to_chf_corrected, thb_to_chf_corrected_sell = apply_correction(rates['thb_to_chf'],
                                                                       *correction_factors["thb_to_chf"])
    thb_to_php_corrected, thb_to_php_corrected_sell = apply_correction(rates['thb_to_php'],
                                                                       *correction_factors["thb_to_php"])
    thb_to_cny_corrected, thb_to_cny_corrected_sell = apply_correction(rates['thb_to_cny'],
                                                                       *correction_factors["thb_to_cny"])
    thb_to_krw_corrected, thb_to_krw_corrected_sell = apply_correction(rates['thb_to_krw'],
                                                                       *correction_factors["thb_to_krw"])
    thb_to_sgd_corrected, thb_to_sgd_corrected_sell = apply_correction(rates['thb_to_sgd'],
                                                                       *correction_factors["thb_to_sgd"])
    thb_to_myr_corrected, thb_to_myr_corrected_sell = apply_correction(rates['thb_to_myr'],
                                                                       *correction_factors["thb_to_myr"])
    thb_to_hkd_corrected, thb_to_hkd_corrected_sell = apply_correction(rates['thb_to_hkd'],
                                                                       *correction_factors["thb_to_hkd"])
    thb_to_aud_corrected, thb_to_aud_corrected_sell = apply_correction(rates['thb_to_aud'],
                                                                       *correction_factors["thb_to_aud"])
    thb_to_inr_corrected, thb_to_inr_corrected_sell = apply_correction(rates['thb_to_inr'],
                                                                       *correction_factors["thb_to_inr"])
    thb_to_sar_corrected, thb_to_sar_corrected_sell = apply_correction(rates['thb_to_sar'],
                                                                       *correction_factors["thb_to_sar"])
    thb_to_cad_corrected, thb_to_cad_corrected_sell = apply_correction(rates['thb_to_cad'],
                                                                       *correction_factors["thb_to_cad"])
    thb_to_nzd_corrected, thb_to_nzd_corrected_sell = apply_correction(rates['thb_to_nzd'],
                                                                       *correction_factors["thb_to_nzd"])
    thb_to_kzt_corrected, thb_to_kzt_corrected_sell = apply_correction(rates['thb_to_kzt'],
                                                                       *correction_factors["thb_to_kzt"])

    usdt_bot_corrected, usdt_bot_corrected_sell = apply_correction(rates['usdt_to_thb'], *correction_factors["usdt_bot_rate"])

    # Проверка данных перед вычислением и пропуск, если данных нет
    if any(value is None for value in [rates.get('usdt_to_rub'), rates.get('usdt_to_thb')]):
        logging.ERROR("Пропуск вычислений: отсутствуют значения 'usdt_to_rub' или 'usdt_to_thb' в словаре rates.")
    else:
        # Вычисление новых курсов для RUB
        new_curs = float(rates['usdt_to_rub']) / float(rates['usdt_to_thb']) * correction_factors["rub_coff_tran"][0]
        sell_rub_trans = float(rates['usdt_to_rub']) / float(rates['usdt_to_thb']) * \
                         correction_factors["rub_coff_tran"][1]

        new_curs_sell = float(rates['usdt_to_rub']) / float(rates['usdt_to_thb']) * correction_factors["rub_coff_cash"][
            0]
        sell_rub_cash = float(rates['usdt_to_rub']) / float(rates['usdt_to_thb']) * correction_factors["rub_coff_cash"][
            1]



    # Форматирование результата
    new_rate_ru = round(new_curs, 2)
    new_rate_ru_sell = round(new_curs_sell, 2)
    new_rate_ru_sell_trans = round(sell_rub_trans, 2)
    new_rate_ru_sell_cash = round(sell_rub_cash, 2)

    # Формирование словаря с результатами
    rates = {
        "RUB (online)": {"buy": new_rate_ru, "sell": new_rate_ru_sell_trans, "flag": "./flags/1x1/ru.svg", "bank_logos": ["./images/sberbank-logo.png", "./images/tinkoff-logo.png"], "is_transfer": True},
        "RUB (cash)": {"buy": new_rate_ru_sell, "sell": new_rate_ru_sell_cash, "flag": "./flags/1x1/ru.svg", "is_transfer": False},
        "USD 100": {"buy": usdt_to_thb_corrected, "sell": usdt_to_thb_corrected_sell, "flag": "./flags/1x1/us.svg", "is_transfer": False},
        "USD 1-50": {"buy": usdt_to_thb_corrected_50, "sell": usdt_to_thb_corrected_sell_50, "flag": "./flags/1x1/us.svg", "is_transfer": False},
        "EUR": {"buy": usdt_to_eur_corrected, "sell": usdt_to_eur_corrected_sell, "flag": "./flags/1x1/eu.svg", "is_transfer": False},
        "GBP": {"buy": usdt_to_gbp_corrected, "sell": usdt_to_gbp_corrected_sell, "flag": "./flags/1x1/gb.svg", "is_transfer": False},
        "AED": {"buy": usdt_to_aed_corrected, "sell": usdt_to_aed_corrected_sell, "flag": "./flags/1x1/ae.svg", "is_transfer": False},
        "USDT": {"buy": usdt_bot_corrected, "sell": usdt_bot_corrected_sell, "flag": "./flags/1x1/us.svg", "is_transfer": False},
        "KWD": {
            "buy": thb_to_kwd_corrected,
            "sell": thb_to_kwd_corrected_sell,
            "flag": "./flags/1x1/kw.svg",
            "is_transfer": False
        },
        "BHD": {
            "buy": thb_to_bhd_corrected,
            "sell": thb_to_bhd_corrected_sell,
            "flag": "./flags/1x1/bh.svg",
            "is_transfer": False
        },
        "BND": {
            "buy": thb_to_bnd_corrected,
            "sell": thb_to_bnd_corrected_sell,
            "flag": "./flags/1x1/bn.svg",
            "is_transfer": False
        },
        "TWD": {
            "buy": thb_to_twd_corrected,
            "sell": thb_to_twd_corrected_sell,
            "flag": "./flags/1x1/tw.svg",
            "is_transfer": False
        },
        "QAR": {
            "buy": thb_to_qar_corrected,
            "sell": thb_to_qar_corrected_sell,
            "flag": "./flags/1x1/qa.svg",
            "is_transfer": False
        },
        "OMR": {
            "buy": thb_to_omr_corrected,
            "sell": thb_to_omr_corrected_sell,
            "flag": "./flags/1x1/om.svg",
            "is_transfer": False
        },
        "JPY": {
            "buy": thb_to_jpy_corrected,
            "sell": thb_to_jpy_corrected_sell,
            "flag": "./flags/1x1/jp.svg",
            "is_transfer": False
        },
        "ZAR": {
            "buy": thb_to_zar_corrected,
            "sell": thb_to_zar_corrected_sell,
            "flag": "./flags/1x1/za.svg",
            "is_transfer": False
        },
        "IDR": {
            "buy": thb_to_idr_corrected,
            "sell": thb_to_idr_corrected_sell,
            "flag": "./flags/1x1/id.svg",
            "is_transfer": False
        },
        "CHF": {
            "buy": thb_to_chf_corrected,
            "sell": thb_to_chf_corrected_sell,
            "flag": "./flags/1x1/ch.svg",
            "is_transfer": False
        },
        "PHP": {
            "buy": thb_to_php_corrected,
            "sell": thb_to_php_corrected_sell,
            "flag": "./flags/1x1/ph.svg",
            "is_transfer": False
        },
        "CNY": {
            "buy": thb_to_cny_corrected,
            "sell": thb_to_cny_corrected_sell,
            "flag": "./flags/1x1/cn.svg",
            "is_transfer": False
        },
        "KRW": {
            "buy": thb_to_krw_corrected,
            "sell": thb_to_krw_corrected_sell,
            "flag": "./flags/1x1/kr.svg",
            "is_transfer": False
        },
        "SGD": {
            "buy": thb_to_sgd_corrected,
            "sell": thb_to_sgd_corrected_sell,
            "flag": "./flags/1x1/sg.svg",
            "is_transfer": False
        },
        "MYR": {
            "buy": thb_to_myr_corrected,
            "sell": thb_to_myr_corrected_sell,
            "flag": "./flags/1x1/my.svg",
            "is_transfer": False
        },
        "HKD": {
            "buy": thb_to_hkd_corrected,
            "sell": thb_to_hkd_corrected_sell,
            "flag": "./flags/1x1/hk.svg",
            "is_transfer": False
        },
        "AUD": {
            "buy": thb_to_aud_corrected,
            "sell": thb_to_aud_corrected_sell,
            "flag": "./flags/1x1/au.svg",
            "is_transfer": False
        },
        "INR": {
            "buy": thb_to_inr_corrected,
            "sell": thb_to_inr_corrected_sell,
            "flag": "./flags/1x1/in.svg",
            "is_transfer": False
        },
        "SAR": {
            "buy": thb_to_sar_corrected,
            "sell": thb_to_sar_corrected_sell,
            "flag": "./flags/1x1/sa.svg",
            "is_transfer": False
        },
        "CAD": {
            "buy": thb_to_cad_corrected,
            "sell": thb_to_cad_corrected_sell,
            "flag": "./flags/1x1/ca.svg",
            "is_transfer": False
        },
        "NZD": {
            "buy": thb_to_nzd_corrected,
            "sell": thb_to_nzd_corrected_sell,
            "flag": "./flags/1x1/nz.svg",
            "is_transfer": False
        },
        "KZT": {
            "buy": thb_to_kzt_corrected,
            "sell": thb_to_kzt_corrected_sell,
            "flag": "./flags/1x1/kz.svg",
            "is_transfer": False
        }
    }

    # Округляем значения покупки и продажи
    for currency, details in rates.items():
        if isinstance(details["buy"], (int, float)):
            if currency in ["IDR", "KRW"]:  # Исключение для IDR и KRW
                precision = 5 if currency == "IDR" else 4
                details["buy"] = round(details["buy"], precision)
            elif currency in ["JPY", "PHP", "INR"]:  # Исключение для JPY и PHP
                details["buy"] = round(details["buy"], 3)
            else:
                details["buy"] = round(details["buy"], 2)

        if isinstance(details["sell"], (int, float)):
            if currency in ["IDR", "KRW"]:  # Исключение для IDR и KRW
                precision = 5 if currency == "IDR" else 4
                details["sell"] = round(details["sell"], precision)
            elif currency in ["JPY", "PHP", "INR"]:  # Исключение для JPY и PHP
                details["sell"] = round(details["sell"], 3)
            else:
                details["sell"] = round(details["sell"], 2)

    # Создаем объект модели User с данными из словаря
    user = Rates(
        rub_tra=rates["RUB (online)"]["buy"],
        rub_cash=rates["RUB (cash)"]["buy"],
        usd_100=rates["USD 100"]["buy"],
        usd_50=rates["USD 1-50"]["buy"],
        eur_thb=rates["EUR"]["buy"],
        gbp_thb=rates["GBP"]["buy"],
        aed_thb=rates["AED"]["buy"],

        rub_tra_sell=rates["RUB (online)"]["sell"],
        rub_cash_sell=rates["RUB (cash)"]["sell"],
        usd_100_sell=rates["USD 100"]["sell"],
        usd_50_sell=rates["USD 1-50"]["sell"],
        eur_thb_sell=rates["EUR"]["sell"],
        gbp_thb_sell=rates["GBP"]["sell"],
        aed_thb_sell=rates["AED"]["sell"],

        usdt_bot=rates["USDT"]["buy"],
        usdt_bot_sell=rates["USDT"]["sell"],

        kwd_thb=rates["KWD"]["buy"],
        bhd_thb=rates["BHD"]["buy"],
        bnd_thb=rates["BND"]["buy"],
        twd_thb=rates["TWD"]["buy"],
        qar_thb=rates["QAR"]["buy"],
        omr_thb=rates["OMR"]["buy"],
        jpy_thb=rates["JPY"]["buy"],
        zar_thb=rates["ZAR"]["buy"],
        idr_thb=rates["IDR"]["buy"],
        chf_thb=rates["CHF"]["buy"],
        php_thb=rates["PHP"]["buy"],
        cny_thb=rates["CNY"]["buy"],
        krw_thb=rates["KRW"]["buy"],
        sgd_thb=rates["SGD"]["buy"],
        myr_thb=rates["MYR"]["buy"],
        hkd_thb=rates["HKD"]["buy"],
        aud_thb=rates["AUD"]["buy"],
        inr_thb=rates["INR"]["buy"],
        sar_thb=rates["SAR"]["buy"],
        cad_thb=rates["CAD"]["buy"],
        nzd_thb=rates["NZD"]["buy"],
        kzt_thb=rates["KZT"]["buy"],

        kwd_thb_sell=rates["KWD"]["sell"],
        bhd_thb_sell=rates["BHD"]["sell"],
        bnd_thb_sell=rates["BND"]["sell"],
        twd_thb_sell=rates["TWD"]["sell"],
        qar_thb_sell=rates["QAR"]["sell"],
        omr_thb_sell=rates["OMR"]["sell"],
        jpy_thb_sell=rates["JPY"]["sell"],
        zar_thb_sell=rates["ZAR"]["sell"],
        idr_thb_sell=rates["IDR"]["sell"],
        chf_thb_sell=rates["CHF"]["sell"],
        php_thb_sell=rates["PHP"]["sell"],
        cny_thb_sell=rates["CNY"]["sell"],
        krw_thb_sell=rates["KRW"]["sell"],
        sgd_thb_sell=rates["SGD"]["sell"],
        myr_thb_sell=rates["MYR"]["sell"],
        hkd_thb_sell=rates["HKD"]["sell"],
        aud_thb_sell=rates["AUD"]["sell"],
        inr_thb_sell=rates["INR"]["sell"],
        sar_thb_sell=rates["SAR"]["sell"],
        cad_thb_sell=rates["CAD"]["sell"],
        nzd_thb_sell=rates["NZD"]["sell"],
        kzt_thb_sell=rates["KZT"]["sell"]
    )

    return user

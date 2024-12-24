import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_TYPE: str
    TG_TOKEN: str
    API_KEY_RATE: str
    WEBHOOK_HOST: str
    WEBHOOK_PATH: str
    WEBAPP_HOST: str
    WEBAPP_PORT: int
    OPERATOR: int
    TG_TOKEN2: str
    ALLOWED_MANAGER_USER_ID_1: int
    ALLOWED_MANAGER_USER_ID_2: int
    WEBHOOK_PATH_2: str
    WEBAPP_PORT_2: int
    API_RATES: str
    BOT_USERNAME: str

    class Config:
        # Путь к файлу .env
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")


# Загрузка настроек и коэффициентов
settings = Settings()


# Список ID операторов
OPERATOR_USER_IDS = [settings.ALLOWED_MANAGER_USER_ID_1, settings.ALLOWED_MANAGER_USER_ID_2]

TEMP_MESSAGES = {}  # {operator_id: {"text": "текст сообщения"}}

# Проверка доступа manager
def is_allowed_user(user_id):
    return user_id in OPERATOR_USER_IDS

correction_factors2 = {
    "usdt_to_gbp": [0.985, 1.01],
    "usdt_to_aed": [0.965, 1.01],
    "usdt_to_thb": [0.99, 1.01],
    "usdt_to_thb_50": [0.98, 1.005],
    "usdt_to_eur": [0.985, 1.01],
    "rub_coff_cash": [1.1, 0.97],
    "rub_coff_tran": [1.05, 0.95],
    "usdt_bot_rate": [0.97, 1],
    "thb_to_kwd": [0.975, 1.0],
    "thb_to_bhd": [0.975, 1.0],
    "thb_to_bnd": [0.975, 1.0],
    "thb_to_twd": [0.975, 1.0],
    "thb_to_qar": [0.975, 1.0],
    "thb_to_omr": [0.975, 1.0],
    "thb_to_jpy": [0.975, 1.0],
    "thb_to_zar": [0.975, 1.0],
    "thb_to_idr": [0.975, 1.0],
    "thb_to_chf": [0.975, 1.0],
    "thb_to_php": [0.975, 1.0],
    "thb_to_cny": [0.975, 1.0],
    "thb_to_krw": [0.975, 1.0],
    "thb_to_sgd": [0.975, 1.0],
    "thb_to_myr": [0.975, 1.0],
    "thb_to_hkd": [0.975, 1.0],
    "thb_to_aud": [0.975, 1.0],
    "thb_to_inr": [0.975, 1.0],
    "thb_to_sar": [0.975, 1.0],
    "thb_to_cad": [0.975, 1.0],
    "thb_to_nzd": [0.975, 1.0],
    "thb_to_kzt": [0.975, 1.0],
}

correction_factors_night = {
    "usdt_to_gbp": [0.955, 1.01],
    "usdt_to_aed": [0.935, 1.01],
    "usdt_to_thb": [0.96, 1.01],
    "usdt_to_thb_50": [0.95, 1.005],
    "usdt_to_eur": [0.955, 1.01],
    "rub_coff_cash": [1.07, 0.97],
    "rub_coff_tran": [1.07, 0.95],
    "usdt_bot_rate": [0.94, 1.0],
    "thb_to_kwd": [0.945, 1.0],
    "thb_to_bhd": [0.945, 1.0],
    "thb_to_bnd": [0.945, 1.0],
    "thb_to_twd": [0.945, 1.0],
    "thb_to_qar": [0.945, 1.0],
    "thb_to_omr": [0.945, 1.0],
    "thb_to_jpy": [0.945, 1.0],
    "thb_to_zar": [0.925, 1.0],
    "thb_to_idr": [0.945, 1.0],
    "thb_to_chf": [0.945, 1.0],
    "thb_to_php": [0.945, 1.0],
    "thb_to_cny": [0.945, 1.0],
    "thb_to_krw": [0.945, 1.0],
    "thb_to_sgd": [0.945, 1.0],
    "thb_to_myr": [0.945, 1.0],
    "thb_to_hkd": [0.945, 1.0],
    "thb_to_aud": [0.945, 1.0],
    "thb_to_inr": [0.945, 1.0],
    "thb_to_sar": [0.945, 1.0],
    "thb_to_cad": [0.945, 1.0],
    "thb_to_nzd": [0.945, 1.0],
    "thb_to_kzt": [0.945, 1.0]
}

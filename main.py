from fastapi import FastAPI
from exchange.router import router as router_rates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from bot_24.router_bot import router as router_bot


app = FastAPI()

# Добавление перенаправления на HTTPS
app.add_middleware(HTTPSRedirectMiddleware)

# Настройка CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://172.24.0.1"],  # Разрешённый источник
    allow_credentials=True,
    allow_methods=["*"],  # Разрешены только GET-запросы
    allow_headers=["*"],  # Разрешены любые заголовки
)



app.include_router(router_rates)
app.include_router(router_bot)
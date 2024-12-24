FROM python:3.8

# Копируем SSL-сертификаты
COPY ssl/server.crt /ssl/server.crt
COPY ssl/server.key /ssl/server.key

WORKDIR /fast_api_ex
# Копируем только необходимые файлы для установки зависимостей
COPY ../requirements.txt ./

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта
COPY .. /fast_api_ex/

# Set the entry point to run the bot
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "443", "--ssl-keyfile", "/ssl/server.key", "--ssl-certfile", "/ssl/server.crt"]


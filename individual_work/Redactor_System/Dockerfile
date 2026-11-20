FROM python:3.11-slim

# Устанавливаем системные зависимости для работы с Postgres
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Открываем порт для FastAPI
EXPOSE 8000

# Команда запуска теперь в docker-compose, но можно продублировать
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
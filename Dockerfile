FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости (если нужны)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем Python-зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё приложение
COPY . .

# Даём права на выполнение скрипта entrypoint
RUN chmod +x /app/entrypoint.sh

# Указываем порт
EXPOSE 8000

# Запускаем через entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
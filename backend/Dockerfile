# Используем официальный образ Python
FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальной код приложения
COPY . .

# Создаем пользователя для запуска приложения (опционально, для безопасности)
RUN useradd -m -u 1000 -p "$(openssl passwd -1 1234)" appuser && chown -R appuser:appuser /app
USER appuser

# Открываем порт, на котором будет работать приложение
EXPOSE 8000
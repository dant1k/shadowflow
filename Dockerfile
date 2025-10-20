# ShadowFlow Docker контейнер
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя для безопасности
RUN useradd --create-home --shell /bin/bash shadowflow

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Создаем необходимые директории
RUN mkdir -p logs data static templates

# Устанавливаем права доступа
RUN chown -R shadowflow:shadowflow /app

# Переключаемся на пользователя shadowflow
USER shadowflow

# Открываем порт
EXPOSE 5001

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Команда запуска
CMD ["python3", "docker_start.py"]

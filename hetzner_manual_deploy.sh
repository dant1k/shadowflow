#!/bin/bash

# 🚀 Ручной скрипт развертывания ShadowFlow на сервере Hetzner
# Выполните этот скрипт на сервере 46.62.233.6

set -e

echo "🚀 Начинаем развертывание ShadowFlow на сервере Hetzner..."

# Обновляем систему
echo "📦 Обновление системы..."
apt-get update -y

# Устанавливаем необходимые пакеты
echo "🔧 Установка необходимых пакетов..."
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    wget \
    unzip

# Добавляем официальный GPG ключ Docker
echo "🔑 Добавление GPG ключа Docker..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Добавляем репозиторий Docker
echo "📋 Добавление репозитория Docker..."
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Обновляем пакеты
echo "🔄 Обновление пакетов..."
apt-get update -y

# Устанавливаем Docker
echo "🐳 Установка Docker..."
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Запускаем Docker
echo "▶️ Запуск Docker..."
systemctl start docker
systemctl enable docker

# Проверяем установку
echo "✅ Проверка установки Docker..."
docker --version
docker-compose --version

# Создаем директории
echo "📁 Создание директорий..."
mkdir -p /opt/shadowflow
mkdir -p /opt/shadowflow/data
mkdir -p /opt/shadowflow/logs
mkdir -p /opt/shadowflow/ssl
mkdir -p /opt/shadowflow/data/models

cd /opt/shadowflow

# Создаем docker-compose.yml
echo "📝 Создание docker-compose.yml..."
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  shadowflow:
    image: dant1k/shadowflow:latest
    container_name: shadowflow-prod
    restart: unless-stopped
    ports:
      - "5001:5001"
    volumes:
      - shadowflow-data:/app/data
      - shadowflow-logs:/app/logs
      - shadowflow-models:/app/data/models
    environment:
      - PYTHONUNBUFFERED=1
      - FLASK_ENV=production
      - TZ=UTC
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/api/scheduler-status"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - shadowflow-network

  nginx:
    image: nginx:alpine
    container_name: shadowflow-nginx-prod
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - shadowflow
    networks:
      - shadowflow-network

networks:
  shadowflow-network:
    driver: bridge

volumes:
  shadowflow-data:
  shadowflow-logs:
  shadowflow-models:
EOF

# Создаем nginx конфигурацию
echo "🌐 Создание nginx конфигурации..."
cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream shadowflow {
        server shadowflow:5001;
    }

    server {
        listen 80;
        server_name _;

        location / {
            proxy_pass http://shadowflow;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /api/ {
            proxy_pass http://shadowflow;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF

# Запускаем контейнеры
echo "🚀 Запуск контейнеров..."
docker-compose up -d

# Ждем запуска
echo "⏳ Ожидание запуска контейнеров..."
sleep 30

# Проверяем статус
echo "📊 Проверка статуса контейнеров..."
docker-compose ps

# Проверяем работу API
echo "🔍 Проверка работы API..."
sleep 10

if curl -s -f "http://localhost:5001/api/predictive/status" > /dev/null; then
    echo "✅ API доступен на порту 5001"
else
    echo "⚠️ API на порту 5001 недоступен, проверяем nginx..."
    if curl -s -f "http://localhost/api/predictive/status" > /dev/null; then
        echo "✅ API доступен через nginx на порту 80"
    else
        echo "❌ API недоступен"
    fi
fi

echo ""
echo "🎉 Развертывание ShadowFlow завершено!"
echo ""
echo "🌐 Доступ к системе:"
echo "   - Прямой доступ: http://46.62.233.6:5001"
echo "   - Через nginx: http://46.62.233.6"
echo ""
echo "🔧 Управление:"
echo "   - Логи: docker-compose logs -f shadowflow"
echo "   - Перезапуск: docker-compose restart"
echo "   - Остановка: docker-compose down"
echo ""
echo "📊 Полезные команды:"
echo "   - Статус: docker-compose ps"
echo "   - Обновление: docker-compose pull && docker-compose up -d"
echo ""
echo "🚀 ShadowFlow готов к работе на сервере Hetzner!"

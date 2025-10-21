#!/bin/bash

# 🚀 Скрипт развертывания ShadowFlow на сервере Hetzner
# Автор: AI Assistant
# Дата: 21 октября 2025

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции логирования
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Конфигурация сервера
HOST="46.62.233.6"
USER="root"
PRIVATE_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJaF0ITwfl/atpsXfqkj8jyPy+5VK/ltKuXNLEwYZXiZ cursor"

# Конфигурация Docker
DOCKER_USERNAME="dant1k"
IMAGE_NAME="shadowflow"
TAG="latest"
FULL_IMAGE_NAME="${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}"

log "🚀 Начинаем развертывание ShadowFlow на сервере Hetzner..."
log "📍 Сервер: ${HOST}"
log "👤 Пользователь: ${USER}"

# Создаем SSH ключ
log "🔑 Создание SSH ключа..."
mkdir -p ~/.ssh
echo "${PRIVATE_KEY}" > ~/.ssh/hetzner_key
chmod 600 ~/.ssh/hetzner_key

# Добавляем сервер в known_hosts
log "🔍 Добавление сервера в known_hosts..."
ssh-keyscan -H ${HOST} >> ~/.ssh/known_hosts 2>/dev/null || true

# Проверяем подключение к серверу
log "🔌 Проверка подключения к серверу..."
if ! ssh -i ~/.ssh/hetzner_key -o ConnectTimeout=10 -o StrictHostKeyChecking=no ${USER}@${HOST} "echo 'Подключение успешно'" 2>/dev/null; then
    error "Не удалось подключиться к серверу ${HOST}"
    error "Проверьте IP адрес и SSH ключ"
    exit 1
fi

success "✅ Подключение к серверу установлено"

# Устанавливаем Docker на сервере
log "🐳 Установка Docker на сервере..."
ssh -i ~/.ssh/hetzner_key ${USER}@${HOST} << 'EOF'
# Обновляем систему
apt-get update -y

# Устанавливаем необходимые пакеты
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    wget \
    unzip

# Добавляем официальный GPG ключ Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Добавляем репозиторий Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Обновляем пакеты
apt-get update -y

# Устанавливаем Docker
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Запускаем Docker
systemctl start docker
systemctl enable docker

# Добавляем пользователя в группу docker
usermod -aG docker root

# Проверяем установку
docker --version
docker-compose --version
EOF

success "✅ Docker установлен на сервере"

# Создаем директории на сервере
log "📁 Создание директорий на сервере..."
ssh -i ~/.ssh/hetzner_key ${USER}@${HOST} << 'EOF'
mkdir -p /opt/shadowflow
mkdir -p /opt/shadowflow/data
mkdir -p /opt/shadowflow/logs
mkdir -p /opt/shadowflow/ssl
mkdir -p /opt/shadowflow/data/models
EOF

# Создаем docker-compose файл для сервера
log "📝 Создание docker-compose файла для сервера..."
ssh -i ~/.ssh/hetzner_key ${USER}@${HOST} << EOF
cat > /opt/shadowflow/docker-compose.yml << 'COMPOSE_EOF'
version: '3.8'

services:
  shadowflow:
    image: ${FULL_IMAGE_NAME}
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
COMPOSE_EOF
EOF

# Создаем nginx конфигурацию
log "🌐 Создание nginx конфигурации..."
ssh -i ~/.ssh/hetzner_key ${USER}@${HOST} << 'EOF'
cat > /opt/shadowflow/nginx.conf << 'NGINX_EOF'
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
NGINX_EOF
EOF

# Запускаем контейнеры
log "🚀 Запуск контейнеров на сервере..."
ssh -i ~/.ssh/hetzner_key ${USER}@${HOST} << 'EOF'
cd /opt/shadowflow

# Останавливаем существующие контейнеры
docker-compose down 2>/dev/null || true

# Запускаем новые контейнеры
docker-compose up -d

# Ждем запуска
sleep 30

# Проверяем статус
docker-compose ps
EOF

# Проверяем работу системы
log "🔍 Проверка работы системы..."
sleep 10

# Проверяем доступность API
log "📡 Проверка API endpoints..."
if curl -s -f "http://${HOST}:5001/api/predictive/status" > /dev/null; then
    success "✅ API доступен на порту 5001"
else
    warning "⚠️ API на порту 5001 недоступен, проверяем nginx..."
    if curl -s -f "http://${HOST}/api/predictive/status" > /dev/null; then
        success "✅ API доступен через nginx на порту 80"
    else
        error "❌ API недоступен"
    fi
fi

# Получаем статус системы
log "📊 Получение статуса системы..."
ssh -i ~/.ssh/hetzner_key ${USER}@${HOST} << 'EOF'
echo "=== Статус контейнеров ==="
docker-compose ps

echo ""
echo "=== Логи ShadowFlow ==="
docker-compose logs --tail=10 shadowflow

echo ""
echo "=== Использование ресурсов ==="
docker stats --no-stream
EOF

# Финальная проверка
log "🎯 Финальная проверка развертывания..."

# Проверяем доступность веб-интерфейса
if curl -s -I "http://${HOST}:5001" | grep -q "200 OK"; then
    success "✅ Веб-интерфейс доступен на http://${HOST}:5001"
elif curl -s -I "http://${HOST}" | grep -q "200 OK"; then
    success "✅ Веб-интерфейс доступен на http://${HOST}"
else
    warning "⚠️ Веб-интерфейс может быть недоступен"
fi

# Проверяем API
if curl -s "http://${HOST}:5001/api/predictive/status" | grep -q "success"; then
    success "✅ API предсказательной аналитики работает"
else
    warning "⚠️ API предсказательной аналитики может быть недоступен"
fi

success "🎉 Развертывание ShadowFlow на сервере Hetzner завершено!"
echo ""
echo "🌐 Доступ к системе:"
echo "   - Прямой доступ: http://${HOST}:5001"
echo "   - Через nginx: http://${HOST}"
echo ""
echo "📊 Управление:"
echo "   - SSH: ssh -i ~/.ssh/hetzner_key ${USER}@${HOST}"
echo "   - Логи: docker-compose -f /opt/shadowflow/docker-compose.yml logs -f"
echo "   - Перезапуск: docker-compose -f /opt/shadowflow/docker-compose.yml restart"
echo ""
echo "🔧 Полезные команды:"
echo "   - Статус: docker-compose -f /opt/shadowflow/docker-compose.yml ps"
echo "   - Остановка: docker-compose -f /opt/shadowflow/docker-compose.yml down"
echo "   - Обновление: docker-compose -f /opt/shadowflow/docker-compose.yml pull && docker-compose -f /opt/shadowflow/docker-compose.yml up -d"
echo ""
success "🚀 ShadowFlow готов к работе на сервере Hetzner!"

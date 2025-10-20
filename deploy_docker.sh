#!/bin/bash

# Скрипт развертывания ShadowFlow с Docker
# Простое развертывание в контейнерах

set -e

echo "🐳 ShadowFlow Docker Deployment"
echo "==============================="
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция логирования
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Проверка Docker
if ! command -v docker &> /dev/null; then
    error "Docker не установлен. Установите Docker и попробуйте снова."
fi

if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose не установлен. Установите Docker Compose и попробуйте снова."
fi

log "Начинаем Docker развертывание ShadowFlow..."

# Создание директорий для данных
log "Создание директорий для данных..."
mkdir -p data logs ssl

# Создание .env файла
log "Создание конфигурации..."
cat > .env << EOF
# ShadowFlow Configuration
FLASK_ENV=production
PYTHONUNBUFFERED=1
TZ=UTC
EOF

# Сборка и запуск контейнеров
log "Сборка Docker образов..."
docker-compose build

log "Запуск контейнеров..."
docker-compose up -d

# Ожидание запуска
log "Ожидание запуска сервисов..."
sleep 10

# Проверка статуса
log "Проверка статуса контейнеров..."
if docker-compose ps | grep -q "Up"; then
    log "✅ Контейнеры запущены"
else
    error "❌ Контейнеры не запустились"
fi

# Проверка здоровья
log "Проверка здоровья приложения..."
for i in {1..30}; do
    if curl -f http://localhost:5001/api/scheduler-status &> /dev/null; then
        log "✅ Приложение отвечает"
        break
    fi
    if [ $i -eq 30 ]; then
        error "❌ Приложение не отвечает"
    fi
    sleep 2
done

# Получение IP сервера
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "localhost")
log "✅ Сервер доступен по IP: $SERVER_IP"

echo ""
echo "🎉 DOCKER РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО!"
echo "=================================="
echo ""
echo "🌐 Веб-интерфейс: http://$SERVER_IP"
echo "📊 Real-time: http://$SERVER_IP/realtime"
echo "📡 Мониторинг: http://$SERVER_IP/monitoring"
echo ""
echo "🎛️ УПРАВЛЕНИЕ КОНТЕЙНЕРАМИ:"
echo "============================"
echo "docker-compose up -d          # Запуск"
echo "docker-compose down           # Остановка"
echo "docker-compose restart        # Перезапуск"
echo "docker-compose logs -f        # Просмотр логов"
echo "docker-compose ps             # Статус контейнеров"
echo ""
echo "📝 ЛОГИ:"
echo "========"
echo "docker-compose logs shadowflow"
echo "docker-compose logs nginx"
echo "tail -f logs/24_7.log"
echo ""
echo "🔧 ОБНОВЛЕНИЕ:"
echo "=============="
echo "git pull"
echo "docker-compose build"
echo "docker-compose up -d"
echo ""
echo "🎉 Система готова к работе 24/7 в Docker!"

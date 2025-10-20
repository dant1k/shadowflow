#!/bin/bash

# Скрипт быстрого развертывания ShadowFlow на сервер
# Поддерживает Ubuntu/Debian серверы

set -e

echo "🚀 ShadowFlow Server Deployment"
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

# Проверка прав root
if [[ $EUID -eq 0 ]]; then
   error "Не запускайте скрипт от имени root. Используйте обычного пользователя с sudo правами."
fi

# Проверка операционной системы
if ! command -v apt-get &> /dev/null; then
    error "Этот скрипт предназначен для Ubuntu/Debian систем"
fi

log "Начинаем развертывание ShadowFlow..."

# Обновление системы
log "Обновление системы..."
sudo apt update && sudo apt upgrade -y

# Установка зависимостей
log "Установка системных зависимостей..."
sudo apt install -y python3 python3-pip python3-venv nginx curl wget git build-essential cmake

# Установка Docker (опционально)
if command -v docker &> /dev/null; then
    log "Docker уже установлен"
else
    log "Установка Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# Создание директории проекта
PROJECT_DIR="/home/$USER/shadowflow"
log "Создание директории проекта: $PROJECT_DIR"
mkdir -p $PROJECT_DIR

# Копирование файлов проекта
log "Копирование файлов проекта..."
cp -r . $PROJECT_DIR/
cd $PROJECT_DIR

# Создание виртуального окружения
log "Создание Python виртуального окружения..."
python3 -m venv venv
source venv/bin/activate

# Установка Python зависимостей
log "Установка Python зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

# Создание systemd службы
log "Создание systemd службы..."
sudo tee /etc/systemd/system/shadowflow.service > /dev/null << EOF
[Unit]
Description=ShadowFlow - Polymarket Analysis System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/start_24_7.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Настройка Nginx
log "Настройка Nginx..."
sudo tee /etc/nginx/sites-available/shadowflow > /dev/null << EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket поддержка
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    location /static {
        alias $PROJECT_DIR/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Активация сайта Nginx
sudo ln -sf /etc/nginx/sites-available/shadowflow /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Проверка конфигурации Nginx
sudo nginx -t || error "Ошибка конфигурации Nginx"

# Настройка файрвола
log "Настройка файрвола..."
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Перезагрузка systemd и запуск служб
log "Запуск служб..."
sudo systemctl daemon-reload
sudo systemctl enable shadowflow
sudo systemctl start shadowflow
sudo systemctl restart nginx

# Проверка статуса
log "Проверка статуса служб..."
sleep 5

if sudo systemctl is-active --quiet shadowflow; then
    log "✅ ShadowFlow служба работает"
else
    error "❌ ShadowFlow служба не запустилась"
fi

if sudo systemctl is-active --quiet nginx; then
    log "✅ Nginx работает"
else
    error "❌ Nginx не запустился"
fi

# Получение IP сервера
SERVER_IP=$(curl -s ifconfig.me)
log "✅ Сервер доступен по IP: $SERVER_IP"

echo ""
echo "🎉 РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО!"
echo "============================"
echo ""
echo "🌐 Веб-интерфейс: http://$SERVER_IP"
echo "📊 Real-time: http://$SERVER_IP/realtime"
echo "📡 Мониторинг: http://$SERVER_IP/monitoring"
echo ""
echo "🎛️ УПРАВЛЕНИЕ:"
echo "==============="
echo "sudo systemctl start shadowflow"
echo "sudo systemctl stop shadowflow"
echo "sudo systemctl restart shadowflow"
echo "sudo systemctl status shadowflow"
echo ""
echo "📝 ЛОГИ:"
echo "========"
echo "sudo journalctl -u shadowflow -f"
echo "tail -f $PROJECT_DIR/logs/24_7.log"
echo ""
echo "🐳 DOCKER (опционально):"
echo "========================"
echo "cd $PROJECT_DIR"
echo "docker-compose up -d"
echo ""
echo "🎉 Система готова к работе 24/7!"

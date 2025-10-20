# 🌐 ShadowFlow Server Deployment Guide

## 📋 Обзор

Полное руководство по развертыванию ShadowFlow на сервере для работы 24/7.

## 🎯 Варианты развертывания

### 1. 🐧 Ubuntu/Debian сервер (systemd)
- ✅ Полная интеграция с системой
- ✅ Автоматический запуск при загрузке
- ✅ Nginx как reverse proxy
- ✅ Systemd для управления службами

### 2. 🐳 Docker контейнеры
- ✅ Изолированная среда
- ✅ Простое развертывание
- ✅ Масштабируемость
- ✅ Легкое обновление

### 3. ☁️ Облачные платформы
- ✅ AWS, Google Cloud, Azure
- ✅ Автоматическое масштабирование
- ✅ Высокая доступность

## 🚀 Быстрое развертывание

### Вариант 1: Ubuntu/Debian сервер

```bash
# 1. Подключитесь к серверу
ssh user@your-server-ip

# 2. Клонируйте проект
git clone https://github.com/your-repo/shadowflow.git
cd shadowflow

# 3. Запустите автоматическое развертывание
chmod +x deploy.sh
./deploy.sh
```

### Вариант 2: Docker

```bash
# 1. Подключитесь к серверу
ssh user@your-server-ip

# 2. Клонируйте проект
git clone https://github.com/your-repo/shadowflow.git
cd shadowflow

# 3. Запустите Docker развертывание
chmod +x deploy_docker.sh
./deploy_docker.sh
```

## 📋 Требования к серверу

### Минимальные требования:
- 💻 **CPU:** 2 ядра
- 🧠 **RAM:** 4GB
- 💾 **Диск:** 20GB SSD
- 🌐 **Сеть:** Стабильное интернет соединение
- 🐧 **ОС:** Ubuntu 20.04+ / Debian 11+

### Рекомендуемые требования:
- 💻 **CPU:** 4+ ядра
- 🧠 **RAM:** 8GB+
- 💾 **Диск:** 50GB+ SSD
- 🌐 **Сеть:** Выделенный IP, 100+ Mbps
- 🐧 **ОС:** Ubuntu 22.04 LTS

## 🔧 Ручное развертывание

### 1. Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка зависимостей
sudo apt install -y python3 python3-pip python3-venv nginx curl wget git build-essential cmake

# Установка Docker (опционально)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### 2. Настройка проекта

```bash
# Создание директории
mkdir -p /home/$USER/shadowflow
cd /home/$USER/shadowflow

# Копирование файлов
# (скопируйте все файлы проекта)

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### 3. Настройка systemd службы

```bash
# Создание службы
sudo tee /etc/systemd/system/shadowflow.service > /dev/null << EOF
[Unit]
Description=ShadowFlow - Polymarket Analysis System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/shadowflow
Environment=PATH=/home/$USER/shadowflow/venv/bin
ExecStart=/home/$USER/shadowflow/venv/bin/python /home/$USER/shadowflow/start_24_7.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Запуск службы
sudo systemctl daemon-reload
sudo systemctl enable shadowflow
sudo systemctl start shadowflow
```

### 4. Настройка Nginx

```bash
# Создание конфигурации
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
    }
}
EOF

# Активация сайта
sudo ln -sf /etc/nginx/sites-available/shadowflow /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

## 🐳 Docker развертывание

### 1. Создание Dockerfile

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential cmake curl wget git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p logs data static templates

EXPOSE 5001
ENV PYTHONUNBUFFERED=1
CMD ["python3", "start_24_7.py"]
```

### 2. Docker Compose

```yaml
version: '3.8'
services:
  shadowflow:
    build: .
    restart: unless-stopped
    ports:
      - "5001:5001"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - PYTHONUNBUFFERED=1
      - FLASK_ENV=production

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - shadowflow
```

### 3. Запуск

```bash
docker-compose up -d
```

## 🔒 Безопасность

### 1. Настройка файрвола

```bash
# UFW (Ubuntu)
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable

# iptables (альтернатива)
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -j DROP
```

### 2. SSL сертификаты

```bash
# Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 3. Обновления безопасности

```bash
# Автоматические обновления безопасности
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## 📊 Мониторинг

### 1. Логи системы

```bash
# Логи службы
sudo journalctl -u shadowflow -f

# Логи приложения
tail -f /home/$USER/shadowflow/logs/24_7.log

# Логи Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 2. Мониторинг ресурсов

```bash
# Использование ресурсов
htop
df -h
free -h

# Сетевые соединения
netstat -tulpn
ss -tulpn
```

### 3. Веб-мониторинг

- 🌐 **Главная:** http://your-server-ip
- ⚡ **Real-time:** http://your-server-ip/realtime
- 📡 **Мониторинг:** http://your-server-ip/monitoring

## 🔧 Обслуживание

### 1. Обновление системы

```bash
# Обновление кода
cd /home/$USER/shadowflow
git pull
source venv/bin/activate
pip install -r requirements.txt

# Перезапуск службы
sudo systemctl restart shadowflow
```

### 2. Резервное копирование

```bash
# Создание бэкапа
tar -czf shadowflow-backup-$(date +%Y%m%d).tar.gz \
    /home/$USER/shadowflow/data \
    /home/$USER/shadowflow/logs

# Восстановление
tar -xzf shadowflow-backup-YYYYMMDD.tar.gz
```

### 3. Масштабирование

```bash
# Горизонтальное масштабирование с Docker
docker-compose up -d --scale shadowflow=3

# Вертикальное масштабирование
# Увеличьте ресурсы сервера
```

## 🚨 Устранение неполадок

### Проблемы с запуском

```bash
# Проверка статуса
sudo systemctl status shadowflow

# Проверка логов
sudo journalctl -u shadowflow -n 50

# Проверка портов
sudo netstat -tulpn | grep 5001
```

### Проблемы с производительностью

```bash
# Мониторинг ресурсов
top
iotop
nethogs

# Оптимизация
# Увеличьте RAM/CPU
# Настройте кэширование
```

### Проблемы с сетью

```bash
# Проверка соединения
curl -I http://localhost:5001
curl -I http://your-server-ip

# Проверка DNS
nslookup your-domain.com
```

## 📈 Оптимизация

### 1. Производительность

- 🧠 **Увеличьте RAM** для ML моделей
- 💻 **Используйте SSD** для быстрого доступа к данным
- 🌐 **Настройте CDN** для статических файлов
- 📊 **Оптимизируйте запросы** к API

### 2. Надежность

- 🔄 **Настройте мониторинг** (Prometheus, Grafana)
- 📝 **Настройте алерты** (Email, Slack)
- 💾 **Настройте резервное копирование**
- 🛡️ **Настройте failover**

## 🎉 Готово!

После развертывания ваша система ShadowFlow будет работать 24/7 на сервере с:

- ✅ **Автоматическим перезапуском** при сбоях
- ✅ **Мониторингом здоровья** системы
- ✅ **Веб-интерфейсом** для управления
- ✅ **Логированием** всех событий
- ✅ **Масштабируемостью** под нагрузку

**Система готова к работе в продакшене!** 🚀

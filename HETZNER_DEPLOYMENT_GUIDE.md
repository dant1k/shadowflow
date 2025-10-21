# 🚀 Руководство по развертыванию ShadowFlow на сервере Hetzner

## 📋 Предварительные требования

### 1. Доступ к серверу
- **IP:** 46.62.233.6
- **Пользователь:** root
- **SSH ключ:** Нужно добавить публичный ключ на сервер

### 2. SSH ключ для развертывания
```bash
# Публичный ключ для добавления на сервер:
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJiGAMgMYFiMx6YHIHSX1k5WTAbZuRoqOKA9Sxqg6Out hetzner-deploy
```

## 🔧 Шаги развертывания

### Шаг 1: Подключение к серверу
```bash
# Добавьте публичный ключ на сервер через Hetzner Cloud Console
# или выполните на сервере:
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJiGAMgMYFiMx6YHIHSX1k5WTAbZuRoqOKA9Sxqg6Out hetzner-deploy" >> ~/.ssh/authorized_keys
```

### Шаг 2: Установка Docker
```bash
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

# Проверяем установку
docker --version
docker-compose --version
```

### Шаг 3: Создание директорий
```bash
mkdir -p /opt/shadowflow
mkdir -p /opt/shadowflow/data
mkdir -p /opt/shadowflow/logs
mkdir -p /opt/shadowflow/ssl
mkdir -p /opt/shadowflow/data/models
```

### Шаг 4: Создание docker-compose.yml
```bash
cd /opt/shadowflow

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
```

### Шаг 5: Создание nginx конфигурации
```bash
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
```

### Шаг 6: Запуск системы
```bash
# Запускаем контейнеры
docker-compose up -d

# Ждем запуска
sleep 30

# Проверяем статус
docker-compose ps
```

### Шаг 7: Проверка работы
```bash
# Проверяем API
curl -s http://localhost:5001/api/predictive/status

# Проверяем веб-интерфейс
curl -I http://localhost:5001

# Проверяем через nginx
curl -I http://localhost
```

## 🌐 Доступ к системе

После успешного развертывания система будет доступна по адресам:
- **Прямой доступ:** http://46.62.233.6:5001
- **Через nginx:** http://46.62.233.6

## 🔧 Управление системой

### Просмотр логов
```bash
cd /opt/shadowflow
docker-compose logs -f shadowflow
```

### Перезапуск
```bash
docker-compose restart
```

### Остановка
```bash
docker-compose down
```

### Обновление
```bash
docker-compose pull
docker-compose up -d
```

## 📊 Мониторинг

### Статус контейнеров
```bash
docker-compose ps
```

### Использование ресурсов
```bash
docker stats
```

### Логи системы
```bash
docker-compose logs --tail=50 shadowflow
```

## 🚨 Устранение неполадок

### Если контейнеры не запускаются
```bash
# Проверяем логи
docker-compose logs

# Перезапускаем
docker-compose down
docker-compose up -d
```

### Если API недоступен
```bash
# Проверяем порты
netstat -tlnp | grep :5001

# Проверяем контейнер
docker-compose ps
```

### Если nginx не работает
```bash
# Проверяем конфигурацию
nginx -t

# Перезапускаем nginx
docker-compose restart nginx
```

## 🎯 Автоматический скрипт

Если у вас есть доступ к серверу, можете использовать автоматический скрипт:

```bash
# Скачиваем и запускаем скрипт
curl -sSL https://raw.githubusercontent.com/your-repo/shadowflow/main/deploy_hetzner.sh | bash
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `docker-compose logs`
2. Проверьте статус: `docker-compose ps`
3. Проверьте ресурсы: `docker stats`
4. Перезапустите: `docker-compose restart`

---

**Статус:** 🟢 Готово к развертыванию  
**Версия:** 1.0.0  
**Дата:** 21 октября 2025

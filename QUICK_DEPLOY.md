# 🚀 Быстрое развертывание ShadowFlow на Hetzner

## 📋 Инструкция для выполнения на сервере

### 1. Подключитесь к серверу
```bash
# Через веб-консоль Hetzner или SSH
ssh root@46.62.233.6
```

### 2. Скопируйте и выполните команды

```bash
# Скачиваем и запускаем скрипт развертывания
curl -sSL https://raw.githubusercontent.com/your-repo/shadowflow/main/hetzner_manual_deploy.sh | bash
```

### Или выполните команды вручную:

```bash
# Обновляем систему
apt-get update -y

# Устанавливаем Docker
apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release wget unzip
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
systemctl start docker
systemctl enable docker

# Создаем директории
mkdir -p /opt/shadowflow
cd /opt/shadowflow

# Создаем docker-compose.yml
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
docker-compose up -d

# Ждем запуска
sleep 30

# Проверяем статус
docker-compose ps
```

### 3. Проверьте работу

```bash
# Проверяем API
curl -s http://localhost:5001/api/predictive/status

# Проверяем веб-интерфейс
curl -I http://localhost:5001
```

## 🌐 Доступ к системе

После успешного развертывания:
- **Прямой доступ:** http://46.62.233.6:5001
- **Через nginx:** http://46.62.233.6

## 🔧 Управление

```bash
cd /opt/shadowflow

# Логи
docker-compose logs -f shadowflow

# Перезапуск
docker-compose restart

# Остановка
docker-compose down

# Обновление
docker-compose pull && docker-compose up -d
```

---

**Готово!** 🎉 ShadowFlow будет развернут на вашем сервере Hetzner.

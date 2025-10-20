# 🚀 Руководство по развертыванию ShadowFlow на сервере

## 📋 Быстрый старт

### 1. Выберите VPS провайдера

#### 🌟 Рекомендуемые провайдеры:

**DigitalOcean** (рекомендуется)
- 💰 **Стоимость:** от $4/месяц
- 🚀 **Быстрая настройка**
- 📚 **Отличная документация**
- 🔗 **Регистрация:** https://digitalocean.com

**Vultr** (бюджетный вариант)
- 💰 **Стоимость:** от $2.50/месяц
- ⚡ **Высокая производительность**
- 🌍 **Много локаций**
- 🔗 **Регистрация:** https://vultr.com

**Hetzner** (европейский)
- 💰 **Стоимость:** от €3/месяц
- 🏆 **Лучшее соотношение цена/качество**
- 🔗 **Регистрация:** https://hetzner.com

### 2. Создайте VPS

#### Рекомендуемые характеристики:
- **OS:** Ubuntu 22.04 LTS
- **RAM:** 1-2 GB (минимум)
- **CPU:** 1-2 ядра
- **Диск:** 20-40 GB SSD
- **Сеть:** 1 TB трафика

### 3. Подключитесь к серверу

```bash
# Замените YOUR_SERVER_IP на IP вашего сервера
ssh root@YOUR_SERVER_IP
```

### 4. Загрузите код

```bash
# Установите Git
apt update && apt install -y git

# Клонируйте репозиторий (замените на ваш URL)
git clone https://github.com/YOUR_USERNAME/shadowflow.git
cd shadowflow

# Или загрузите архив
wget https://github.com/YOUR_USERNAME/shadowflow/archive/main.zip
unzip main.zip
cd shadowflow-main
```

## 🐳 Развертывание с Docker (рекомендуется)

### Автоматическое развертывание:

```bash
# Сделайте скрипт исполняемым
chmod +x deploy_docker.sh

# Запустите развертывание
./deploy_docker.sh
```

### Ручное развертывание:

```bash
# 1. Установите Docker и Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
apt install -y docker-compose

# 2. Создайте необходимые директории
mkdir -p logs data static templates certbot/conf certbot/www

# 3. Запустите контейнеры
docker-compose up -d

# 4. Проверьте статус
docker-compose ps
```

## 🔧 Развертывание без Docker

### Автоматическое развертывание:

```bash
# Сделайте скрипт исполняемым
chmod +x deploy.sh

# Запустите развертывание
sudo ./deploy.sh
```

### Ручное развертывание:

```bash
# 1. Установите зависимости
apt update
apt install -y python3 python3-pip python3-venv nginx curl git build-essential

# 2. Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Создайте пользователя
useradd -m -s /bin/bash shadowflow
chown -R shadowflow:shadowflow /path/to/shadowflow

# 4. Настройте systemd службу
cp shadowflow.service /etc/systemd/system/
systemctl daemon-reload
systemctl start shadowflow
systemctl enable shadowflow

# 5. Настройте Nginx
cp nginx.conf /etc/nginx/sites-available/shadowflow
ln -s /etc/nginx/sites-available/shadowflow /etc/nginx/sites-enabled/
systemctl restart nginx
```

## 🔐 Настройка SSL (опционально)

### С Let's Encrypt:

```bash
# Установите Certbot
apt install -y certbot python3-certbot-nginx

# Получите сертификат (замените your-domain.com)
certbot --nginx -d your-domain.com

# Настройте автообновление
crontab -e
# Добавьте строку:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 Проверка работы

### Проверьте статус:

```bash
# Docker
docker-compose ps
docker-compose logs -f

# Без Docker
systemctl status shadowflow
systemctl status nginx
```

### Откройте в браузере:

- **HTTP:** http://YOUR_SERVER_IP
- **HTTPS:** https://YOUR_SERVER_IP (если настроен SSL)

## 🔧 Управление системой

### Docker:

```bash
# Остановить
docker-compose down

# Перезапустить
docker-compose restart

# Обновить
git pull
docker-compose build
docker-compose up -d

# Просмотр логов
docker-compose logs -f shadowflow
```

### Без Docker:

```bash
# Остановить
systemctl stop shadowflow

# Запустить
systemctl start shadowflow

# Перезапустить
systemctl restart shadowflow

# Просмотр логов
journalctl -u shadowflow -f
```

## 🚨 Устранение неполадок

### Проблема: Контейнеры не запускаются

```bash
# Проверьте логи
docker-compose logs

# Проверьте порты
netstat -tlnp | grep :80
netstat -tlnp | grep :5001
```

### Проблема: Nginx 502 Bad Gateway

```bash
# Проверьте статус Flask
systemctl status shadowflow
# или
docker-compose logs shadowflow

# Проверьте конфигурацию Nginx
nginx -t
```

### Проблема: Нет данных

```bash
# Проверьте планировщик
docker-compose logs shadowflow | grep scheduler
# или
journalctl -u shadowflow | grep scheduler

# Проверьте кэш
ls -la data/cache.json
```

## 📈 Мониторинг

### Проверка ресурсов:

```bash
# Использование CPU и памяти
htop

# Использование диска
df -h

# Сетевой трафик
iftop
```

### Логи:

```bash
# Docker
docker-compose logs -f

# Systemd
journalctl -u shadowflow -f
journalctl -u nginx -f
```

## 🔄 Обновление системы

### Docker:

```bash
# 1. Остановите контейнеры
docker-compose down

# 2. Обновите код
git pull

# 3. Пересоберите и запустите
docker-compose build
docker-compose up -d
```

### Без Docker:

```bash
# 1. Остановите службу
systemctl stop shadowflow

# 2. Обновите код
git pull

# 3. Обновите зависимости
source venv/bin/activate
pip install -r requirements.txt

# 4. Запустите службу
systemctl start shadowflow
```

## 💡 Советы по оптимизации

### Производительность:

1. **Увеличьте RAM** до 2-4 GB для больших объемов данных
2. **Используйте SSD** для быстрого доступа к данным
3. **Настройте swap** файл для предотвращения OOM
4. **Ограничьте логи** чтобы не забить диск

### Безопасность:

1. **Настройте файрвол** (UFW)
2. **Используйте SSH ключи** вместо паролей
3. **Регулярно обновляйте** систему
4. **Настройте мониторинг** безопасности

## 🆘 Поддержка

Если у вас возникли проблемы:

1. **Проверьте логи** системы
2. **Убедитесь** что все порты открыты
3. **Проверьте** статус всех служб
4. **Создайте issue** в репозитории

---

## 🎉 Готово!

После успешного развертывания ваша система ShadowFlow будет работать 24/7 и автоматически обновлять данные с Polymarket!

**Доступ к системе:** http://YOUR_SERVER_IP

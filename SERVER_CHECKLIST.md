# ✅ Чек-лист развертывания ShadowFlow на сервере

## 🎯 Подготовка к развертыванию

### 1. Выбор VPS провайдера
- [ ] **DigitalOcean** (рекомендуется) - от $4/месяц
- [ ] **Vultr** (бюджетный) - от $2.50/месяц  
- [ ] **Hetzner** (европейский) - от €3/месяц
- [ ] **AWS EC2** - от $3.50/месяц

### 2. Создание VPS
- [ ] **OS:** Ubuntu 22.04 LTS
- [ ] **RAM:** минимум 1GB (рекомендуется 2GB)
- [ ] **CPU:** минимум 1 ядро (рекомендуется 2)
- [ ] **Диск:** минимум 20GB SSD
- [ ] **Сеть:** минимум 1TB трафика

### 3. Подключение к серверу
- [ ] Получен IP адрес сервера
- [ ] Настроен SSH доступ
- [ ] Проверено подключение: `ssh root@YOUR_SERVER_IP`

## 🐳 Развертывание с Docker (рекомендуется)

### Автоматическое развертывание:
- [ ] Загружен код на сервер
- [ ] Выполнен: `chmod +x deploy_docker.sh`
- [ ] Запущен: `./deploy_docker.sh`
- [ ] Проверен статус: `docker-compose ps`

### Ручное развертывание:
- [ ] Установлен Docker: `curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh`
- [ ] Установлен Docker Compose: `apt install -y docker-compose`
- [ ] Созданы директории: `mkdir -p logs data static templates certbot/conf certbot/www`
- [ ] Запущены контейнеры: `docker-compose up -d`
- [ ] Проверен статус: `docker-compose ps`

## 🔧 Развертывание без Docker

### Автоматическое развертывание:
- [ ] Загружен код на сервер
- [ ] Выполнен: `chmod +x deploy.sh`
- [ ] Запущен: `sudo ./deploy.sh`

### Ручное развертывание:
- [ ] Установлены зависимости: `apt update && apt install -y python3 python3-pip python3-venv nginx curl git build-essential`
- [ ] Создано виртуальное окружение: `python3 -m venv venv`
- [ ] Активировано окружение: `source venv/bin/activate`
- [ ] Обновлен pip: `pip install --upgrade pip`
- [ ] Установлены зависимости: `pip install -r requirements.txt`
- [ ] Создан пользователь: `useradd -m -s /bin/bash shadowflow`
- [ ] Настроены права: `chown -R shadowflow:shadowflow /path/to/shadowflow`
- [ ] Настроена systemd служба
- [ ] Запущена служба: `systemctl start shadowflow`
- [ ] Включен автозапуск: `systemctl enable shadowflow`
- [ ] Настроен Nginx
- [ ] Перезапущен Nginx: `systemctl restart nginx`

## 🔐 Настройка SSL (опционально)

- [ ] Установлен Certbot: `apt install -y certbot python3-certbot-nginx`
- [ ] Получен сертификат: `certbot --nginx -d your-domain.com`
- [ ] Настроено автообновление сертификата
- [ ] Проверен доступ по HTTPS

## 📊 Проверка работы

### Статус системы:
- [ ] **Docker:** `docker-compose ps` - все контейнеры в статусе "Up"
- [ ] **Без Docker:** `systemctl status shadowflow` - активен
- [ ] **Nginx:** `systemctl status nginx` - активен
- [ ] **Порты:** `netstat -tlnp | grep -E ":(80|443|5001)"` - открыты

### Веб-интерфейс:
- [ ] **HTTP:** http://YOUR_SERVER_IP - загружается
- [ ] **HTTPS:** https://YOUR_SERVER_IP - загружается (если настроен SSL)
- [ ] **API:** http://YOUR_SERVER_IP/api/scheduler-status - возвращает JSON
- [ ] **Real-time:** http://YOUR_SERVER_IP/realtime - загружается

### Данные:
- [ ] **Кэш:** `ls -la data/cache.json` - файл существует
- [ ] **Логи:** `ls -la logs/` - директория создана
- [ ] **Планировщик:** работает и обновляет данные
- [ ] **Кластеры:** система анализирует данные

## 🔧 Управление системой

### Docker команды:
- [ ] **Остановка:** `docker-compose down`
- [ ] **Запуск:** `docker-compose up -d`
- [ ] **Перезапуск:** `docker-compose restart`
- [ ] **Обновление:** `git pull && docker-compose build && docker-compose up -d`
- [ ] **Логи:** `docker-compose logs -f shadowflow`

### Systemd команды:
- [ ] **Остановка:** `systemctl stop shadowflow`
- [ ] **Запуск:** `systemctl start shadowflow`
- [ ] **Перезапуск:** `systemctl restart shadowflow`
- [ ] **Статус:** `systemctl status shadowflow`
- [ ] **Логи:** `journalctl -u shadowflow -f`

## 🚨 Устранение неполадок

### Проблемы с контейнерами:
- [ ] Проверены логи: `docker-compose logs`
- [ ] Проверены порты: `netstat -tlnp | grep -E ":(80|443|5001)"`
- [ ] Проверена конфигурация: `docker-compose config`
- [ ] Пересобраны контейнеры: `docker-compose build --no-cache`

### Проблемы с Nginx:
- [ ] Проверена конфигурация: `nginx -t`
- [ ] Проверены логи: `tail -f /var/log/nginx/error.log`
- [ ] Проверен статус: `systemctl status nginx`
- [ ] Перезапущен: `systemctl restart nginx`

### Проблемы с данными:
- [ ] Проверен планировщик в логах
- [ ] Проверен кэш: `ls -la data/cache.json`
- [ ] Проверены права доступа к файлам
- [ ] Запущен ручной анализ: `python3 -c "from analyzer.cluster import TradeClusterAnalyzer; TradeClusterAnalyzer().analyze_clusters()"`

## 📈 Мониторинг

### Ресурсы сервера:
- [ ] **CPU:** `htop` - использование в норме
- [ ] **Память:** `free -h` - достаточно свободной памяти
- [ ] **Диск:** `df -h` - достаточно места
- [ ] **Сеть:** `iftop` - трафик в норме

### Логи системы:
- [ ] **Docker:** `docker-compose logs -f`
- [ ] **Systemd:** `journalctl -u shadowflow -f`
- [ ] **Nginx:** `tail -f /var/log/nginx/access.log`
- [ ] **Система:** `tail -f /var/log/syslog`

## 🔄 Обновление системы

### Docker:
- [ ] Остановлены контейнеры: `docker-compose down`
- [ ] Обновлен код: `git pull`
- [ ] Пересобраны контейнеры: `docker-compose build`
- [ ] Запущены контейнеры: `docker-compose up -d`
- [ ] Проверен статус: `docker-compose ps`

### Без Docker:
- [ ] Остановлена служба: `systemctl stop shadowflow`
- [ ] Обновлен код: `git pull`
- [ ] Обновлены зависимости: `pip install -r requirements.txt`
- [ ] Запущена служба: `systemctl start shadowflow`
- [ ] Проверен статус: `systemctl status shadowflow`

## 💡 Оптимизация

### Производительность:
- [ ] Увеличена RAM до 2-4GB (при необходимости)
- [ ] Используется SSD диск
- [ ] Настроен swap файл
- [ ] Ограничены логи

### Безопасность:
- [ ] Настроен файрвол (UFW)
- [ ] Используются SSH ключи
- [ ] Регулярно обновляется система
- [ ] Настроен мониторинг безопасности

## 🎉 Финальная проверка

- [ ] **Система работает 24/7**
- [ ] **Данные обновляются каждые 5 минут**
- [ ] **Веб-интерфейс доступен**
- [ ] **API отвечает корректно**
- [ ] **Логи не показывают ошибок**
- [ ] **Ресурсы сервера в норме**

---

## ✅ Готово!

После выполнения всех пунктов чек-листа ваша система ShadowFlow будет полностью развернута и готова к работе 24/7!

**🌐 Доступ:** http://YOUR_SERVER_IP  
**📊 Мониторинг:** http://YOUR_SERVER_IP/realtime  
**🔧 Управление:** через Docker Compose или systemd

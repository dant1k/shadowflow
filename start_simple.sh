#!/bin/bash

# Простой скрипт для запуска ShadowFlow 24/7
# Без установки как службы

echo "🚀 Запуск ShadowFlow 24/7"
echo "========================="
echo ""

# Переходим в директорию проекта
cd /Users/Kos/shadowflow

# Создаем директорию для логов
mkdir -p logs

echo "📊 Проверка системы..."
echo ""

# Проверяем Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден"
    exit 1
fi
echo "✅ Python3 найден"

# Проверяем зависимости
if ! python3 -c "import flask, requests, pandas, sklearn" &> /dev/null; then
    echo "❌ Не все зависимости установлены"
    echo "💡 Запустите: pip install -r requirements.txt"
    exit 1
fi
echo "✅ Зависимости установлены"

# Проверяем интернет
if ! ping -c 1 polymarket.com &> /dev/null; then
    echo "⚠️ Нет подключения к Polymarket"
    echo "💡 Проверьте интернет соединение"
fi
echo "✅ Интернет соединение работает"

echo ""
echo "🚀 Запуск системы..."
echo ""

# Запускаем систему 24/7
python3 start_24_7.py

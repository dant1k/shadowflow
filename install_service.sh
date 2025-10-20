#!/bin/bash

# Скрипт для установки ShadowFlow как службы на macOS
# Использует launchd для автоматического запуска

echo "🚀 Установка ShadowFlow как службы 24/7"
echo "======================================="
echo ""

# Создаем plist файл для launchd
PLIST_FILE="$HOME/Library/LaunchAgents/com.shadowflow.plist"
SERVICE_SCRIPT="/Users/Kos/shadowflow/start_24_7.py"

echo "📝 Создание конфигурации службы..."

cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.shadowflow</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$SERVICE_SCRIPT</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>/Users/Kos/shadowflow</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>/Users/Kos/shadowflow/logs/service.log</string>
    
    <key>StandardErrorPath</key>
    <string>/Users/Kos/shadowflow/logs/service_error.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
EOF

echo "✅ Конфигурация создана: $PLIST_FILE"

# Создаем директорию для логов
mkdir -p /Users/Kos/shadowflow/logs

# Загружаем службу
echo "🔄 Загрузка службы..."
launchctl load "$PLIST_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Служба загружена успешно!"
    echo ""
    echo "🎯 УПРАВЛЕНИЕ СЛУЖБОЙ:"
    echo "====================="
    echo "Запуск:   launchctl start com.shadowflow"
    echo "Остановка: launchctl stop com.shadowflow"
    echo "Перезагрузка: launchctl unload $PLIST_FILE && launchctl load $PLIST_FILE"
    echo "Статус:   launchctl list | grep shadowflow"
    echo ""
    echo "📊 ЛОГИ:"
    echo "========"
    echo "Служба:   tail -f /Users/Kos/shadowflow/logs/service.log"
    echo "Ошибки:   tail -f /Users/Kos/shadowflow/logs/service_error.log"
    echo "24/7:     tail -f /Users/Kos/shadowflow/logs/24_7.log"
    echo ""
    echo "🌐 ВЕБ-ИНТЕРФЕЙС:"
    echo "=================="
    echo "Главная:  http://127.0.0.1:5001"
    echo "Real-time: http://127.0.0.1:5001/realtime"
    echo ""
    echo "🎉 СИСТЕМА УСТАНОВЛЕНА КАК СЛУЖБА 24/7!"
else
    echo "❌ Ошибка загрузки службы"
    exit 1
fi

#!/usr/bin/env python3
"""
Скрипт для запуска всей системы ShadowFlow
Запускает Flask приложение и WebSocket мониторинг
"""

import subprocess
import sys
import time
import signal
import os
from threading import Thread

def run_flask_app():
    """Запускает Flask приложение"""
    print("🌐 Запуск Flask приложения...")
    try:
        subprocess.run([sys.executable, "app.py"], cwd="/Users/Kos/shadowflow")
    except KeyboardInterrupt:
        print("⏹️  Flask приложение остановлено")

def run_websocket_monitor():
    """Запускает WebSocket мониторинг"""
    print("📡 Запуск WebSocket мониторинга...")
    try:
        subprocess.run([
            sys.executable, "-c", 
            "import asyncio; import sys; sys.path.append('/Users/Kos/shadowflow'); from monitoring.realtime_monitor import start_realtime_monitoring; asyncio.run(start_realtime_monitoring())"
        ], cwd="/Users/Kos/shadowflow")
    except KeyboardInterrupt:
        print("⏹️  WebSocket мониторинг остановлен")

def main():
    """Главная функция запуска системы"""
    print("🚀 Запуск системы ShadowFlow...")
    print("=" * 50)
    
    # Создаем потоки для запуска компонентов
    flask_thread = Thread(target=run_flask_app, daemon=True)
    websocket_thread = Thread(target=run_websocket_monitor, daemon=True)
    
    try:
        # Запускаем WebSocket мониторинг
        websocket_thread.start()
        time.sleep(2)  # Даем время на запуск WebSocket сервера
        
        # Запускаем Flask приложение
        flask_thread.start()
        
        print("\n✅ Система ShadowFlow запущена!")
        print("📊 Веб-интерфейс: http://localhost:5001")
        print("📡 WebSocket мониторинг: ws://localhost:8765")
        print("\n📋 Доступные страницы:")
        print("   • Дашборд: http://localhost:5001/")
        print("   • Кластеры: http://localhost:5001/clusters")
        print("   • AI Анализ: http://localhost:5001/ai-analysis")
        print("   • Анализ сетей: http://localhost:5001/network-analysis")
        print("   • Мониторинг: http://localhost:5001/monitoring")
        print("\n⏹️  Нажмите Ctrl+C для остановки")
        
        # Ожидаем завершения
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Остановка системы...")
        print("✅ Система ShadowFlow остановлена")

if __name__ == "__main__":
    main()

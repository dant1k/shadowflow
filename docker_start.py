#!/usr/bin/env python3
"""
Простой запуск ShadowFlow для Docker
"""

import os
import sys
import time
import threading
import subprocess
from datetime import datetime

def log(message):
    """Логирование"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def run_scheduler():
    """Запуск планировщика в отдельном потоке"""
    try:
        log("🚀 Запуск планировщика...")
        subprocess.run([sys.executable, "scheduler.py"], cwd="/app")
    except Exception as e:
        log(f"❌ Ошибка планировщика: {e}")

def main():
    """Основная функция"""
    log("🐳 ShadowFlow Docker запуск")
    log("==========================")
    
    # Создаем необходимые директории
    os.makedirs("/app/logs", exist_ok=True)
    os.makedirs("/app/data", exist_ok=True)
    
    # Запускаем планировщик в фоновом режиме
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Небольшая задержка для запуска планировщика
    time.sleep(2)
    
    # Запускаем Flask
    log("🚀 Запуск Flask сервера...")
    try:
        from app import app
        app.run(host='0.0.0.0', port=5001, debug=False)
    except Exception as e:
        log(f"❌ Ошибка Flask: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Система запуска ShadowFlow для работы 24/7
Автоматический перезапуск, мониторинг и восстановление
"""

import os
import sys
import time
import signal
import subprocess
import threading
import psutil
from datetime import datetime
import json
import requests

class ShadowFlow24_7:
    def __init__(self):
        self.flask_process = None
        self.scheduler_process = None
        self.is_running = False
        self.restart_count = 0
        self.max_restarts = 10
        self.restart_delay = 30  # секунд
        self.health_check_interval = 60  # секунд
        # Определяем путь к логам в зависимости от окружения
        if os.path.exists("/app"):
            # Docker окружение
            self.log_file = "/app/logs/24_7.log"
        else:
            # Локальное окружение
            self.log_file = "/Users/Kos/shadowflow/logs/24_7.log"
        
        # Создаем директорию для логов
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
    def log(self, message):
        """Записывает сообщение в лог"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_message + "\n")
        except:
            pass
    
    def start_flask(self):
        """Запускает Flask сервер"""
        try:
            self.log("🚀 Запуск Flask сервера...")
            self.flask_process = subprocess.Popen(
                [sys.executable, "app.py"],
                cwd="/app" if os.path.exists("/app") else "/Users/Kos/shadowflow",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Ждем запуска
            time.sleep(5)
            
            if self.flask_process.poll() is None:
                self.log("✅ Flask сервер запущен успешно")
                return True
            else:
                self.log("❌ Flask сервер не запустился")
                return False
                
        except Exception as e:
            self.log(f"❌ Ошибка запуска Flask: {e}")
            return False
    
    def start_scheduler(self):
        """Запускает планировщик"""
        try:
            self.log("🚀 Запуск планировщика...")
            self.scheduler_process = subprocess.Popen(
                [sys.executable, "scheduler.py"],
                cwd="/app" if os.path.exists("/app") else "/Users/Kos/shadowflow",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Ждем запуска
            time.sleep(3)
            
            if self.scheduler_process.poll() is None:
                self.log("✅ Планировщик запущен успешно")
                return True
            else:
                self.log("❌ Планировщик не запустился")
                return False
                
        except Exception as e:
            self.log(f"❌ Ошибка запуска планировщика: {e}")
            return False
    
    def check_flask_health(self):
        """Проверяет здоровье Flask сервера"""
        try:
            response = requests.get("http://127.0.0.1:5001/api/scheduler-status", timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def check_scheduler_health(self):
        """Проверяет здоровье планировщика"""
        try:
            # Проверяем, что процесс планировщика работает
            if self.scheduler_process and self.scheduler_process.poll() is None:
                return True
            return False
        except:
            return False
    
    def restart_flask(self):
        """Перезапускает Flask сервер"""
        self.log("🔄 Перезапуск Flask сервера...")
        
        if self.flask_process:
            try:
                self.flask_process.terminate()
                self.flask_process.wait(timeout=10)
            except:
                try:
                    self.flask_process.kill()
                except:
                    pass
        
        time.sleep(2)
        return self.start_flask()
    
    def restart_scheduler(self):
        """Перезапускает планировщик"""
        self.log("🔄 Перезапуск планировщика...")
        
        if self.scheduler_process:
            try:
                self.scheduler_process.terminate()
                self.scheduler_process.wait(timeout=10)
            except:
                try:
                    self.scheduler_process.kill()
                except:
                    pass
        
        time.sleep(2)
        return self.start_scheduler()
    
    def health_monitor(self):
        """Мониторинг здоровья системы"""
        while self.is_running:
            try:
                # Проверяем Flask
                if not self.check_flask_health():
                    self.log("⚠️ Flask сервер не отвечает, перезапускаем...")
                    if not self.restart_flask():
                        self.log("❌ Не удалось перезапустить Flask")
                        self.restart_count += 1
                
                # Проверяем планировщик
                if not self.check_scheduler_health():
                    self.log("⚠️ Планировщик не работает, перезапускаем...")
                    if not self.restart_scheduler():
                        self.log("❌ Не удалось перезапустить планировщик")
                        self.restart_count += 1
                
                # Проверяем количество перезапусков
                if self.restart_count >= self.max_restarts:
                    self.log(f"❌ Превышено максимальное количество перезапусков ({self.max_restarts})")
                    self.stop()
                    break
                
                time.sleep(self.health_check_interval)
                
            except Exception as e:
                self.log(f"❌ Ошибка в мониторе здоровья: {e}")
                time.sleep(self.health_check_interval)
    
    def start(self):
        """Запускает систему 24/7"""
        self.log("🚀 Запуск системы ShadowFlow 24/7...")
        self.is_running = True
        
        # Запускаем Flask
        if not self.start_flask():
            self.log("❌ Не удалось запустить Flask, завершаем работу")
            return False
        
        # Запускаем планировщик
        if not self.start_scheduler():
            self.log("❌ Не удалось запустить планировщик, завершаем работу")
            return False
        
        self.log("✅ Система запущена успешно!")
        self.log("🌐 Веб-интерфейс: http://127.0.0.1:5001")
        self.log("📊 Real-time мониторинг: http://127.0.0.1:5001/realtime")
        
        # Запускаем мониторинг в отдельном потоке
        monitor_thread = threading.Thread(target=self.health_monitor, daemon=True)
        monitor_thread.start()
        
        # Основной цикл
        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.log("⏹️ Получен сигнал остановки...")
            self.stop()
        
        return True
    
    def stop(self):
        """Останавливает систему"""
        self.log("⏹️ Остановка системы...")
        self.is_running = False
        
        if self.flask_process:
            try:
                self.flask_process.terminate()
                self.flask_process.wait(timeout=10)
                self.log("✅ Flask сервер остановлен")
            except:
                try:
                    self.flask_process.kill()
                    self.log("✅ Flask сервер принудительно остановлен")
                except:
                    pass
        
        if self.scheduler_process:
            try:
                self.scheduler_process.terminate()
                self.scheduler_process.wait(timeout=10)
                self.log("✅ Планировщик остановлен")
            except:
                try:
                    self.scheduler_process.kill()
                    self.log("✅ Планировщик принудительно остановлен")
                except:
                    pass
        
        self.log("✅ Система остановлена")
    
    def get_status(self):
        """Возвращает статус системы"""
        return {
            'is_running': self.is_running,
            'flask_running': self.check_flask_health(),
            'scheduler_running': self.check_scheduler_health(),
            'restart_count': self.restart_count,
            'uptime': time.time() - self.start_time if hasattr(self, 'start_time') else 0
        }

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    print("\n⏹️ Получен сигнал остановки...")
    if hasattr(signal_handler, 'system'):
        signal_handler.system.stop()
    sys.exit(0)

def main():
    """Основная функция"""
    print("🚀 ShadowFlow 24/7 System")
    print("=========================")
    print("")
    
    # Создаем систему
    system = ShadowFlow24_7()
    system.start_time = time.time()
    
    # Настраиваем обработчик сигналов
    signal_handler.system = system
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Запускаем систему
        system.start()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        system.stop()
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Планировщик для автоматического обновления данных Polymarket каждые 5 минут
"""

import time
import threading
import schedule
import requests
import json
import os
from datetime import datetime
from api.polymarket import PolymarketAPI
from analyzer.cluster import TradeClusterAnalyzer

class RealtimeDataScheduler:
    def __init__(self):
        self.api = PolymarketAPI()
        self.analyzer = TradeClusterAnalyzer()
        # Определяем путь к кэшу в зависимости от окружения
        if os.path.exists("/app"):
            # Docker окружение
            self.cache_file = "/app/data/cache.json"
        else:
            # Локальное окружение
            self.cache_file = "/Users/Kos/shadowflow/data/cache.json"
        self.is_running = False
        self.update_interval = 5  # минут
        
    def update_data(self):
        """Обновляет данные с Polymarket"""
        try:
            print(f"🔄 [{datetime.now().strftime('%H:%M:%S')}] Обновление данных...")
            
            # Получаем актуальные рынки
            markets = self.api.get_active_markets(limit=100)
            if not markets:
                print("❌ Не удалось получить рынки")
                return False
                
            print(f"✅ Получено {len(markets)} рынков")
            
            # Получаем сделки для каждого рынка
            all_trades = []
            for market in markets[:20]:  # Ограничиваем для производительности
                market_id = market.get('id', market.get('market_id', ''))
                if market_id:
                    try:
                        trades = self.api.get_market_trades(market_id, limit=50)
                        if trades:
                            all_trades.extend(trades)
                    except Exception as e:
                        print(f"⚠️ Ошибка при получении сделок для рынка {market_id}: {e}")
            
            print(f"✅ Получено {len(all_trades)} сделок")
            
            # Сохраняем в кэш
            cache_data = {
                'markets': markets,
                'trades': all_trades,
                'last_updated': datetime.now().isoformat(),
                'source': 'realtime_scheduler',
                'update_count': self.get_update_count() + 1
            }
            
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Данные сохранены в кэш")
            
            # Запускаем анализ кластеров
            try:
                self.analyzer.analyze_clusters()
                print("✅ Анализ кластеров завершен")
            except Exception as e:
                print(f"⚠️ Ошибка при анализе кластеров: {e}")
            
            # Отправляем уведомление через WebSocket
            self.notify_websocket_clients()
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при обновлении данных: {e}")
            return False
    
    def get_update_count(self):
        """Получает количество обновлений из кэша"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('update_count', 0)
        except:
            pass
        return 0
    
    def notify_websocket_clients(self):
        """Уведомляет WebSocket клиентов о новых данных"""
        try:
            # Отправляем уведомление на WebSocket сервер
            response = requests.post('http://127.0.0.1:5001/api/notify-update', 
                                  json={'type': 'data_updated', 'timestamp': datetime.now().isoformat()},
                                  timeout=5)
            if response.status_code == 200:
                print("✅ WebSocket клиенты уведомлены")
        except Exception as e:
            print(f"⚠️ Ошибка при уведомлении WebSocket: {e}")
    
    def start_scheduler(self):
        """Запускает планировщик"""
        if self.is_running:
            print("⚠️ Планировщик уже запущен")
            return
            
        print(f"🚀 Запуск планировщика обновления данных каждые {self.update_interval} минут")
        
        # Настраиваем расписание
        schedule.every(self.update_interval).minutes.do(self.update_data)
        
        # Первоначальное обновление
        print("🔄 Выполняем первоначальное обновление...")
        self.update_data()
        
        self.is_running = True
        
        # Запускаем в отдельном потоке
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        print("✅ Планировщик запущен")
    
    def stop_scheduler(self):
        """Останавливает планировщик"""
        self.is_running = False
        schedule.clear()
        print("⏹️ Планировщик остановлен")
    
    def get_status(self):
        """Возвращает статус планировщика"""
        return {
            'is_running': self.is_running,
            'update_interval': self.update_interval,
            'last_update': self.get_last_update_time(),
            'update_count': self.get_update_count()
        }
    
    def get_last_update_time(self):
        """Получает время последнего обновления"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('last_updated', 'Неизвестно')
        except:
            pass
        return 'Неизвестно'

def main():
    """Основная функция для запуска планировщика"""
    scheduler = RealtimeDataScheduler()
    
    try:
        scheduler.start_scheduler()
        
        print("\n🎯 Планировщик работает в фоновом режиме")
        print("📊 Данные обновляются каждые 5 минут")
        print("🌐 Веб-интерфейс доступен по адресу: http://127.0.0.1:5001")
        print("\n💡 Для остановки нажмите Ctrl+C")
        
        # Держим программу запущенной
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Остановка планировщика...")
        scheduler.stop_scheduler()
        print("✅ Планировщик остановлен")

if __name__ == "__main__":
    main()

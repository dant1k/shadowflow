#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы системы ShadowFlow
Проверяет все основные компоненты: API, анализ кластеризации, веб-интерфейс
"""

import sys
import os
import json
from datetime import datetime

# Добавляем текущую директорию в путь для импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.polymarket import PolymarketAPI
from analyzer.cluster import TradeClusterAnalyzer

def test_api_connection():
    """Тестирует подключение к API Polymarket"""
    print("🔗 Тестирование подключения к API Polymarket...")
    
    try:
        api = PolymarketAPI()
        
        # Тестируем получение активных рынков
        markets = api.get_active_markets(limit=5)
        if markets:
            print(f"✅ Получено {len(markets)} активных рынков")
            print(f"   Пример рынка: {markets[0].get('question', 'N/A')[:50]}...")
            return True
        else:
            print("❌ Не удалось получить активные рынки")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании API: {e}")
        return False

def test_data_collection():
    """Тестирует сбор данных о сделках"""
    print("\n📊 Тестирование сбора данных о сделках...")
    
    try:
        api = PolymarketAPI()
        
        # Проверяем, есть ли данные в кэше
        cached_trades = api.load_from_cache()
        
        if cached_trades:
            print(f"✅ Найдено {len(cached_trades)} сделок в кэше")
            
            # Показываем примеры данных
            if len(cached_trades) > 0:
                sample_trade = cached_trades[0]
                print(f"   Пример сделки:")
                print(f"   - Рынок: {sample_trade.get('market_name', 'N/A')}")
                print(f"   - Направление: {sample_trade.get('side', 'N/A')}")
                print(f"   - Объем: ${sample_trade.get('amount', 0):.2f}")
                print(f"   - Время: {sample_trade.get('datetime', 'N/A')}")
            
            return True
        else:
            print("⚠️  Нет данных в кэше. Создаем демо-данные...")
            # Создаем демо-данные для тестирования
            try:
                from create_demo_data import save_demo_data
                trades = save_demo_data()
                if trades:
                    print(f"✅ Создано {len(trades)} демо-сделок")
                    return True
                else:
                    print("❌ Не удалось создать демо-данные")
                    return False
            except Exception as e:
                print(f"❌ Ошибка при создании демо-данных: {e}")
                return False
            
    except Exception as e:
        print(f"❌ Ошибка при сборе данных: {e}")
        return False

def test_cluster_analysis():
    """Тестирует анализ кластеризации"""
    print("\n🔍 Тестирование анализа кластеризации...")
    
    try:
        analyzer = TradeClusterAnalyzer(sync_threshold_seconds=300)  # 5 минут для теста
        
        # Загружаем данные из кэша
        trades = analyzer.load_trades_data()
        
        if not trades:
            print("⚠️  Нет данных в кэше. Сначала запустите сбор данных.")
            return False
        
        print(f"📈 Анализ {len(trades)} сделок...")
        
        # Выполняем анализ
        clusters = analyzer.find_all_clusters()
        
        if clusters:
            print(f"✅ Найдено {len(clusters)} кластеров")
            
            # Показываем топ-3 кластера
            print("\n🏆 Топ-3 подозрительных кластера:")
            for i, cluster in enumerate(clusters[:3], 1):
                print(f"\n{i}. {cluster['market_name']}")
                print(f"   Направление: {cluster['side']}")
                print(f"   Синхронность: {cluster['sync_score']:.1f}%")
                print(f"   Кошельков: {cluster['wallets_count']}")
                print(f"   Сделок: {cluster['trades_count']}")
                print(f"   Объем: ${cluster['total_volume']:,.2f}")
                print(f"   Время: {cluster['time_window_str']}")
            
            # Создаем сводку
            summary = analyzer.get_cluster_summary(clusters)
            print(f"\n📊 Сводка:")
            print(f"   Общий объем: ${summary['total_volume']:,.2f}")
            print(f"   Уникальных кошельков: {summary['total_unique_wallets']}")
            print(f"   Средняя синхронность: {summary['avg_sync_score']:.1f}%")
            
            return True
        else:
            print("❌ Кластеры не найдены")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при анализе кластеризации: {e}")
        return False

def test_web_interface():
    """Тестирует доступность веб-интерфейса"""
    print("\n🌐 Тестирование веб-интерфейса...")
    
    try:
        # Проверяем наличие необходимых файлов
        required_files = [
            'app.py',
            'templates/base.html',
            'templates/index.html',
            'templates/clusters.html'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            print(f"❌ Отсутствуют файлы: {', '.join(missing_files)}")
            return False
        
        print("✅ Все файлы веб-интерфейса найдены")
        
        # Проверяем синтаксис Python файлов
        try:
            with open('app.py', 'r') as f:
                compile(f.read(), 'app.py', 'exec')
            print("✅ Синтаксис app.py корректен")
        except SyntaxError as e:
            print(f"❌ Ошибка синтаксиса в app.py: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании веб-интерфейса: {e}")
        return False

def test_data_directory():
    """Проверяет создание необходимых директорий"""
    print("\n📁 Проверка структуры директорий...")
    
    required_dirs = [
        'data',
        'templates',
        'static/css',
        'static/js'
    ]
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"✅ Создана директория: {dir_path}")
            except Exception as e:
                print(f"❌ Не удалось создать директорию {dir_path}: {e}")
                return False
        else:
            print(f"✅ Директория существует: {dir_path}")
    
    return True

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования системы ShadowFlow")
    print("=" * 50)
    
    tests = [
        ("Структура директорий", test_data_directory),
        ("Веб-интерфейс", test_web_interface),
        ("API подключение", test_api_connection),
        ("Сбор данных", test_data_collection),
        ("Анализ кластеризации", test_cluster_analysis)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    print("\n" + "=" * 50)
    print("📋 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nРезультат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("\n🎉 Все тесты пройдены! Система готова к работе.")
        print("\nДля запуска веб-интерфейса выполните:")
        print("python app.py")
        print("\nЗатем откройте браузер: http://localhost:5000")
    else:
        print(f"\n⚠️  {total - passed} тестов провалено. Проверьте ошибки выше.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

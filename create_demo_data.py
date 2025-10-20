#!/usr/bin/env python3
"""
Скрипт для создания демо-данных для тестирования системы ShadowFlow
Создает реалистичные данные о сделках с подозрительными паттернами
"""

import json
import random
import time
from datetime import datetime, timedelta
import os

def generate_demo_trades():
    """Генерирует демо-данные о сделках"""
    
    # Демо-рынки
    markets = [
        {
            'id': 'market_1',
            'name': 'Will Bitcoin reach $100,000 by end of 2024?',
            'question': 'Will Bitcoin reach $100,000 by end of 2024?'
        },
        {
            'id': 'market_2', 
            'name': 'Will Ethereum 2.0 upgrade complete successfully?',
            'question': 'Will Ethereum 2.0 upgrade complete successfully?'
        },
        {
            'id': 'market_3',
            'name': 'Will there be a major DeFi hack in 2024?',
            'question': 'Will there be a major DeFi hack in 2024?'
        },
        {
            'id': 'market_4',
            'name': 'Will AI regulation pass in the US in 2024?',
            'question': 'Will AI regulation pass in the US in 2024?'
        },
        {
            'id': 'market_5',
            'name': 'Will Tesla stock reach $300 by end of 2024?',
            'question': 'Will Tesla stock reach $300 by end of 2024?'
        }
    ]
    
    # Демо-кошельки
    wallets = [
        '0x1234567890abcdef1234567890abcdef12345678',
        '0xabcdef1234567890abcdef1234567890abcdef12',
        '0x9876543210fedcba9876543210fedcba98765432',
        '0xfedcba0987654321fedcba0987654321fedcba09',
        '0x1111222233334444555566667777888899990000',
        '0x0000999988887777666655554444333322221111',
        '0x5555666677778888999900001111222233334444',
        '0x4444333322221111000099998888777766665555',
        '0x9999888877776666555544443333222211110000',
        '0x0000111122223333444455556666777788889999'
    ]
    
    trades = []
    base_time = int(time.time()) - 3600  # 1 час назад
    
    # Создаем подозрительные кластеры
    for market in markets:
        # Случайные сделки
        for _ in range(random.randint(5, 15)):
            trade_time = base_time + random.randint(0, 3600)
            trades.append({
                'id': f'trade_{len(trades)}',
                'market_id': market['id'],
                'market_name': market['name'],
                'market_question': market['question'],
                'wallet': random.choice(wallets),
                'side': random.choice(['YES', 'NO']),
                'amount': random.uniform(100, 5000),
                'price': random.uniform(0.1, 0.9),
                'timestamp': trade_time,
                'datetime': datetime.fromtimestamp(trade_time).isoformat(),
                'outcome': random.choice(['YES', 'NO']),
                'market_outcomes': ['YES', 'NO']
            })
        
        # Создаем подозрительный кластер (синхронные сделки)
        cluster_wallets = random.sample(wallets, random.randint(3, 6))
        cluster_time = base_time + random.randint(1800, 3000)  # В середине периода
        side = random.choice(['YES', 'NO'])
        
        for i, wallet in enumerate(cluster_wallets):
            # Сделки в пределах 2-3 минут
            trade_time = cluster_time + random.randint(0, 180)
            trades.append({
                'id': f'cluster_trade_{len(trades)}',
                'market_id': market['id'],
                'market_name': market['name'],
                'market_question': market['question'],
                'wallet': wallet,
                'side': side,
                'amount': random.uniform(1000, 10000),  # Большие суммы
                'price': random.uniform(0.4, 0.6),  # Средние цены
                'timestamp': trade_time,
                'datetime': datetime.fromtimestamp(trade_time).isoformat(),
                'outcome': side,
                'market_outcomes': ['YES', 'NO']
            })
    
    return trades

def save_demo_data():
    """Сохраняет демо-данные в кэш"""
    trades = generate_demo_trades()
    
    # Сортируем по времени
    trades.sort(key=lambda x: x['timestamp'])
    
    cache_data = {
        'timestamp': datetime.now().isoformat(),
        'trades': trades,
        'count': len(trades)
    }
    
    # Создаем директорию data если её нет
    os.makedirs('/Users/Kos/shadowflow/data', exist_ok=True)
    
    cache_file = '/Users/Kos/shadowflow/data/cache.json'
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Создано {len(trades)} демо-сделок")
    print(f"📁 Данные сохранены в {cache_file}")
    
    # Показываем статистику
    markets = {}
    wallets = set()
    for trade in trades:
        market_name = trade['market_name']
        if market_name not in markets:
            markets[market_name] = 0
        markets[market_name] += 1
        wallets.add(trade['wallet'])
    
    print(f"\n📊 Статистика:")
    print(f"   Рынков: {len(markets)}")
    print(f"   Уникальных кошельков: {len(wallets)}")
    print(f"   Среднее количество сделок на рынок: {len(trades) / len(markets):.1f}")
    
    return trades

if __name__ == "__main__":
    print("🎭 Создание демо-данных для ShadowFlow...")
    trades = save_demo_data()
    print("\n🎉 Демо-данные готовы! Теперь можно запустить анализ.")

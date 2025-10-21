"""
Анализатор кластеризации для выявления координированных действий кошельков
Группирует сделки по времени, рынку и направлению для поиска синхронных операций
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Set, Tuple
from collections import defaultdict
import pandas as pd
from sklearn.cluster import DBSCAN
import numpy as np

class TradeClusterAnalyzer:
    def __init__(self, sync_threshold_seconds: int = 180):
        """
        Инициализация анализатора кластеризации
        
        Args:
            sync_threshold_seconds: Порог синхронности в секундах (по умолчанию 180 сек = 3 минуты)
        """
        self.sync_threshold = sync_threshold_seconds
        self.cache_file = "/app/data/cache.json"  # Правильный путь для Docker
    
    def load_trades_data(self) -> List[Dict]:
        """Загружает данные о сделках из кэша"""
        try:
            if not os.path.exists(self.cache_file):
                print("Файл кэша не найден")
                return []
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            trades = cache_data.get('trades', [])
            print(f"Загружено {len(trades)} сделок для анализа")
            return trades
            
        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")
            return []
    
    def group_trades_by_market_and_side(self, trades: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Группирует сделки по рынку и направлению (BUY/SELL)
        
        Returns:
            Dict с ключами вида "conditionId:side" и списками сделок
        """
        groups = defaultdict(list)
        
        for trade in trades:
            # Используем conditionId как market_id
            market_id = trade.get('conditionId', '')
            # Используем side (BUY/SELL)
            side = trade.get('side', '')
            
            if market_id and side in ['BUY', 'SELL']:
                key = f"{market_id}:{side}"
                groups[key].append(trade)
        
        print(f"Создано {len(groups)} групп по рынкам и направлениям")
        return dict(groups)
    
    def find_sync_clusters(self, trades_group: List[Dict]) -> List[List[Dict]]:
        """
        Находит кластеры синхронных сделок в группе
        
        Args:
            trades_group: Список сделок одного рынка и направления
            
        Returns:
            Список кластеров (каждый кластер - список сделок)
        """
        if len(trades_group) < 2:
            return []
        
        # Сортируем сделки по времени
        sorted_trades = sorted(trades_group, key=lambda x: x['timestamp'])
        
        clusters = []
        current_cluster = [sorted_trades[0]]
        
        for i in range(1, len(sorted_trades)):
            current_trade = sorted_trades[i]
            last_trade_in_cluster = current_cluster[-1]
            
            # Проверяем, попадает ли сделка в временное окно
            time_diff = current_trade['timestamp'] - last_trade_in_cluster['timestamp']
            
            if time_diff <= self.sync_threshold:
                # Добавляем в текущий кластер
                current_cluster.append(current_trade)
            else:
                # Сохраняем текущий кластер, если в нем больше одной сделки
                if len(current_cluster) > 1:
                    clusters.append(current_cluster)
                
                # Начинаем новый кластер
                current_cluster = [current_trade]
        
        # Добавляем последний кластер, если он содержит больше одной сделки
        if len(current_cluster) > 1:
            clusters.append(current_cluster)
        
        return clusters
    
    def analyze_cluster(self, cluster: List[Dict]) -> Dict:
        """
        Анализирует кластер и извлекает метаданные
        
        Args:
            cluster: Список сделок в кластере
            
        Returns:
            Словарь с метаданными кластера
        """
        if not cluster:
            return {}
        
        # Основные метрики
        wallets = list(set(trade['proxyWallet'] for trade in cluster))
        total_volume = sum(trade['size'] for trade in cluster)
        
        # Временные метрики
        timestamps = [trade['timestamp'] for trade in cluster]
        start_time = min(timestamps)
        end_time = max(timestamps)
        time_window = end_time - start_time
        
        # Информация о рынке
        market_info = cluster[0]
        market_name = market_info.get('title', 'Неизвестный рынок')
        market_question = market_info.get('title', '')
        side = market_info.get('side', '')
        market_id = market_info.get('conditionId', '')
        
        # Статистика по кошелькам
        wallet_stats = {}
        for trade in cluster:
            wallet = trade['proxyWallet']
            if wallet not in wallet_stats:
                wallet_stats[wallet] = {
                    'trades_count': 0,
                    'total_amount': 0,
                    'avg_price': 0
                }
            
            wallet_stats[wallet]['trades_count'] += 1
            wallet_stats[wallet]['total_amount'] += trade['size']
            wallet_stats[wallet]['avg_price'] = trade['price']
        
        # Форматируем временное окно
        if time_window < 60:
            time_window_str = f"{time_window}с"
        elif time_window < 3600:
            time_window_str = f"{time_window // 60}м {time_window % 60}с"
        else:
            hours = time_window // 3600
            minutes = (time_window % 3600) // 60
            time_window_str = f"{hours}ч {minutes}м"
        
        return {
            'market_id': market_id,
            'market_name': market_name,
            'market_question': market_question,
            'side': side,
            'wallets': wallets,
            'wallets_count': len(wallets),
            'trades_count': len(cluster),
            'total_volume': total_volume,
            'time_window_seconds': time_window,
            'time_window_str': time_window_str,
            'start_time': start_time,
            'end_time': end_time,
            'start_datetime': datetime.fromtimestamp(start_time).isoformat(),
            'end_datetime': datetime.fromtimestamp(end_time).isoformat(),
            'wallet_stats': wallet_stats,
            'avg_trade_size': total_volume / len(cluster),
            'sync_score': self.calculate_sync_score(cluster)
        }
    
    def calculate_sync_score(self, cluster: List[Dict]) -> float:
        """
        Вычисляет оценку синхронности кластера (0-100)
        
        Args:
            cluster: Список сделок в кластере
            
        Returns:
            Оценка синхронности от 0 до 100
        """
        if len(cluster) < 2:
            return 0.0
        
        # Факторы синхронности
        time_factor = 1.0 - (self.get_time_spread(cluster) / self.sync_threshold)
        volume_factor = min(1.0, sum(trade['size'] for trade in cluster) / 10000)  # Нормализация по объему
        wallet_diversity = len(set(trade['proxyWallet'] for trade in cluster)) / len(cluster)
        
        # Взвешенная оценка
        sync_score = (time_factor * 0.5 + volume_factor * 0.3 + wallet_diversity * 0.2) * 100
        
        return max(0.0, min(100.0, sync_score))
    
    def get_time_spread(self, cluster: List[Dict]) -> int:
        """Вычисляет разброс времени в кластере в секундах"""
        timestamps = [trade['timestamp'] for trade in cluster]
        return max(timestamps) - min(timestamps)
    
    def find_all_clusters(self) -> List[Dict]:
        """
        Основной метод для поиска всех кластеров координированных действий
        
        Returns:
            Список кластеров с метаданными
        """
        print("Начинаем анализ кластеризации...")
        
        # Загружаем данные
        trades = self.load_trades_data()
        if not trades:
            print("Нет данных для анализа")
            return []
        
        # Группируем по рынкам и направлениям
        groups = self.group_trades_by_market_and_side(trades)
        
        all_clusters = []
        
        for group_key, trades_group in groups.items():
            print(f"Анализируем группу: {group_key} ({len(trades_group)} сделок)")
            
            # Ищем кластеры в группе
            clusters = self.find_sync_clusters(trades_group)
            
            # Анализируем каждый кластер
            for cluster in clusters:
                cluster_analysis = self.analyze_cluster(cluster)
                if cluster_analysis:
                    all_clusters.append(cluster_analysis)
        
        # Сортируем по оценке синхронности
        all_clusters.sort(key=lambda x: x['sync_score'], reverse=True)
        
        print(f"Найдено {len(all_clusters)} кластеров координированных действий")
        return all_clusters
    
    def get_cluster_summary(self, clusters: List[Dict]) -> Dict:
        """
        Создает сводку по всем найденным кластерам
        
        Args:
            clusters: Список кластеров
            
        Returns:
            Словарь со статистикой
        """
        if not clusters:
            return {}
        
        total_volume = sum(cluster['total_volume'] for cluster in clusters)
        total_wallets = len(set(wallet for cluster in clusters for wallet in cluster['wallets']))
        avg_sync_score = sum(cluster['sync_score'] for cluster in clusters) / len(clusters)
        
        # Топ рынки по количеству кластеров
        market_clusters = defaultdict(int)
        for cluster in clusters:
            market_clusters[cluster['market_name']] += 1
        
        top_markets = sorted(market_clusters.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_clusters': len(clusters),
            'total_volume': total_volume,
            'total_unique_wallets': total_wallets,
            'avg_sync_score': avg_sync_score,
            'top_markets': top_markets,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def save_clusters_to_file(self, clusters: List[Dict], filename: str = None) -> None:
        """Сохраняет результаты анализа в файл"""
        if filename is None:
            filename = "/Users/Kos/shadowflow/data/clusters.json"
        
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            output_data = {
                'summary': self.get_cluster_summary(clusters),
                'clusters': clusters,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print(f"Результаты анализа сохранены в {filename}")
            
        except Exception as e:
            print(f"Ошибка при сохранении результатов: {e}")
    
    def analyze_clusters(self) -> List[Dict]:
        """Основной метод для анализа кластеров"""
        try:
            print("🔄 Запуск анализа кластеров...")
            clusters = self.find_all_clusters()
            
            if clusters:
                print(f"✅ Найдено {len(clusters)} кластеров")
                self.save_clusters_to_file(clusters)
                return clusters
            else:
                print("⚠️ Кластеры не найдены")
                return []
                
        except Exception as e:
            print(f"❌ Ошибка при анализе кластеров: {e}")
            return []

# Пример использования
if __name__ == "__main__":
    analyzer = TradeClusterAnalyzer(sync_threshold_seconds=180)
    
    # Находим все кластеры
    clusters = analyzer.find_all_clusters()
    
    # Показываем топ-5 кластеров
    print(f"\nТоп-5 кластеров координированных действий:")
    for i, cluster in enumerate(clusters[:5], 1):
        print(f"\n{i}. {cluster['market_name']}")
        print(f"   Направление: {cluster['side']}")
        print(f"   Кошельков: {cluster['wallets_count']}")
        print(f"   Сделок: {cluster['trades_count']}")
        print(f"   Объем: ${cluster['total_volume']:,.2f}")
        print(f"   Время: {cluster['time_window_str']}")
        print(f"   Синхронность: {cluster['sync_score']:.1f}%")
    
    # Сохраняем результаты
    analyzer.save_clusters_to_file(clusters)

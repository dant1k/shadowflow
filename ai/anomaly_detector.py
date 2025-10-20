"""
AI-анализатор аномалий для выявления подозрительных торговых паттернов
Использует машинное обучение для обнаружения необычных паттернов в данных
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from typing import List, Dict, Tuple
import json
from datetime import datetime, timedelta
from collections import defaultdict

class AnomalyDetector:
    def __init__(self):
        self.scaler = StandardScaler()
        self.isolation_forest = IsolationForest(
            contamination=0.1,  # 10% данных считаем аномальными
            random_state=42
        )
        self.dbscan = DBSCAN(eps=0.5, min_samples=5)
        
    def extract_features(self, trades: List[Dict]) -> np.ndarray:
        """Извлекает признаки из сделок для ML анализа"""
        features = []
        
        for trade in trades:
            # Безопасно извлекаем числовые значения
            amount = float(trade.get('amount', 0))
            price = float(trade.get('price', 0))
            timestamp = int(trade.get('timestamp', 0))
            wallet = str(trade.get('wallet', ''))
            market_id = str(trade.get('market_id', '0'))
            
            feature_vector = [
                amount,
                price,
                timestamp % 86400,  # Время дня в секундах
                len(wallet),  # Длина адреса кошелька
                hash(wallet) % 1000,  # Хэш кошелька
                hash(market_id) % 100,  # ID рынка (хэшируем строку)
            ]
            features.append(feature_vector)
        
        return np.array(features)
    
    def detect_anomalies(self, trades: List[Dict]) -> List[Dict]:
        """Обнаруживает аномальные сделки"""
        if len(trades) < 10:
            return []
        
        # Извлекаем признаки
        features = self.extract_features(trades)
        
        # Нормализуем данные
        features_scaled = self.scaler.fit_transform(features)
        
        # Применяем Isolation Forest
        anomaly_scores = self.isolation_forest.fit_predict(features_scaled)
        
        # Находим аномальные сделки
        anomalous_trades = []
        for i, (trade, score) in enumerate(zip(trades, anomaly_scores)):
            if score == -1:  # Аномальная сделка
                trade['anomaly_score'] = float(self.isolation_forest.decision_function([features_scaled[i]])[0])
                trade['is_anomaly'] = True
                anomalous_trades.append(trade)
            else:
                trade['anomaly_score'] = float(self.isolation_forest.decision_function([features_scaled[i]])[0])
                trade['is_anomaly'] = False
        
        return anomalous_trades
    
    def detect_wallet_clusters(self, trades: List[Dict]) -> Dict[str, List[Dict]]:
        """Обнаруживает кластеры связанных кошельков"""
        if len(trades) < 10:
            return {}
        
        # Группируем сделки по кошелькам
        wallet_trades = defaultdict(list)
        for trade in trades:
            wallet = trade.get('wallet', '')
            if wallet:
                wallet_trades[wallet].append(trade)
        
        # Извлекаем признаки для каждого кошелька
        wallet_features = []
        wallet_list = []
        
        for wallet, wallet_trade_list in wallet_trades.items():
            if len(wallet_trade_list) >= 3:  # Минимум 3 сделки
                feature_vector = [
                    len(wallet_trade_list),  # Количество сделок
                    sum(t['amount'] for t in wallet_trade_list),  # Общий объем
                    np.mean([t['amount'] for t in wallet_trade_list]),  # Средний размер
                    np.std([t['amount'] for t in wallet_trade_list]) if len(wallet_trade_list) > 1 else 0,  # Стандартное отклонение
                    len(set(t['market_id'] for t in wallet_trade_list)),  # Количество уникальных рынков
                    len(set(t['side'] for t in wallet_trade_list)),  # Разнообразие направлений
                ]
                wallet_features.append(feature_vector)
                wallet_list.append(wallet)
        
        if len(wallet_features) < 5:
            return {}
        
        # Применяем DBSCAN для кластеризации кошельков
        wallet_features_scaled = self.scaler.fit_transform(wallet_features)
        cluster_labels = self.dbscan.fit_predict(wallet_features_scaled)
        
        # Группируем кошельки по кластерам
        wallet_clusters = defaultdict(list)
        for wallet, label in zip(wallet_list, cluster_labels):
            if label != -1:  # Не шум
                wallet_clusters[f"cluster_{label}"].append(wallet)
        
        return dict(wallet_clusters)
    
    def analyze_temporal_patterns(self, trades: List[Dict]) -> Dict:
        """Анализирует временные паттерны в сделках"""
        if not trades:
            return {}
        
        # Группируем сделки по времени
        hourly_trades = defaultdict(int)
        daily_trades = defaultdict(int)
        
        for trade in trades:
            timestamp = trade.get('timestamp', 0)
            if timestamp:
                dt = datetime.fromtimestamp(timestamp)
                hour_key = dt.strftime('%H')
                day_key = dt.strftime('%A')
                
                hourly_trades[hour_key] += 1
                daily_trades[day_key] += 1
        
        # Находим пиковые часы и дни
        peak_hour = max(hourly_trades.items(), key=lambda x: x[1]) if hourly_trades else None
        peak_day = max(daily_trades.items(), key=lambda x: x[1]) if daily_trades else None
        
        # Вычисляем коэффициент вариации для определения регулярности
        hourly_values = list(hourly_trades.values())
        daily_values = list(daily_trades.values())
        
        hourly_cv = np.std(hourly_values) / np.mean(hourly_values) if hourly_values and np.mean(hourly_values) > 0 else 0
        daily_cv = np.std(daily_values) / np.mean(daily_values) if daily_values and np.mean(daily_values) > 0 else 0
        
        return {
            'hourly_distribution': dict(hourly_trades),
            'daily_distribution': dict(daily_trades),
            'peak_hour': peak_hour,
            'peak_day': peak_day,
            'hourly_regularity': float(1 - hourly_cv),  # Чем выше, тем регулярнее
            'daily_regularity': float(1 - daily_cv),
            'suspicious_pattern': bool(hourly_cv > 1.5 or daily_cv > 1.5)  # Высокая вариативность подозрительна
        }
    
    def detect_price_manipulation(self, trades: List[Dict]) -> Dict:
        """Обнаруживает возможные манипуляции с ценами"""
        if len(trades) < 10:
            return {'suspicious': False, 'reason': 'insufficient_data'}
        
        # Группируем по рынкам
        market_trades = defaultdict(list)
        for trade in trades:
            market_id = trade.get('market_id', '')
            if market_id:
                market_trades[market_id].append(trade)
        
        manipulation_signals = []
        
        for market_id, market_trade_list in market_trades.items():
            if len(market_trade_list) < 5:
                continue
            
            # Сортируем по времени
            sorted_trades = sorted(market_trade_list, key=lambda x: x.get('timestamp', 0))
            
            prices = [t.get('price', 0) for t in sorted_trades]
            amounts = [t.get('amount', 0) for t in sorted_trades]
            
            if not prices or not amounts:
                continue
            
            # Анализируем корреляцию между объемом и ценой
            price_volume_corr = np.corrcoef(prices, amounts)[0, 1] if len(prices) > 1 else 0
            
            # Анализируем волатильность цен
            price_volatility = np.std(prices) / np.mean(prices) if np.mean(prices) > 0 else 0
            
            # Анализируем распределение объемов
            large_trades = [a for a in amounts if a > np.percentile(amounts, 90)]
            large_trade_ratio = len(large_trades) / len(amounts)
            
            # Сигналы манипуляции
            signals = []
            if abs(price_volume_corr) > 0.7:
                signals.append(f"high_price_volume_correlation_{price_volume_corr:.2f}")
            
            if price_volatility > 0.3:
                signals.append(f"high_price_volatility_{price_volatility:.2f}")
            
            if large_trade_ratio > 0.3:
                signals.append(f"high_large_trade_ratio_{large_trade_ratio:.2f}")
            
            if signals:
                manipulation_signals.append({
                    'market_id': market_id,
                    'signals': signals,
                    'price_volume_corr': price_volume_corr,
                    'price_volatility': price_volatility,
                    'large_trade_ratio': large_trade_ratio
                })
        
        return {
            'suspicious': bool(len(manipulation_signals) > 0),
            'manipulation_signals': manipulation_signals,
            'total_markets_analyzed': len(market_trades),
            'suspicious_markets': len(manipulation_signals)
        }
    
    def comprehensive_analysis(self, trades: List[Dict]) -> Dict:
        """Комплексный анализ всех аномалий"""
        print("🔍 Запуск комплексного AI-анализа...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_trades': len(trades),
            'anomalies': {},
            'wallet_clusters': {},
            'temporal_patterns': {},
            'price_manipulation': {},
            'risk_score': 0.0
        }
        
        if len(trades) < 10:
            results['error'] = 'Недостаточно данных для анализа'
            return results
        
        # 1. Обнаружение аномальных сделок
        print("  📊 Анализ аномальных сделок...")
        anomalous_trades = self.detect_anomalies(trades)
        results['anomalies'] = {
            'count': len([t for t in anomalous_trades if t.get('is_anomaly', False)]),
            'percentage': len([t for t in anomalous_trades if t.get('is_anomaly', False)]) / len(trades) * 100,
            'top_anomalies': sorted([t for t in anomalous_trades if t.get('is_anomaly', False)], 
                                  key=lambda x: x.get('anomaly_score', 0))[:5]
        }
        
        # 2. Кластеризация кошельков
        print("  🔗 Анализ кластеров кошельков...")
        wallet_clusters = self.detect_wallet_clusters(trades)
        results['wallet_clusters'] = {
            'count': len(wallet_clusters),
            'clusters': wallet_clusters,
            'total_wallets_in_clusters': sum(len(wallets) for wallets in wallet_clusters.values())
        }
        
        # 3. Временные паттерны
        print("  ⏰ Анализ временных паттернов...")
        temporal_analysis = self.analyze_temporal_patterns(trades)
        results['temporal_patterns'] = temporal_analysis
        
        # 4. Манипуляции с ценами
        print("  💰 Анализ манипуляций с ценами...")
        price_analysis = self.detect_price_manipulation(trades)
        results['price_manipulation'] = price_analysis
        
        # 5. Общий риск-скор
        risk_factors = []
        
        # Аномалии (вес 30%)
        anomaly_risk = results['anomalies']['percentage'] / 10  # Нормализуем к 0-10
        risk_factors.append(('anomalies', anomaly_risk, 0.3))
        
        # Кластеры кошельков (вес 25%)
        cluster_risk = min(len(wallet_clusters) * 2, 10)  # Максимум 10
        risk_factors.append(('wallet_clusters', cluster_risk, 0.25))
        
        # Временные паттерны (вес 20%)
        temporal_risk = 10 if temporal_analysis.get('suspicious_pattern', False) else 0
        risk_factors.append(('temporal_patterns', temporal_risk, 0.2))
        
        # Манипуляции с ценами (вес 25%)
        price_risk = len(price_analysis.get('manipulation_signals', [])) * 3  # 3 балла за каждый сигнал
        risk_factors.append(('price_manipulation', min(price_risk, 10), 0.25))
        
        # Вычисляем общий риск-скор
        total_risk = sum(risk * weight for _, risk, weight in risk_factors)
        results['risk_score'] = min(total_risk, 100)  # Максимум 100
        results['risk_factors'] = risk_factors
        
        print(f"✅ AI-анализ завершен. Риск-скор: {results['risk_score']:.1f}/100")
        
        return results

# Пример использования
if __name__ == "__main__":
    detector = AnomalyDetector()
    
    # Загружаем данные из кэша
    try:
        with open('/Users/Kos/shadowflow/data/cache.json', 'r') as f:
            cache_data = json.load(f)
        trades = cache_data.get('trades', [])
        
        if trades:
            print(f"Анализируем {len(trades)} сделок...")
            results = detector.comprehensive_analysis(trades)
            
            print(f"\n📊 Результаты AI-анализа:")
            print(f"Риск-скор: {results['risk_score']:.1f}/100")
            print(f"Аномальных сделок: {results['anomalies']['count']} ({results['anomalies']['percentage']:.1f}%)")
            print(f"Кластеров кошельков: {results['wallet_clusters']['count']}")
            print(f"Подозрительные временные паттерны: {results['temporal_patterns'].get('suspicious_pattern', False)}")
            print(f"Рынков с манипуляциями: {results['price_manipulation'].get('suspicious_markets', 0)}")
        else:
            print("Нет данных для анализа")
            
    except Exception as e:
        print(f"Ошибка: {e}")

"""
Модуль предсказательной аналитики для ShadowFlow
Прогнозирование координированных атак, раннее предупреждение и риск-скоринг
"""

import json
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from collections import defaultdict, deque
import warnings
warnings.filterwarnings('ignore')

# ML библиотеки
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import classification_report, accuracy_score
    from sklearn.linear_model import LogisticRegression
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

class PredictiveAnalytics:
    def __init__(self, cache_file: str = None):
        """
        Инициализация модуля предсказательной аналитики
        
        Args:
            cache_file: Путь к файлу кэша с данными
        """
        if cache_file is None:
            if os.path.exists("/app"):
                # Docker окружение
                self.cache_file = "/app/data/cache.json"
            else:
                # Локальное окружение
                self.cache_file = "/Users/Kos/shadowflow/data/cache.json"
        else:
            self.cache_file = cache_file
            
        self.models = {}
        self.scalers = {}
        self.feature_history = deque(maxlen=1000)  # История признаков
        self.alert_history = deque(maxlen=100)     # История предупреждений
        self.models_trained = False                # Флаг обучения моделей
        self.cache_dir = os.path.join(os.path.dirname(self.cache_file), 'models')
        
        # Пороги для предупреждений
        self.risk_thresholds = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.8,
            'critical': 0.9
        }
        
        # Инициализация моделей
        self._initialize_models()
        
        # Создаем директорию для моделей
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Пытаемся загрузить сохраненные модели
        self._load_saved_models()
    
    def _initialize_models(self):
        """Инициализация ML моделей"""
        print("🧠 Инициализация моделей предсказательной аналитики...")
        
        if SKLEARN_AVAILABLE:
            self.models['random_forest'] = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            self.models['gradient_boosting'] = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=6,
                random_state=42
            )
            self.models['logistic_regression'] = LogisticRegression(
                random_state=42,
                max_iter=1000
            )
            self.scalers['standard'] = StandardScaler()
        
        if XGBOOST_AVAILABLE:
            self.models['xgboost'] = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
        
        if LIGHTGBM_AVAILABLE:
            self.models['lightgbm'] = lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
        
        print(f"✅ Загружено моделей: {len(self.models)}")
    
    def _save_models(self):
        """Сохраняет обученные модели"""
        try:
            import pickle
            
            for name, model in self.models.items():
                model_path = os.path.join(self.cache_dir, f"{name}_model.pkl")
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)
            
            # Сохраняем скейлеры
            for name, scaler in self.scalers.items():
                scaler_path = os.path.join(self.cache_dir, f"{name}_scaler.pkl")
                with open(scaler_path, 'wb') as f:
                    pickle.dump(scaler, f)
            
            # Сохраняем флаг обучения
            with open(os.path.join(self.cache_dir, 'trained.flag'), 'w') as f:
                f.write('trained')
            
            print("✅ Модели сохранены")
            
        except Exception as e:
            print(f"❌ Ошибка сохранения моделей: {e}")
    
    def _load_saved_models(self):
        """Загружает сохраненные модели"""
        try:
            import pickle
            
            # Проверяем, есть ли флаг обучения
            flag_path = os.path.join(self.cache_dir, 'trained.flag')
            if not os.path.exists(flag_path):
                return
            
            # Загружаем модели
            for name in self.models.keys():
                model_path = os.path.join(self.cache_dir, f"{name}_model.pkl")
                if os.path.exists(model_path):
                    with open(model_path, 'rb') as f:
                        self.models[name] = pickle.load(f)
            
            # Загружаем скейлеры
            for name in self.scalers.keys():
                scaler_path = os.path.join(self.cache_dir, f"{name}_scaler.pkl")
                if os.path.exists(scaler_path):
                    with open(scaler_path, 'rb') as f:
                        self.scalers[name] = pickle.load(f)
            
            self.models_trained = True
            print("✅ Сохраненные модели загружены")
            
        except Exception as e:
            print(f"❌ Ошибка загрузки моделей: {e}")
            self.models_trained = False
    
    def load_historical_data(self) -> pd.DataFrame:
        """Загружает исторические данные для обучения"""
        try:
            if not os.path.exists(self.cache_file):
                print("❌ Файл кэша не найден")
                return pd.DataFrame()
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            trades = cache_data.get('trades', [])
            if not trades:
                print("❌ Нет данных о сделках")
                return pd.DataFrame()
            
            # Конвертируем в DataFrame
            df = pd.DataFrame(trades)
            
            # Добавляем временные признаки
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
            
            print(f"✅ Загружено {len(df)} исторических сделок")
            return df
            
        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
            return pd.DataFrame()
    
    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Извлекает признаки для ML моделей"""
        try:
            features_df = pd.DataFrame()
            
            # Временные признаки
            if 'hour' in df.columns:
                features_df['hour'] = df['hour']
            if 'day_of_week' in df.columns:
                features_df['day_of_week'] = df['day_of_week']
            if 'is_weekend' in df.columns:
                features_df['is_weekend'] = df['is_weekend']
            
            # Торговые признаки
            features_df['price'] = df['price'].astype(float)
            features_df['size'] = df['size'].astype(float)
            features_df['volume'] = features_df['price'] * features_df['size']
            
            # Признаки рынка
            features_df['market_id'] = df['conditionId'].astype(str)
            features_df['outcome'] = df['outcome'].astype(str)
            features_df['outcome_encoded'] = (df['outcome'] == 'Up').astype(int)
            
            # Агрегированные признаки по рынку
            market_stats = df.groupby('conditionId').agg({
                'size': ['mean', 'std', 'count'],
                'price': ['mean', 'std'],
                'timestamp': ['min', 'max']
            }).fillna(0)
            
            market_stats.columns = ['_'.join(col).strip() for col in market_stats.columns]
            market_stats = market_stats.reset_index()
            
            # Объединяем с основными признаками
            features_df = features_df.merge(
                market_stats, 
                left_on='market_id', 
                right_on='conditionId', 
                how='left'
            )
            
            # Признаки активности кошельков
            wallet_stats = df.groupby('proxyWallet').agg({
                'size': ['mean', 'std', 'count'],
                'price': ['mean', 'std']
            }).fillna(0)
            
            wallet_stats.columns = ['wallet_' + '_'.join(col).strip() for col in wallet_stats.columns]
            wallet_stats = wallet_stats.reset_index()
            
            # Добавляем proxyWallet в features_df для merge
            features_df['proxyWallet'] = df['proxyWallet']
            
            features_df = features_df.merge(
                wallet_stats,
                left_on='proxyWallet',
                right_on='proxyWallet',
                how='left'
            )
            
            # Удаляем нечисловые колонки
            numeric_columns = features_df.select_dtypes(include=[np.number]).columns
            features_df = features_df[numeric_columns].fillna(0)
            
            print(f"✅ Извлечено {len(features_df.columns)} признаков")
            return features_df
            
        except Exception as e:
            print(f"❌ Ошибка извлечения признаков: {e}")
            return pd.DataFrame()
    
    def create_target_variable(self, df: pd.DataFrame) -> pd.Series:
        """Создает целевую переменную для обучения (координированные атаки)"""
        try:
            # Простая эвристика: координированная атака = много сделок одного кошелька за короткое время
            target = pd.Series(0, index=df.index)
            
            # Группируем по кошельку и времени
            df_sorted = df.sort_values(['proxyWallet', 'timestamp'])
            
            for wallet in df['proxyWallet'].unique():
                wallet_trades = df_sorted[df_sorted['proxyWallet'] == wallet]
                
                if len(wallet_trades) < 3:
                    continue
                
                # Проверяем временные интервалы
                time_diffs = wallet_trades['timestamp'].diff().dt.total_seconds()
                
                # Если много сделок за короткое время - помечаем как координированную
                rapid_trades = (time_diffs < 300).sum()  # 5 минут
                if rapid_trades >= 3:
                    target[wallet_trades.index] = 1
            
            print(f"✅ Создана целевая переменная: {target.sum()} координированных атак")
            return target
            
        except Exception as e:
            print(f"❌ Ошибка создания целевой переменной: {e}")
            return pd.Series(0, index=df.index)
    
    def train_models(self) -> Dict[str, float]:
        """Обучает все доступные модели"""
        try:
            print("🎯 Начало обучения моделей...")
            
            # Загружаем данные
            df = self.load_historical_data()
            if df.empty:
                return {}
            
            # Извлекаем признаки
            features = self.extract_features(df)
            if features.empty:
                return {}
            
            # Создаем целевую переменную
            target = self.create_target_variable(df)
            
            # Разделяем на train/test
            X_train, X_test, y_train, y_test = train_test_split(
                features, target, test_size=0.2, random_state=42, stratify=target
            )
            
            # Масштабируем признаки
            if 'standard' in self.scalers:
                X_train_scaled = self.scalers['standard'].fit_transform(X_train)
                X_test_scaled = self.scalers['standard'].transform(X_test)
            else:
                X_train_scaled = X_train
                X_test_scaled = X_test
            
            # Обучаем модели
            model_scores = {}
            
            for name, model in self.models.items():
                try:
                    print(f"🔄 Обучение модели: {name}")
                    
                    if name in ['logistic_regression'] and 'standard' in self.scalers:
                        model.fit(X_train_scaled, y_train)
                        y_pred = model.predict(X_test_scaled)
                    else:
                        model.fit(X_train, y_train)
                        y_pred = model.predict(X_test)
                    
                    score = accuracy_score(y_test, y_pred)
                    model_scores[name] = score
                    
                    print(f"✅ {name}: точность {score:.3f}")
                    
                except Exception as e:
                    print(f"❌ Ошибка обучения {name}: {e}")
                    model_scores[name] = 0.0
            
            print(f"✅ Обучение завершено. Лучшая модель: {max(model_scores, key=model_scores.get)}")
            
            # Сохраняем обученные модели
            self.models_trained = True
            self._save_models()
            
            return model_scores
            
        except Exception as e:
            print(f"❌ Ошибка обучения моделей: {e}")
            return {}
    
    def predict_coordinated_attacks(self, recent_trades: List[Dict]) -> Dict:
        """Прогнозирует вероятность координированных атак"""
        try:
            if not recent_trades or not self.models:
                return {'risk_level': 'unknown', 'probability': 0.0, 'details': 'Нет данных или моделей'}
            
            if not self.models_trained:
                return {'risk_level': 'unknown', 'probability': 0.0, 'details': 'Модели не обучены. Выполните обучение.'}
            
            # Конвертируем в DataFrame
            df = pd.DataFrame(recent_trades)
            
            # Обрабатываем timestamp
            if 'timestamp' in df.columns:
                if df['timestamp'].dtype == 'object':
                    # Если timestamp уже в формате datetime
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                else:
                    # Если timestamp в секундах
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                
                # Добавляем временные признаки
                df['hour'] = df['timestamp'].dt.hour
                df['day_of_week'] = df['timestamp'].dt.dayofweek
                df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
            
            # Извлекаем признаки
            features = self.extract_features(df)
            if features.empty:
                return {'risk_level': 'unknown', 'probability': 0.0, 'details': 'Не удалось извлечь признаки'}
            
            # Предсказания всех моделей
            predictions = {}
            probabilities = {}
            
            for name, model in self.models.items():
                try:
                    if name in ['logistic_regression'] and 'standard' in self.scalers:
                        features_scaled = self.scalers['standard'].transform(features)
                        pred = model.predict(features_scaled)
                        prob = model.predict_proba(features_scaled)[:, 1]
                    else:
                        pred = model.predict(features)
                        prob = model.predict_proba(features)[:, 1]
                    
                    predictions[name] = pred.mean()
                    probabilities[name] = prob.mean()
                    
                except Exception as e:
                    print(f"⚠️ Ошибка предсказания {name}: {e}")
                    predictions[name] = 0.0
                    probabilities[name] = 0.0
            
            # Усредняем предсказания
            avg_probability = float(np.mean(list(probabilities.values())))
            
            # Определяем уровень риска
            if avg_probability >= self.risk_thresholds['critical']:
                risk_level = 'critical'
            elif avg_probability >= self.risk_thresholds['high']:
                risk_level = 'high'
            elif avg_probability >= self.risk_thresholds['medium']:
                risk_level = 'medium'
            elif avg_probability >= self.risk_thresholds['low']:
                risk_level = 'low'
            else:
                risk_level = 'minimal'
            
            # Конвертируем все значения в Python типы
            predictions_clean = {k: float(v) for k, v in predictions.items()}
            probabilities_clean = {k: float(v) for k, v in probabilities.items()}
            
            return {
                'risk_level': risk_level,
                'probability': avg_probability,
                'model_predictions': predictions_clean,
                'model_probabilities': probabilities_clean,
                'details': f'Анализ {len(recent_trades)} сделок, {len(self.models)} моделей'
            }
            
        except Exception as e:
            print(f"❌ Ошибка прогнозирования: {e}")
            return {'risk_level': 'error', 'probability': 0.0, 'details': str(e)}
    
    def analyze_trends(self, days_back: int = 7) -> Dict:
        """Анализирует тренды и сезонные паттерны"""
        try:
            print(f"📈 Анализ трендов за последние {days_back} дней...")
            
            df = self.load_historical_data()
            if df.empty:
                return {}
            
            # Фильтруем по времени
            cutoff_date = datetime.now() - timedelta(days=days_back)
            df_recent = df[df['timestamp'] >= cutoff_date]
            
            if df_recent.empty:
                return {}
            
            trends = {}
            
            # Анализ по часам
            hourly_activity = df_recent.groupby(df_recent['timestamp'].dt.hour).size()
            trends['peak_hours'] = hourly_activity.nlargest(3).to_dict()
            trends['quiet_hours'] = hourly_activity.nsmallest(3).to_dict()
            
            # Анализ по дням недели
            daily_activity = df_recent.groupby(df_recent['timestamp'].dt.day_name()).size()
            trends['daily_patterns'] = daily_activity.to_dict()
            
            # Анализ объемов
            volume_trends = df_recent.groupby(df_recent['timestamp'].dt.date).agg({
                'size': ['sum', 'mean', 'count']
            })
            trends['volume_trends'] = {
                'total_volume': {str(k): v for k, v in volume_trends[('size', 'sum')].to_dict().items()},
                'avg_trade_size': {str(k): v for k, v in volume_trends[('size', 'mean')].to_dict().items()},
                'trade_count': {str(k): v for k, v in volume_trends[('size', 'count')].to_dict().items()}
            }
            
            # Анализ рынков
            market_activity = df_recent.groupby('conditionId').size().nlargest(5)
            trends['top_markets'] = market_activity.to_dict()
            
            print("✅ Анализ трендов завершен")
            return trends
            
        except Exception as e:
            print(f"❌ Ошибка анализа трендов: {e}")
            return {}
    
    def generate_early_warning(self, current_risk: Dict) -> Optional[Dict]:
        """Генерирует раннее предупреждение о подозрительной активности"""
        try:
            if current_risk['risk_level'] in ['high', 'critical']:
                warning = {
                    'timestamp': datetime.now().isoformat(),
                    'risk_level': current_risk['risk_level'],
                    'probability': current_risk['probability'],
                    'message': self._get_warning_message(current_risk),
                    'recommendations': self._get_recommendations(current_risk),
                    'severity': 'high' if current_risk['risk_level'] == 'critical' else 'medium'
                }
                
                # Добавляем в историю предупреждений
                self.alert_history.append(warning)
                
                print(f"🚨 Сгенерировано предупреждение: {warning['risk_level']}")
                return warning
            
            return None
            
        except Exception as e:
            print(f"❌ Ошибка генерации предупреждения: {e}")
            return None
    
    def _get_warning_message(self, risk: Dict) -> str:
        """Генерирует сообщение предупреждения"""
        if risk['risk_level'] == 'critical':
            return f"🚨 КРИТИЧЕСКИЙ РИСК! Обнаружена высокая вероятность координированной атаки ({risk['probability']:.1%})"
        elif risk['risk_level'] == 'high':
            return f"⚠️ ВЫСОКИЙ РИСК! Подозрительная активность обнаружена ({risk['probability']:.1%})"
        else:
            return f"ℹ️ Повышенная активность ({risk['probability']:.1%})"
    
    def _get_recommendations(self, risk: Dict) -> List[str]:
        """Генерирует рекомендации по снижению риска"""
        recommendations = []
        
        if risk['risk_level'] == 'critical':
            recommendations.extend([
                "Немедленно проанализировать подозрительные кошельки",
                "Усилить мониторинг соответствующих рынков",
                "Рассмотреть возможность приостановки торгов",
                "Уведомить команду безопасности"
            ])
        elif risk['risk_level'] == 'high':
            recommendations.extend([
                "Усилить мониторинг подозрительных активностей",
                "Проанализировать паттерны торгов",
                "Подготовить план действий на случай эскалации"
            ])
        else:
            recommendations.extend([
                "Продолжить мониторинг",
                "Отслеживать развитие ситуации"
            ])
        
        return recommendations
    
    def get_risk_score(self, recent_trades: List[Dict]) -> Dict:
        """Вычисляет риск-скор в реальном времени"""
        try:
            if not recent_trades:
                return {'score': 0.0, 'level': 'minimal', 'factors': []}
            
            factors = []
            total_score = 0.0
            
            # Фактор 1: Объем торгов
            total_volume = sum(trade.get('size', 0) for trade in recent_trades)
            volume_score = min(1.0, total_volume / 100000)  # Нормализация
            factors.append({'name': 'Объем торгов', 'score': volume_score, 'weight': 0.3})
            total_score += volume_score * 0.3
            
            # Фактор 2: Количество уникальных кошельков
            unique_wallets = len(set(trade.get('proxyWallet', '') for trade in recent_trades))
            wallet_score = min(1.0, unique_wallets / 10)  # Нормализация
            factors.append({'name': 'Активность кошельков', 'score': wallet_score, 'weight': 0.2})
            total_score += wallet_score * 0.2
            
            # Фактор 3: Временная концентрация
            if len(recent_trades) > 1:
                timestamps = [trade.get('timestamp', 0) for trade in recent_trades]
                if all(isinstance(ts, (int, float)) for ts in timestamps):
                    time_span = max(timestamps) - min(timestamps)
                    concentration_score = 1.0 - min(1.0, time_span / 3600)  # Чем меньше времени, тем выше риск
                    factors.append({'name': 'Временная концентрация', 'score': concentration_score, 'weight': 0.3})
                    total_score += concentration_score * 0.3
                else:
                    # Если timestamps не числовые, используем фиксированный score
                    factors.append({'name': 'Временная концентрация', 'score': 0.5, 'weight': 0.3})
                    total_score += 0.5 * 0.3
            
            # Фактор 4: Разнообразие рынков
            unique_markets = len(set(trade.get('conditionId', '') for trade in recent_trades))
            market_diversity_score = min(1.0, unique_markets / 5)
            factors.append({'name': 'Разнообразие рынков', 'score': market_diversity_score, 'weight': 0.2})
            total_score += market_diversity_score * 0.2
            
            # Определяем уровень риска
            if total_score >= 0.8:
                level = 'critical'
            elif total_score >= 0.6:
                level = 'high'
            elif total_score >= 0.4:
                level = 'medium'
            elif total_score >= 0.2:
                level = 'low'
            else:
                level = 'minimal'
            
            return {
                'score': round(total_score, 3),
                'level': level,
                'factors': factors,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Ошибка вычисления риск-скора: {e}")
            return {'score': 0.0, 'level': 'error', 'factors': [], 'error': str(e)}
    
    def get_analytics_summary(self) -> Dict:
        """Возвращает сводку по предсказательной аналитике"""
        return {
            'models_available': len(self.models),
            'model_names': list(self.models.keys()),
            'models_trained': self.models_trained,
            'recent_alerts': len(self.alert_history),
            'feature_history_size': len(self.feature_history),
            'risk_thresholds': self.risk_thresholds,
            'last_updated': datetime.now().isoformat()
        }

# Пример использования
if __name__ == "__main__":
    analytics = PredictiveAnalytics()
    
    # Обучаем модели
    scores = analytics.train_models()
    print(f"Результаты обучения: {scores}")
    
    # Анализируем тренды
    trends = analytics.analyze_trends()
    print(f"Тренды: {trends}")
    
    # Получаем сводку
    summary = analytics.get_analytics_summary()
    print(f"Сводка: {summary}")

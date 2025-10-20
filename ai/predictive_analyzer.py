import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import GradientBoostingClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
import os
import json
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Импортируем продвинутые ML модели
from .advanced_ml_models import AdvancedMLModels

class PredictiveAnalyzer:
    """
    Продвинутый модуль предсказательной аналитики для ShadowFlow
    Использует ML модели для прогнозирования координированных атак
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.models_dir = os.path.join(data_dir, "models")
        self.predictions_dir = os.path.join(data_dir, "predictions")
        
        # Создаем директории если не существуют
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.predictions_dir, exist_ok=True)
        
        # Инициализируем модели
        self.attack_classifier = None
        self.risk_regressor = None
        self.trend_analyzer = None
        self.scaler = StandardScaler()
        
        # Инициализируем продвинутые ML модели
        self.advanced_ml = AdvancedMLModels(data_dir)
        
        # Загружаем обученные модели если существуют
        self.load_models()
        
        # Пороги для алертов
        self.risk_thresholds = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.8,
            'critical': 0.9
        }
    
    def load_models(self):
        """Загружает предобученные модели"""
        try:
            if os.path.exists(os.path.join(self.models_dir, "attack_classifier.pkl")):
                self.attack_classifier = joblib.load(os.path.join(self.models_dir, "attack_classifier.pkl"))
                print("✅ Загружен классификатор атак")
            
            if os.path.exists(os.path.join(self.models_dir, "risk_regressor.pkl")):
                self.risk_regressor = joblib.load(os.path.join(self.models_dir, "risk_regressor.pkl"))
                print("✅ Загружен регрессор рисков")
            
            if os.path.exists(os.path.join(self.models_dir, "scaler.pkl")):
                self.scaler = joblib.load(os.path.join(self.models_dir, "scaler.pkl"))
                print("✅ Загружен скейлер")
                
        except Exception as e:
            print(f"⚠️ Ошибка загрузки моделей: {e}")
    
    def save_models(self):
        """Сохраняет обученные модели"""
        try:
            if self.attack_classifier:
                joblib.dump(self.attack_classifier, os.path.join(self.models_dir, "attack_classifier.pkl"))
            
            if self.risk_regressor:
                joblib.dump(self.risk_regressor, os.path.join(self.models_dir, "risk_regressor.pkl"))
            
            joblib.dump(self.scaler, os.path.join(self.models_dir, "scaler.pkl"))
            print("✅ Модели сохранены")
            
        except Exception as e:
            print(f"⚠️ Ошибка сохранения моделей: {e}")
    
    def extract_temporal_features(self, trades_data: List[Dict]) -> pd.DataFrame:
        """Извлекает временные признаки из данных о сделках"""
        if not trades_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(trades_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Временные признаки
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['day_of_month'] = df['timestamp'].dt.day
        df['month'] = df['timestamp'].dt.month
        
        # Агрегация по временным окнам
        features = []
        
        # По часам
        hourly = df.groupby('hour').agg({
            'amount': ['count', 'sum', 'mean', 'std'],
            'price': ['mean', 'std', 'min', 'max']
        }).fillna(0)
        hourly.columns = [f'hourly_{col[0]}_{col[1]}' for col in hourly.columns]
        features.append(hourly)
        
        # По дням недели
        daily = df.groupby('day_of_week').agg({
            'amount': ['count', 'sum', 'mean', 'std'],
            'price': ['mean', 'std', 'min', 'max']
        }).fillna(0)
        daily.columns = [f'daily_{col[0]}_{col[1]}' for col in daily.columns]
        features.append(daily)
        
        # По рынкам
        market = df.groupby('market_id').agg({
            'amount': ['count', 'sum', 'mean', 'std'],
            'price': ['mean', 'std', 'min', 'max']
        }).fillna(0)
        market.columns = [f'market_{col[0]}_{col[1]}' for col in market.columns]
        features.append(market)
        
        # Объединяем все признаки
        if features:
            result = pd.concat(features, axis=1).fillna(0)
            return result
        else:
            return pd.DataFrame()
    
    def extract_coordination_features(self, clusters_data: List[Dict]) -> pd.DataFrame:
        """Извлекает признаки координированной активности"""
        if not clusters_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(clusters_data)
        
        features = []
        
        # Признаки кластеров
        cluster_features = df.groupby('cluster_id').agg({
            'wallet_count': ['mean', 'std', 'max'],
            'total_volume': ['mean', 'std', 'max'],
            'sync_score': ['mean', 'std', 'max'],
            'time_window': ['mean', 'std', 'max']
        }).fillna(0)
        cluster_features.columns = [f'cluster_{col[0]}_{col[1]}' for col in cluster_features.columns]
        features.append(cluster_features)
        
        # Признаки кошельков
        wallet_features = df.groupby('wallets').agg({
            'wallet_count': ['mean', 'std', 'max'],
            'total_volume': ['mean', 'std', 'max'],
            'sync_score': ['mean', 'std', 'max']
        }).fillna(0)
        wallet_features.columns = [f'wallet_{col[0]}_{col[1]}' for col in wallet_features.columns]
        features.append(wallet_features)
        
        if features:
            result = pd.concat(features, axis=1).fillna(0)
            return result
        else:
            return pd.DataFrame()
    
    def create_training_data(self, trades_data: List[Dict], clusters_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Создает обучающие данные для ML моделей"""
        # Извлекаем признаки
        temporal_features = self.extract_temporal_features(trades_data)
        coordination_features = self.extract_coordination_features(clusters_data)
        
        if temporal_features.empty and coordination_features.empty:
            return np.array([]), np.array([])
        
        # Объединяем признаки
        if not temporal_features.empty and not coordination_features.empty:
            # Находим общие индексы
            common_index = temporal_features.index.intersection(coordination_features.index)
            if len(common_index) > 0:
                X = pd.concat([
                    temporal_features.loc[common_index],
                    coordination_features.loc[common_index]
                ], axis=1).fillna(0)
            else:
                X = pd.concat([temporal_features, coordination_features], axis=1).fillna(0)
        elif not temporal_features.empty:
            X = temporal_features.fillna(0)
        else:
            X = coordination_features.fillna(0)
        
        # Создаем целевые переменные
        # Для классификации: есть ли координированная атака
        y_classification = np.zeros(len(X))
        if not clusters_data:
            # Если есть кластеры, помечаем как атаки
            y_classification = np.ones(len(X))
        
        # Для регрессии: уровень риска (0-1)
        y_regression = np.random.uniform(0.1, 0.9, len(X))  # Заглушка
        
        return X.values, y_classification, y_regression
    
    def train_models(self, trades_data: List[Dict], clusters_data: List[Dict]):
        """Обучает ML модели на исторических данных"""
        print("🚀 Начинаем обучение моделей...")
        
        # Сначала обучаем продвинутые модели
        print("🤖 Обучаем продвинутые ML модели...")
        advanced_results = self.advanced_ml.train_advanced_models(trades_data, clusters_data)
        
        if advanced_results:
            print("✅ Продвинутые модели обучены успешно!")
            # Используем лучшие модели из продвинутых
            best_classifier = None
            best_regressor = None
            
            for name, result in advanced_results.items():
                if 'classification' in name and 'f1' in result:
                    if best_classifier is None or result['f1'] > best_classifier[1]:
                        best_classifier = (result['model'], result['f1'])
                elif 'regression' in name and 'r2' in result:
                    if best_regressor is None or result['r2'] > best_regressor[1]:
                        best_regressor = (result['model'], result['r2'])
            
            if best_classifier:
                self.attack_classifier = best_classifier[0]
                print(f"✅ Лучший классификатор: F1={best_classifier[1]:.3f}")
            
            if best_regressor:
                self.risk_regressor = best_regressor[0]
                print(f"✅ Лучший регрессор: R²={best_regressor[1]:.3f}")
        
        # Если продвинутые модели не сработали, обучаем базовые
        if not self.attack_classifier or not self.risk_regressor:
            print("🔄 Обучаем базовые модели...")
            X, y_class, y_reg = self.create_training_data(trades_data, clusters_data)
            
            if len(X) == 0:
                print("⚠️ Недостаточно данных для обучения")
                return
            
            # Разделяем на train/test
            X_train, X_test, y_class_train, y_class_test, y_reg_train, y_reg_test = train_test_split(
                X, y_class, y_reg, test_size=0.2, random_state=42
            )
            
            # Нормализуем данные
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Обучаем классификатор атак
            if not self.attack_classifier:
                print("📊 Обучаем классификатор атак...")
                self.attack_classifier = GradientBoostingClassifier(
                    n_estimators=100,
                    learning_rate=0.1,
                    max_depth=6,
                    random_state=42
                )
                self.attack_classifier.fit(X_train_scaled, y_class_train)
            
            # Обучаем регрессор рисков
            if not self.risk_regressor:
                print("📈 Обучаем регрессор рисков...")
                self.risk_regressor = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42
                )
                self.risk_regressor.fit(X_train_scaled, y_reg_train)
            
            # Оцениваем качество
            y_class_pred = self.attack_classifier.predict(X_test_scaled)
            y_reg_pred = self.risk_regressor.predict(X_test_scaled)
            
            accuracy = accuracy_score(y_class_test, y_class_pred)
            precision = precision_score(y_class_test, y_class_pred, zero_division=0)
            recall = recall_score(y_class_test, y_class_pred, zero_division=0)
            f1 = f1_score(y_class_test, y_class_pred, zero_division=0)
            
            mse = np.mean((y_reg_test - y_reg_pred) ** 2)
            mae = np.mean(np.abs(y_reg_test - y_reg_pred))
            
            print(f"✅ Классификатор: Accuracy={accuracy:.3f}, Precision={precision:.3f}, Recall={recall:.3f}, F1={f1:.3f}")
            print(f"✅ Регрессор: MSE={mse:.3f}, MAE={mae:.3f}")
        
        # Сохраняем модели
        self.save_models()
    
    def predict_attack_probability(self, trades_data: List[Dict], clusters_data: List[Dict]) -> float:
        """Предсказывает вероятность координированной атаки"""
        # Сначала пробуем продвинутые модели
        try:
            advanced_predictions = self.advanced_ml.predict_with_ensemble(trades_data, clusters_data)
            if advanced_predictions and 'attack_probability' in advanced_predictions:
                return advanced_predictions['attack_probability']
        except:
            pass
        
        # Если продвинутые модели не работают, используем базовые
        if not self.attack_classifier:
            return 0.5  # Заглушка если модель не обучена
        
        X, _, _ = self.create_training_data(trades_data, clusters_data)
        if len(X) == 0:
            return 0.5
        
        X_scaled = self.scaler.transform(X)
        if hasattr(self.attack_classifier, 'predict_proba'):
            probability = self.attack_classifier.predict_proba(X_scaled)[0][1]
        else:
            probability = self.attack_classifier.predict(X_scaled)[0]
        return float(probability)
    
    def predict_risk_level(self, trades_data: List[Dict], clusters_data: List[Dict]) -> float:
        """Предсказывает уровень риска (0-1)"""
        # Сначала пробуем продвинутые модели
        try:
            advanced_predictions = self.advanced_ml.predict_with_ensemble(trades_data, clusters_data)
            if advanced_predictions and 'risk_level' in advanced_predictions:
                return advanced_predictions['risk_level']
        except:
            pass
        
        # Если продвинутые модели не работают, используем базовые
        if not self.risk_regressor:
            return 0.5  # Заглушка если модель не обучена
        
        X, _, _ = self.create_training_data(trades_data, clusters_data)
        if len(X) == 0:
            return 0.5
        
        X_scaled = self.scaler.transform(X)
        risk = self.risk_regressor.predict(X_scaled)[0]
        return float(np.clip(risk, 0, 1))
    
    def analyze_trends(self, trades_data: List[Dict]) -> Dict:
        """Анализирует тренды в торговой активности"""
        if not trades_data:
            return {}
        
        df = pd.DataFrame(trades_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Анализ по времени
        hourly_volume = df.groupby(df['timestamp'].dt.hour)['amount'].sum()
        daily_volume = df.groupby(df['timestamp'].dt.date)['amount'].sum()
        
        # Анализ по рынкам
        market_volume = df.groupby('market_id')['amount'].sum().sort_values(ascending=False)
        
        # Анализ цен
        price_stats = df.groupby('market_id')['price'].agg(['mean', 'std', 'min', 'max'])
        
        trends = {
            'hourly_patterns': {
                'peak_hours': hourly_volume.nlargest(3).index.tolist(),
                'low_hours': hourly_volume.nsmallest(3).index.tolist(),
                'total_volume_by_hour': hourly_volume.to_dict()
            },
            'daily_patterns': {
                'volume_trend': daily_volume.tolist(),
                'dates': [str(d) for d in daily_volume.index]
            },
            'market_analysis': {
                'top_markets': market_volume.head(10).to_dict(),
                'price_volatility': price_stats['std'].to_dict()
            },
            'summary': {
                'total_trades': len(df),
                'total_volume': df['amount'].sum(),
                'avg_price': df['price'].mean(),
                'price_std': df['price'].std(),
                'unique_markets': df['market_id'].nunique(),
                'unique_wallets': df['wallet'].nunique()
            }
        }
        
        return trends
    
    def generate_early_warnings(self, trades_data: List[Dict], clusters_data: List[Dict]) -> List[Dict]:
        """Генерирует ранние предупреждения о потенциальных атаках"""
        warnings = []
        
        # Предсказываем вероятность атаки
        attack_prob = self.predict_attack_probability(trades_data, clusters_data)
        risk_level = self.predict_risk_level(trades_data, clusters_data)
        
        # Анализируем тренды
        trends = self.analyze_trends(trades_data)
        
        # Проверяем пороги
        if attack_prob > self.risk_thresholds['high']:
            warnings.append({
                'type': 'attack_probability',
                'level': 'high',
                'message': f'Высокая вероятность координированной атаки: {attack_prob:.1%}',
                'timestamp': datetime.now().isoformat(),
                'details': {
                    'probability': attack_prob,
                    'risk_level': risk_level
                }
            })
        
        if risk_level > self.risk_thresholds['critical']:
            warnings.append({
                'type': 'risk_level',
                'level': 'critical',
                'message': f'Критический уровень риска: {risk_level:.1%}',
                'timestamp': datetime.now().isoformat(),
                'details': {
                    'risk_level': risk_level,
                    'attack_probability': attack_prob
                }
            })
        
        # Проверяем аномальные паттерны
        if trends and 'hourly_patterns' in trends:
            peak_hours = trends['hourly_patterns']['peak_hours']
            if len(peak_hours) > 0:
                current_hour = datetime.now().hour
                if current_hour in peak_hours:
                    warnings.append({
                        'type': 'temporal_pattern',
                        'level': 'medium',
                        'message': f'Текущий час ({current_hour}:00) является пиковым для торговой активности',
                        'timestamp': datetime.now().isoformat(),
                        'details': {
                            'current_hour': current_hour,
                            'peak_hours': peak_hours
                        }
                    })
        
        return warnings
    
    def get_predictions_summary(self, trades_data: List[Dict], clusters_data: List[Dict]) -> Dict:
        """Возвращает сводку предсказаний"""
        attack_prob = self.predict_attack_probability(trades_data, clusters_data)
        risk_level = self.predict_risk_level(trades_data, clusters_data)
        trends = self.analyze_trends(trades_data)
        warnings = self.generate_early_warnings(trades_data, clusters_data)
        
        # Определяем уровень риска
        if risk_level >= self.risk_thresholds['critical']:
            risk_category = 'critical'
        elif risk_level >= self.risk_thresholds['high']:
            risk_category = 'high'
        elif risk_level >= self.risk_thresholds['medium']:
            risk_category = 'medium'
        else:
            risk_category = 'low'
        
        return {
            'attack_probability': attack_prob,
            'risk_level': risk_level,
            'risk_category': risk_category,
            'warnings_count': len(warnings),
            'warnings': warnings,
            'trends': trends,
            'timestamp': datetime.now().isoformat(),
            'model_status': {
                'classifier_loaded': self.attack_classifier is not None,
                'regressor_loaded': self.risk_regressor is not None,
                'scaler_loaded': self.scaler is not None
            }
        }
    
    def save_predictions(self, predictions: Dict, filename: str = None):
        """Сохраняет предсказания в файл"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"predictions_{timestamp}.json"
        
        filepath = os.path.join(self.predictions_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(predictions, f, ensure_ascii=False, indent=2)
            print(f"✅ Предсказания сохранены: {filepath}")
        except Exception as e:
            print(f"⚠️ Ошибка сохранения предсказаний: {e}")
    
    def load_latest_predictions(self) -> Optional[Dict]:
        """Загружает последние предсказания"""
        try:
            prediction_files = [f for f in os.listdir(self.predictions_dir) if f.startswith('predictions_')]
            if not prediction_files:
                return None
            
            latest_file = max(prediction_files)
            filepath = os.path.join(self.predictions_dir, latest_file)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"⚠️ Ошибка загрузки предсказаний: {e}")
            return None

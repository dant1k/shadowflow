import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import joblib
import os
import json
from typing import Dict, List, Tuple, Optional, Any
import warnings
warnings.filterwarnings('ignore')

# Продвинутые ML библиотеки
from sklearn.ensemble import (
    GradientBoostingClassifier, RandomForestRegressor, 
    VotingClassifier, StackingClassifier, AdaBoostClassifier
)
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import (
    train_test_split, cross_val_score, GridSearchCV, 
    StratifiedKFold, TimeSeriesSplit
)
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, mean_squared_error, mean_absolute_error,
    classification_report, confusion_matrix
)
from sklearn.pipeline import Pipeline
# from imblearn.over_sampling import SMOTE
# from imblearn.under_sampling import RandomUnderSampler
# from imblearn.pipeline import Pipeline as ImbPipeline

# Продвинутые градиентные бустинги
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
except Exception:
    LIGHTGBM_AVAILABLE = False

try:
    from catboost import CatBoostClassifier, CatBoostRegressor
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False
except Exception:
    CATBOOST_AVAILABLE = False

try:
    import optuna
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False

class AdvancedMLModels:
    """
    Продвинутый модуль ML моделей для ShadowFlow
    Включает ensemble методы, гиперпараметр тюнинг и продвинутые алгоритмы
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.models_dir = os.path.join(data_dir, "advanced_models")
        self.results_dir = os.path.join(data_dir, "ml_results")
        
        # Создаем директории
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Инициализируем модели
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_importance = {}
        self.model_performance = {}
        
        # Флаги доступности библиотек
        self.libs_available = {
            'xgboost': XGBOOST_AVAILABLE,
            'lightgbm': LIGHTGBM_AVAILABLE,
            'catboost': CATBOOST_AVAILABLE,
            'optuna': OPTUNA_AVAILABLE
        }
        
        print(f"📚 Доступные ML библиотеки: {[k for k, v in self.libs_available.items() if v]}")
    
    def create_advanced_features(self, trades_data: List[Dict], clusters_data: List[Dict]) -> pd.DataFrame:
        """Создает продвинутые признаки для ML моделей"""
        if not trades_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(trades_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Базовые признаки
        features = []
        
        # 1. Временные признаки
        df['hour'] = df['timestamp'].dt.hour.astype(float)
        df['day_of_week'] = df['timestamp'].dt.dayofweek.astype(float)
        df['day_of_month'] = df['timestamp'].dt.day.astype(float)
        df['month'] = df['timestamp'].dt.month.astype(float)
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int).astype(float)
        df['is_business_hours'] = df['hour'].between(9, 17).astype(int).astype(float)
        
        # 2. Статистические признаки по кошелькам
        wallet_stats = df.groupby('wallet').agg({
            'amount': ['count', 'sum', 'mean', 'std', 'min', 'max'],
            'price': ['mean', 'std', 'min', 'max'],
            'timestamp': ['min', 'max']
        }).fillna(0)
        wallet_stats.columns = [f'wallet_{col[0]}_{col[1]}' for col in wallet_stats.columns]
        
        # 3. Статистические признаки по рынкам
        market_stats = df.groupby('market_id').agg({
            'amount': ['count', 'sum', 'mean', 'std', 'min', 'max'],
            'price': ['mean', 'std', 'min', 'max'],
            'wallet': 'nunique'
        }).fillna(0)
        market_stats.columns = [f'market_{col[0]}_{col[1]}' for col in market_stats.columns]
        
        # 4. Признаки взаимодействия
        df['amount_price_interaction'] = df['amount'] * df['price']
        df['hour_day_interaction'] = df['hour'] * df['day_of_week']
        df['volume_intensity'] = df['amount'] / (df.groupby('market_id')['amount'].transform('mean') + 1e-6)
        
        # 5. Признаки аномальности
        for col in ['amount', 'price']:
            df[f'{col}_zscore'] = (df[col] - df[col].mean()) / (df[col].std() + 1e-6)
            df[f'{col}_is_outlier'] = (abs(df[f'{col}_zscore']) > 3).astype(int).astype(float)
        
        # 6. Временные окна (скользящие средние)
        df_sorted = df.sort_values('timestamp')
        for window in [5, 10, 30, 60]:  # минуты
            df_sorted[f'amount_ma_{window}'] = df_sorted['amount'].rolling(window=window, min_periods=1).mean()
            df_sorted[f'price_ma_{window}'] = df_sorted['price'].rolling(window=window, min_periods=1).mean()
            df_sorted[f'volume_ma_{window}'] = df_sorted['amount'].rolling(window=window, min_periods=1).sum()
        
        # 7. Признаки синхронности (если есть кластеры)
        if clusters_data:
            cluster_df = pd.DataFrame(clusters_data)
            # Проверяем наличие нужных колонок
            if 'cluster_id' in cluster_df.columns:
                cluster_features = cluster_df.groupby('cluster_id').agg({
                    'wallet_count': ['mean', 'std', 'max'],
                    'total_volume': ['mean', 'std', 'max'],
                    'sync_score': ['mean', 'std', 'max'],
                    'time_window': ['mean', 'std', 'max']
                }).fillna(0)
                cluster_features.columns = [f'cluster_{col[0]}_{col[1]}' for col in cluster_features.columns]
        
        # Объединяем все признаки
        feature_cols = [
            'hour', 'day_of_week', 'day_of_month', 'month', 'is_weekend', 'is_business_hours',
            'amount', 'price', 'amount_price_interaction', 'hour_day_interaction', 'volume_intensity',
            'amount_zscore', 'price_zscore', 'amount_is_outlier', 'price_is_outlier'
        ]
        
        # Добавляем скользящие средние
        ma_cols = [col for col in df_sorted.columns if col.startswith(('amount_ma_', 'price_ma_', 'volume_ma_'))]
        feature_cols.extend(ma_cols)
        
        # Создаем финальный датафрейм, исключая нечисловые колонки
        available_cols = [col for col in feature_cols if col in df_sorted.columns]
        final_df = df_sorted[available_cols].fillna(0)
        
        # Исключаем datetime и object колонки
        numeric_cols = final_df.select_dtypes(include=[np.number]).columns
        final_df = final_df[numeric_cols]
        
        # Убеждаемся, что все данные числовые
        for col in final_df.columns:
            if final_df[col].dtype == 'bool':
                final_df[col] = final_df[col].astype(float)
        
        # Конвертируем все в float для совместимости с ML моделями
        final_df = final_df.astype(float)
        
        # Добавляем статистики по кошелькам и рынкам
        if not wallet_stats.empty:
            wallet_features = df_sorted.merge(wallet_stats, left_on='wallet', right_index=True, how='left')
            wallet_cols = [col for col in wallet_features.columns if col.startswith('wallet_')]
            final_df = pd.concat([final_df, wallet_features[wallet_cols].fillna(0)], axis=1)
        
        if not market_stats.empty:
            market_features = df_sorted.merge(market_stats, left_on='market_id', right_index=True, how='left')
            market_cols = [col for col in market_features.columns if col.startswith('market_')]
            final_df = pd.concat([final_df, market_features[market_cols].fillna(0)], axis=1)
        
        return final_df.fillna(0)
    
    def create_target_variables(self, trades_data: List[Dict], clusters_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Создает целевые переменные для обучения"""
        if not trades_data:
            return np.array([]), np.array([])
        
        df = pd.DataFrame(trades_data)
        
        # Для классификации: есть ли координированная атака
        # Используем наличие кластеров как индикатор атак
        y_classification = np.zeros(len(df))
        
        if clusters_data:
            # Если есть кластеры, помечаем соответствующие сделки как атаки
            cluster_wallets = set()
            for cluster in clusters_data:
                if 'wallets' in cluster:
                    wallets = cluster['wallets'].split(',') if isinstance(cluster['wallets'], str) else cluster['wallets']
                    cluster_wallets.update(wallets)
            
            # Помечаем сделки от кошельков из кластеров как атаки
            y_classification = df['wallet'].isin(cluster_wallets).astype(int)
        
        # Для регрессии: уровень риска (0-1)
        # Используем комбинацию факторов
        risk_factors = []
        
        # Фактор 1: объем сделки относительно среднего
        avg_amount = df['amount'].mean()
        volume_factor = np.clip(df['amount'] / (avg_amount + 1e-6), 0, 2)
        
        # Фактор 2: время (ночные часы более подозрительны)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        hour_factor = np.where(df['timestamp'].dt.hour.between(0, 6), 1.5, 1.0)
        
        # Фактор 3: принадлежность к кластеру
        cluster_factor = y_classification * 1.5 + (1 - y_classification) * 0.5
        
        # Комбинируем факторы
        y_regression = np.clip(
            (volume_factor * hour_factor * cluster_factor) / 3.0, 
            0.1, 1.0
        )
        
        return y_classification, y_regression
    
    def create_ensemble_models(self) -> Dict[str, Any]:
        """Создает ensemble модели"""
        models = {}
        
        # 1. Базовые модели
        models['logistic'] = LogisticRegression(random_state=42, max_iter=1000)
        models['random_forest'] = RandomForestRegressor(n_estimators=100, random_state=42)
        models['gradient_boosting'] = GradientBoostingClassifier(n_estimators=100, random_state=42)
        models['svm'] = SVC(probability=True, random_state=42)
        models['neural_network'] = MLPClassifier(hidden_layer_sizes=(100, 50), random_state=42, max_iter=500)
        
        # 2. Продвинутые модели (если доступны)
        if self.libs_available['xgboost']:
            try:
                models['xgboost'] = xgb.XGBClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42,
                    eval_metric='logloss'
                )
                models['xgboost_reg'] = xgb.XGBRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42
                )
            except Exception as e:
                print(f"⚠️ XGBoost недоступен: {e}")
        
        if self.libs_available['lightgbm']:
            try:
                models['lightgbm'] = lgb.LGBMClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42,
                    verbose=-1
                )
                models['lightgbm_reg'] = lgb.LGBMRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42,
                    verbose=-1
                )
            except Exception as e:
                print(f"⚠️ LightGBM недоступен: {e}")
        
        if self.libs_available['catboost']:
            try:
                models['catboost'] = CatBoostClassifier(
                    iterations=100,
                    depth=6,
                    learning_rate=0.1,
                    random_state=42,
                    verbose=False
                )
                models['catboost_reg'] = CatBoostRegressor(
                    iterations=100,
                    depth=6,
                    learning_rate=0.1,
                    random_state=42,
                    verbose=False
                )
            except Exception as e:
                print(f"⚠️ CatBoost недоступен: {e}")
        
        # 3. Ensemble модели
        # Voting Classifier
        voting_models = [
            ('logistic', models['logistic']),
            ('gradient_boosting', models['gradient_boosting']),
            ('neural_network', models['neural_network'])
        ]
        
        if self.libs_available['xgboost']:
            voting_models.append(('xgboost', models['xgboost']))
        
        models['voting_classifier'] = VotingClassifier(
            estimators=voting_models,
            voting='soft'
        )
        
        # Stacking Classifier
        models['stacking_classifier'] = StackingClassifier(
            estimators=voting_models,
            final_estimator=LogisticRegression(),
            cv=3
        )
        
        return models
    
    def train_advanced_models(self, trades_data: List[Dict], clusters_data: List[Dict]) -> Dict[str, Any]:
        """Обучает продвинутые ML модели"""
        print("🚀 Начинаем обучение продвинутых ML моделей...")
        
        # Создаем признаки и целевые переменные
        X = self.create_advanced_features(trades_data, clusters_data)
        y_class, y_reg = self.create_target_variables(trades_data, clusters_data)
        
        if len(X) == 0 or len(y_class) == 0:
            print("⚠️ Недостаточно данных для обучения")
            return {}
        
        print(f"📊 Создано {X.shape[1]} признаков из {len(trades_data)} сделок")
        
        # Разделяем данные
        X_train, X_test, y_class_train, y_class_test, y_reg_train, y_reg_test = train_test_split(
            X, y_class, y_reg, test_size=0.2, random_state=42, stratify=y_class
        )
        
        # Нормализуем данные
        scaler = StandardScaler()
        
        # Убеждаемся, что данные числовые
        # Исключаем datetime колонки
        numeric_cols = X_train.select_dtypes(include=[np.number]).columns
        X_train = X_train[numeric_cols]
        X_test = X_test[numeric_cols]
        
        X_train = X_train.astype(float)
        X_test = X_test.astype(float)
        
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        self.scalers['main'] = scaler
        
        # Создаем модели
        models = self.create_ensemble_models()
        
        results = {}
        
        # Обучаем классификаторы
        print("📈 Обучаем классификаторы...")
        classification_models = {}
        
        # Базовые модели
        if 'logistic' in models:
            classification_models['logistic'] = models['logistic']
        if 'gradient_boosting' in models:
            classification_models['gradient_boosting'] = models['gradient_boosting']
        if 'neural_network' in models:
            classification_models['neural_network'] = models['neural_network']
        
        # Продвинутые модели
        if 'xgboost' in models:
            classification_models['xgboost'] = models['xgboost']
        if 'lightgbm' in models:
            classification_models['lightgbm'] = models['lightgbm']
        if 'catboost' in models:
            classification_models['catboost'] = models['catboost']
        
        # Ensemble модели
        if 'voting_classifier' in models:
            classification_models['voting_classifier'] = models['voting_classifier']
        if 'stacking_classifier' in models:
            classification_models['stacking_classifier'] = models['stacking_classifier']
        
        for name, model in classification_models.items():
            try:
                print(f"  🔄 Обучаем {name}...")
                model.fit(X_train_scaled, y_class_train)
                
                # Предсказания
                y_pred = model.predict(X_test_scaled)
                y_pred_proba = model.predict_proba(X_test_scaled)[:, 1] if hasattr(model, 'predict_proba') else y_pred
                
                # Метрики
                accuracy = accuracy_score(y_class_test, y_pred)
                precision = precision_score(y_class_test, y_pred, zero_division=0)
                recall = recall_score(y_class_test, y_pred, zero_division=0)
                f1 = f1_score(y_class_test, y_pred, zero_division=0)
                auc = roc_auc_score(y_class_test, y_pred_proba) if len(np.unique(y_class_test)) > 1 else 0
                
                results[f'{name}_classification'] = {
                    'model': model,
                    'accuracy': accuracy,
                    'precision': precision,
                    'recall': recall,
                    'f1': f1,
                    'auc': auc,
                    'predictions': y_pred,
                    'probabilities': y_pred_proba
                }
                
                print(f"    ✅ {name}: Accuracy={accuracy:.3f}, F1={f1:.3f}, AUC={auc:.3f}")
                
            except Exception as e:
                print(f"    ❌ {name}: {str(e)}")
        
        # Обучаем регрессоры
        print("📊 Обучаем регрессоры...")
        regression_models = {}
        
        # Базовые модели
        if 'random_forest' in models:
            regression_models['random_forest'] = models['random_forest']
        
        # Продвинутые модели
        if 'xgboost_reg' in models:
            regression_models['xgboost'] = models['xgboost_reg']
        if 'lightgbm_reg' in models:
            regression_models['lightgbm'] = models['lightgbm_reg']
        if 'catboost_reg' in models:
            regression_models['catboost'] = models['catboost_reg']
        
        # Ensemble модели
        if 'voting_regressor' in models:
            regression_models['voting_regressor'] = models['voting_regressor']
        
        for name, model in regression_models.items():
            try:
                print(f"  🔄 Обучаем {name}...")
                model.fit(X_train_scaled, y_reg_train)
                
                # Предсказания
                y_pred = model.predict(X_test_scaled)
                
                # Метрики
                mse = mean_squared_error(y_reg_test, y_pred)
                mae = mean_absolute_error(y_reg_test, y_pred)
                r2 = model.score(X_test_scaled, y_reg_test)
                
                results[f'{name}_regression'] = {
                    'model': model,
                    'mse': mse,
                    'mae': mae,
                    'r2': r2,
                    'predictions': y_pred
                }
                
                print(f"    ✅ {name}: MSE={mse:.3f}, MAE={mae:.3f}, R²={r2:.3f}")
                
            except Exception as e:
                print(f"    ❌ {name}: {str(e)}")
        
        # Сохраняем результаты
        self.model_performance = results
        self.save_models()
        
        print("🎉 Обучение завершено!")
        return results
    
    def predict_with_ensemble(self, trades_data: List[Dict], clusters_data: List[Dict]) -> Dict[str, float]:
        """Делает предсказания с использованием ensemble моделей"""
        if not self.model_performance:
            return {'attack_probability': 0.5, 'risk_level': 0.5}
        
        # Создаем признаки
        X = self.create_advanced_features(trades_data, clusters_data)
        if len(X) == 0:
            return {'attack_probability': 0.5, 'risk_level': 0.5}
        
        # Убеждаемся, что признаки соответствуют обученным
        # Исключаем datetime и object колонки
        numeric_cols = X.select_dtypes(include=[np.number]).columns
        X = X[numeric_cols]
        X = X.astype(float)
        
        # Нормализуем
        if 'main' in self.scalers:
            X_scaled = self.scalers['main'].transform(X)
        else:
            X_scaled = X.values
        
        # Предсказания классификаторов
        attack_probs = []
        for name, result in self.model_performance.items():
            if 'classification' in name and 'model' in result:
                try:
                    if hasattr(result['model'], 'predict_proba'):
                        prob = result['model'].predict_proba(X_scaled)[:, 1].mean()
                    else:
                        prob = result['model'].predict(X_scaled).mean()
                    attack_probs.append(prob)
                except:
                    continue
        
        # Предсказания регрессоров
        risk_levels = []
        for name, result in self.model_performance.items():
            if 'regression' in name and 'model' in result:
                try:
                    risk = result['model'].predict(X_scaled).mean()
                    risk_levels.append(risk)
                except:
                    continue
        
        # Усредняем предсказания
        attack_probability = np.mean(attack_probs) if attack_probs else 0.5
        risk_level = np.mean(risk_levels) if risk_levels else 0.5
        
        return {
            'attack_probability': float(np.clip(attack_probability, 0, 1)),
            'risk_level': float(np.clip(risk_level, 0, 1))
        }
    
    def save_models(self):
        """Сохраняет обученные модели"""
        try:
            for name, result in self.model_performance.items():
                if 'model' in result:
                    model_path = os.path.join(self.models_dir, f"{name}.pkl")
                    joblib.dump(result['model'], model_path)
            
            # Сохраняем скейлеры
            for name, scaler in self.scalers.items():
                scaler_path = os.path.join(self.models_dir, f"scaler_{name}.pkl")
                joblib.dump(scaler, scaler_path)
            
            # Сохраняем метрики
            metrics_path = os.path.join(self.results_dir, "model_performance.json")
            metrics_data = {}
            for name, result in self.model_performance.items():
                metrics_data[name] = {
                    k: v for k, v in result.items() 
                    if k != 'model' and k != 'predictions' and k != 'probabilities'
                }
            
            with open(metrics_path, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            
            print("✅ Модели сохранены")
            
        except Exception as e:
            print(f"⚠️ Ошибка сохранения моделей: {e}")
    
    def load_models(self):
        """Загружает обученные модели"""
        try:
            # Загружаем метрики
            metrics_path = os.path.join(self.results_dir, "model_performance.json")
            if os.path.exists(metrics_path):
                with open(metrics_path, 'r') as f:
                    metrics_data = json.load(f)
                
                # Загружаем модели
                for name in metrics_data.keys():
                    model_path = os.path.join(self.models_dir, f"{name}.pkl")
                    if os.path.exists(model_path):
                        model = joblib.load(model_path)
                        self.model_performance[name] = {
                            'model': model,
                            **metrics_data[name]
                        }
                
                print(f"✅ Загружено {len(self.model_performance)} моделей")
            
            # Загружаем скейлеры
            for scaler_file in os.listdir(self.models_dir):
                if scaler_file.startswith('scaler_'):
                    scaler_name = scaler_file.replace('scaler_', '').replace('.pkl', '')
                    scaler_path = os.path.join(self.models_dir, scaler_file)
                    self.scalers[scaler_name] = joblib.load(scaler_path)
                
        except Exception as e:
            print(f"⚠️ Ошибка загрузки моделей: {e}")
    
    def get_model_summary(self) -> Dict[str, Any]:
        """Возвращает сводку по моделям"""
        if not self.model_performance:
            return {'models_loaded': 0, 'best_classifier': None, 'best_regressor': None}
        
        # Находим лучшие модели
        best_classifier = None
        best_classifier_score = 0
        
        best_regressor = None
        best_regressor_score = float('inf')
        
        for name, result in self.model_performance.items():
            if 'classification' in name:
                if 'f1' in result and result['f1'] > best_classifier_score:
                    best_classifier = name
                    best_classifier_score = result['f1']
            elif 'regression' in name:
                if 'mse' in result and result['mse'] < best_regressor_score:
                    best_regressor = name
                    best_regressor_score = result['mse']
        
        return {
            'models_loaded': len(self.model_performance),
            'best_classifier': best_classifier,
            'best_regressor': best_regressor,
            'available_libraries': self.libs_available,
            'model_details': {
                name: {k: v for k, v in result.items() if k != 'model'}
                for name, result in self.model_performance.items()
            }
        }

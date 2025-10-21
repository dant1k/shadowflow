"""
ShadowFlow - Система анализа координированных действий на Polymarket
Веб-приложение Flask для визуализации результатов анализа кластеризации
"""

from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime
from analyzer.cluster import TradeClusterAnalyzer
from analyzer.predictive_analytics import PredictiveAnalytics
from api.polymarket import PolymarketAPI
from ai.anomaly_detector import AnomalyDetector
from ai.predictive_analyzer import PredictiveAnalyzer
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'shadowflow-secret-key-2024'

# Инициализация компонентов
analyzer = TradeClusterAnalyzer(sync_threshold_seconds=180)
api = PolymarketAPI()
ai_detector = AnomalyDetector()
predictive_analyzer = PredictiveAnalyzer()
predictive_analytics = PredictiveAnalytics()

# WebSocket клиенты для уведомлений
websocket_clients = []

@app.route('/')
def index():
    """Главная страница с дашбордом"""
    return render_template('index.html')

@app.route('/api/clusters')
def get_clusters():
    """API endpoint для получения кластеров"""
    try:
        clusters = analyzer.find_all_clusters()
        return jsonify({
            'success': True,
            'clusters': clusters,
            'count': len(clusters)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/summary')
def get_summary():
    """API endpoint для получения сводки по кластерам"""
    try:
        clusters = analyzer.find_all_clusters()
        summary = analyzer.get_cluster_summary(clusters)
        return jsonify({
            'success': True,
            'summary': summary
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/update-data-old')
def update_data_old():
    """API endpoint для обновления данных (старая версия)"""
    try:
        hours_back = request.args.get('hours', 6, type=int)
        trades = api.update_trades_data(hours_back)
        
        return jsonify({
            'success': True,
            'trades_count': len(trades),
            'message': f'Обновлено {len(trades)} сделок за последние {hours_back} часов'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/clusters')
def clusters_page():
    """Страница с детальным просмотром кластеров"""
    return render_template('clusters.html')

@app.route('/ai-analysis')
def ai_analysis_page():
    """Страница с AI-анализом аномалий"""
    return render_template('ai_analysis.html')

@app.route('/network-analysis')
def network_analysis_page():
    """Страница с анализом сетей кошельков"""
    return render_template('network_analysis.html')

@app.route('/monitoring')
def monitoring_page():
    """Страница real-time мониторинга"""
    return render_template('monitoring.html')

@app.route('/realtime')
def realtime():
    """Страница мониторинга реального времени"""
    return render_template('realtime.html')

@app.route('/predictions')
def predictions_page():
    """Страница с предсказательной аналитикой"""
    return render_template('predictions.html')

@app.route('/early-warnings')
def early_warnings_page():
    """Страница с ранними предупреждениями"""
    return render_template('early_warnings.html')

@app.route('/api/cluster/<int:cluster_id>')
def get_cluster_details(cluster_id):
    """API endpoint для получения деталей конкретного кластера"""
    try:
        clusters = analyzer.find_all_clusters()
        if 0 <= cluster_id < len(clusters):
            return jsonify({
                'success': True,
                'cluster': clusters[cluster_id]
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Кластер не найден'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/markets')
def get_markets():
    """API endpoint для получения списка рынков"""
    try:
        markets = api.get_active_markets(limit=100)
        return jsonify({
            'success': True,
            'markets': markets
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ai-analysis')
def get_ai_analysis():
    """API endpoint для получения AI-анализа аномалий"""
    try:
        # Создаем новый экземпляр API с правильным путем к кэшу
        from api.polymarket import PolymarketAPI
        api_instance = PolymarketAPI()
        api_instance.cache_file = '/app/data/cache.json'  # Правильный путь для Docker
        
        # Загружаем данные из кэша
        trades = api_instance.load_from_cache()
        if not trades:
            return jsonify({
                'success': False,
                'error': 'Нет данных для анализа'
            }), 400
        
        # Выполняем AI-анализ
        analysis_results = ai_detector.comprehensive_analysis(trades)
        
        return jsonify({
            'success': True,
            'analysis': analysis_results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/anomalies')
def get_anomalies():
    """API endpoint для получения аномальных сделок"""
    try:
        # Создаем новый экземпляр API с правильным путем к кэшу
        from api.polymarket import PolymarketAPI
        api_instance = PolymarketAPI()
        api_instance.cache_file = '/app/data/cache.json'  # Правильный путь для Docker
        
        trades = api_instance.load_from_cache()
        if not trades:
            return jsonify({
                'success': False,
                'error': 'Нет данных для анализа'
            }), 400
        
        anomalous_trades = ai_detector.detect_anomalies(trades)
        suspicious_trades = [t for t in anomalous_trades if t.get('is_anomaly', False)]
        
        return jsonify({
            'success': True,
            'anomalies': suspicious_trades,
            'count': len(suspicious_trades),
            'total_trades': len(trades)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/wallet-clusters')
def get_wallet_clusters():
    """API endpoint для получения кластеров кошельков"""
    try:
        trades = api.load_from_cache()
        if not trades:
            return jsonify({
                'success': False,
                'error': 'Нет данных для анализа'
            }), 400
        
        wallet_clusters = ai_detector.detect_wallet_clusters(trades)
        
        return jsonify({
            'success': True,
            'clusters': wallet_clusters,
            'count': len(wallet_clusters)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/predictions')
def get_predictions():
    """API endpoint для получения предсказаний"""
    try:
        trades = api.load_from_cache()
        clusters = analyzer.find_all_clusters()
        
        if not trades:
            return jsonify({
                'success': False,
                'error': 'Нет данных для анализа'
            }), 400
        
        # Получаем предсказания
        predictions = predictive_analyzer.get_predictions_summary(trades, clusters)
        
        return jsonify({
            'success': True,
            'predictions': predictions
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/early-warnings')
def get_early_warnings():
    """API endpoint для получения ранних предупреждений"""
    try:
        trades = api.load_from_cache()
        clusters = analyzer.find_all_clusters()
        
        if not trades:
            return jsonify({
                'success': False,
                'error': 'Нет данных для анализа'
            }), 400
        
        # Генерируем ранние предупреждения
        warnings = predictive_analyzer.generate_early_warnings(trades, clusters)
        
        return jsonify({
            'success': True,
            'warnings': warnings,
            'count': len(warnings)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/trends')
def get_trends():
    """API endpoint для получения анализа трендов"""
    try:
        trades = api.load_from_cache()
        
        if not trades:
            return jsonify({
                'success': False,
                'error': 'Нет данных для анализа'
            }), 400
        
        # Анализируем тренды
        trends = predictive_analyzer.analyze_trends(trades)
        
        return jsonify({
            'success': True,
            'trends': trends
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/train-models')
def train_models():
    """API endpoint для обучения ML моделей"""
    try:
        trades = api.load_from_cache()
        clusters = analyzer.find_all_clusters()
        
        if not trades:
            return jsonify({
                'success': False,
                'error': 'Нет данных для обучения'
            }), 400
        
        # Обучаем модели
        predictive_analyzer.train_models(trades, clusters)
        
        return jsonify({
            'success': True,
            'message': 'Модели успешно обучены'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ml-models')
def get_ml_models():
    """API endpoint для получения информации о ML моделях"""
    try:
        # Получаем сводку по продвинутым моделям
        model_summary = predictive_analyzer.advanced_ml.get_model_summary()
        
        return jsonify({
            'success': True,
            'models': model_summary
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/market-info/<market_id>')
def api_market_info(market_id):
    """API endpoint для получения информации о конкретном рынке"""
    try:
        # Создаем новый экземпляр API с правильным путем к кэшу
        from api.polymarket import PolymarketAPI
        api_instance = PolymarketAPI()
        api_instance.cache_file = '/app/data/cache.json'  # Правильный путь для Docker
        
        market_info = api_instance.get_market_info(market_id)
        return jsonify({
            'success': True,
            'market': market_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/polymarket/events')
def get_polymarket_events():
    """API endpoint для получения актуальных событий Polymarket"""
    try:
        import requests
        import time
        
        # Проверяем кэш
        cache_file = '/app/data/polymarket_events_cache.json'
        cache_duration = 300  # 5 минут
        
        # Загружаем кэш если существует
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                if time.time() - cache_data.get('timestamp', 0) < cache_duration:
                    return jsonify({
                        'success': True,
                        'events': cache_data.get('events', []),
                        'cached': True
                    })
        
        # Получаем данные из Gamma API (более надежно)
        url = "https://gamma-api.polymarket.com/markets"
        params = {
            'limit': 100,  # Увеличиваем лимит для лучшей фильтрации
            'active': 'true',
            'order': 'volume',
            'ascending': 'false'
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'Gamma API error: {response.status_code}'
            }), 500
        
        data = response.json()
        markets = data if isinstance(data, list) else data.get('markets', [])
        
        # Фильтруем только активные рынки и форматируем
        events = []
        for market in markets:
            question = market.get('question', '')
            slug = market.get('slug', '')
            volume = market.get('volume', 0)
            liquidity = market.get('liquidity', 0)
            end_date = market.get('endDate', market.get('end_date', ''))
            
            # Проверяем, что событие актуальное (не старше 1 года)
            if end_date:
                try:
                    from datetime import datetime, timedelta
                    # Исправляем парсинг даты
                    if end_date.endswith('Z'):
                        event_date = datetime.fromisoformat(end_date[:-1] + '+00:00')
                    else:
                        event_date = datetime.fromisoformat(end_date)
                    
                    one_year_ago = datetime.now().replace(tzinfo=event_date.tzinfo) - timedelta(days=365)
                    
                    # Пропускаем события старше года
                    if event_date < one_year_ago:
                        continue
                except Exception as e:
                    # Если не можем распарсить дату, пропускаем событие
                    continue
            
            # Проверяем, что рынок активен и не решен
            if (market.get('active', True) and 
                not market.get('resolved', False) and 
                question and 
                volume > 0):  # Только рынки с объемом
                
                # Создаем slug если его нет
                if not slug:
                    import re
                    slug = re.sub(r'[^\w\s-]', '', question.lower())
                    slug = re.sub(r'[-\s]+', '-', slug)
                    slug = slug.strip('-')[:50]
                    if not slug:
                        slug = f'market-{market.get("id", "unknown")}'
                
                event = {
                    'question': question,
                    'url': f'https://polymarket.com/event/{slug}',
                    'volume': volume,
                    'liquidity': liquidity,
                    'end_date': end_date,
                    'slug': slug
                }
                events.append(event)
        
        # Сортируем по объему и берем топ-10
        events.sort(key=lambda x: x['volume'], reverse=True)
        top_events = events[:10]
        
        # Сохраняем в кэш
        cache_data = {
            'events': top_events,
            'timestamp': time.time()
        }
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            'success': True,
            'events': top_events,
            'cached': False
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/markets-with-info')
def api_markets_with_info():
    """API endpoint для получения всех рынков с названиями и ссылками"""
    try:
        trades = api.load_from_cache()
        if not trades:
            return jsonify({
                'success': False,
                'error': 'Нет данных в кэше'
            }), 404
        
        # Получаем уникальные market_id
        market_ids = set()
        for trade in trades:
            if 'market_id' in trade:
                market_ids.add(trade['market_id'])
        
        # Получаем информацию о каждом рынке
        markets_info = []
        for market_id in list(market_ids)[:20]:  # Ограничиваем до 20 для скорости
            market_info = api.get_market_info(market_id)
            markets_info.append(market_info)
        
        return jsonify({
            'success': True,
            'markets': markets_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/test-links')
def test_links():
    """Тестовая страница для проверки ссылок"""
    return render_template('test_links.html')

@app.route('/api/notify-update', methods=['POST'])
def notify_update():
    """API для уведомления о новых данных"""
    try:
        data = request.get_json()
        notification_type = data.get('type', 'data_updated')
        timestamp = data.get('timestamp', datetime.now().isoformat())
        
        # Отправляем уведомление всем WebSocket клиентам
        for client in websocket_clients:
            try:
                client.send(json.dumps({
                    'type': notification_type,
                    'timestamp': timestamp,
                    'message': 'Данные обновлены'
                }))
            except:
                # Удаляем неактивных клиентов
                websocket_clients.remove(client)
        
        return jsonify({'success': True, 'clients_notified': len(websocket_clients)})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scheduler-status')
def scheduler_status():
    """API для получения статуса планировщика"""
    try:
        # Проверяем статус планировщика
        cache_file = "/Users/Kos/shadowflow/data/cache.json"
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                last_update = data.get('last_updated', 'Неизвестно')
                update_count = data.get('update_count', 0)
        else:
            last_update = 'Неизвестно'
            update_count = 0
        
        return jsonify({
            'success': True,
            'status': {
                'last_update': last_update,
                'update_count': update_count,
                'websocket_clients': len(websocket_clients),
                'is_realtime_active': True
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/update-data', methods=['POST'])
def update_data():
    """API для ручного обновления данных"""
    try:
        # Запускаем обновление данных
        markets = api.get_active_markets(limit=50)
        if not markets:
            return jsonify({'success': False, 'error': 'Не удалось получить рынки'}), 500
        
        # Получаем сделки
        all_trades = []
        for market in markets[:20]:
            market_id = market.get('id', market.get('market_id', ''))
            if market_id:
                try:
                    trades = api.get_market_trades(market_id, limit=50)
                    if trades:
                        all_trades.extend(trades)
                except Exception as e:
                    print(f"Ошибка при получении сделок для рынка {market_id}: {e}")
        
        # Сохраняем в кэш
        cache_data = {
            'markets': markets,
            'trades': all_trades,
            'last_updated': datetime.now().isoformat(),
            'source': 'manual_update',
            'update_count': get_update_count() + 1
        }
        
        cache_file = "/Users/Kos/shadowflow/data/cache.json"
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        
        # Запускаем анализ кластеров
        try:
            analyzer.analyze_clusters()
        except Exception as e:
            print(f"Ошибка при анализе кластеров: {e}")
        
        return jsonify({
            'success': True,
            'markets_count': len(markets),
            'trades_count': len(all_trades),
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/start-scheduler', methods=['POST'])
def start_scheduler():
    """API для запуска планировщика"""
    try:
        # Здесь можно добавить логику запуска планировщика
        return jsonify({'success': True, 'message': 'Планировщик запущен'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stop-scheduler', methods=['POST'])
def stop_scheduler():
    """API для остановки планировщика"""
    try:
        # Здесь можно добавить логику остановки планировщика
        return jsonify({'success': True, 'message': 'Планировщик остановлен'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_update_count():
    """Получает количество обновлений из кэша"""
    try:
        cache_file = "/Users/Kos/shadowflow/data/cache.json"
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('update_count', 0)
    except:
        pass
    return 0

# ===== ПРЕДСКАЗАТЕЛЬНАЯ АНАЛИТИКА API =====

@app.route('/api/predictive/status')
def predictive_status():
    """API endpoint для получения статуса предсказательной аналитики"""
    try:
        summary = predictive_analytics.get_analytics_summary()
        return jsonify({
            'success': True,
            'status': summary
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/predictive/train', methods=['POST'])
def train_predictive_models():
    """API endpoint для обучения моделей предсказательной аналитики"""
    try:
        print("🎯 Запуск обучения моделей предсказательной аналитики...")
        scores = predictive_analytics.train_models()
        
        return jsonify({
            'success': True,
            'model_scores': scores,
            'message': f'Обучено {len(scores)} моделей'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/predictive/predict')
def predict_attacks():
    """API endpoint для прогнозирования координированных атак"""
    try:
        # Получаем последние сделки из кэша
        hours_back = request.args.get('hours', 1, type=int)
        
        # Загружаем данные из кэша
        cache_file = "/Users/Kos/shadowflow/data/cache.json" if not os.path.exists("/app") else "/app/data/cache.json"
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            recent_trades = cache_data.get('trades', [])[:100]  # Берем последние 100 сделок
        else:
            recent_trades = []
        
        if not recent_trades:
            return jsonify({
                'success': False,
                'error': 'Нет данных о сделках'
            }), 400
        
        # Прогнозируем атаки
        prediction = predictive_analytics.predict_coordinated_attacks(recent_trades)
        
        return jsonify({
            'success': True,
            'prediction': prediction,
            'trades_analyzed': len(recent_trades)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/predictive/trends')
def get_predictive_trends():
    """API endpoint для получения анализа трендов"""
    try:
        days_back = request.args.get('days', 7, type=int)
        trends = predictive_analytics.analyze_trends(days_back)
        
        return jsonify({
            'success': True,
            'trends': trends,
            'period_days': days_back
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/predictive/risk-score')
def get_risk_score():
    """API endpoint для получения риск-скора в реальном времени"""
    try:
        # Получаем последние сделки из кэша
        cache_file = "/Users/Kos/shadowflow/data/cache.json" if not os.path.exists("/app") else "/app/data/cache.json"
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            recent_trades = cache_data.get('trades', [])[:50]  # Берем последние 50 сделок
        else:
            recent_trades = []
        
        if not recent_trades:
            return jsonify({
                'success': False,
                'error': 'Нет данных о сделках'
            }), 400
        
        # Вычисляем риск-скор
        risk_score = predictive_analytics.get_risk_score(recent_trades)
        
        return jsonify({
            'success': True,
            'risk_score': risk_score,
            'trades_analyzed': len(recent_trades)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/predictive/warnings')
def get_warnings():
    """API endpoint для получения предупреждений"""
    try:
        # Получаем последние сделки из кэша
        cache_file = "/Users/Kos/shadowflow/data/cache.json" if not os.path.exists("/app") else "/app/data/cache.json"
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            recent_trades = cache_data.get('trades', [])[:100]  # Берем последние 100 сделок
        else:
            recent_trades = []
        
        if not recent_trades:
            return jsonify({
                'success': False,
                'error': 'Нет данных о сделках'
            }), 400
        
        # Прогнозируем атаки
        prediction = predictive_analytics.predict_coordinated_attacks(recent_trades)
        
        # Генерируем предупреждение
        warning = predictive_analytics.generate_early_warning(prediction)
        
        return jsonify({
            'success': True,
            'warning': warning,
            'prediction': prediction,
            'trades_analyzed': len(recent_trades)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/predictive')
def predictive_dashboard():
    """Страница предсказательной аналитики"""
    return render_template('predictive.html')

if __name__ == '__main__':
    # Создаем необходимые директории
    os.makedirs('/Users/Kos/shadowflow/data', exist_ok=True)
    os.makedirs('/Users/Kos/shadowflow/templates', exist_ok=True)
    os.makedirs('/Users/Kos/shadowflow/static/css', exist_ok=True)
    os.makedirs('/Users/Kos/shadowflow/static/js', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5001)

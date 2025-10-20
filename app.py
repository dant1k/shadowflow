"""
ShadowFlow - Система анализа координированных действий на Polymarket
Веб-приложение Flask для визуализации результатов анализа кластеризации
"""

from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime
from analyzer.cluster import TradeClusterAnalyzer
from api.polymarket import PolymarketAPI
from ai.anomaly_detector import AnomalyDetector

app = Flask(__name__)
app.config['SECRET_KEY'] = 'shadowflow-secret-key-2024'

# Инициализация компонентов
analyzer = TradeClusterAnalyzer(sync_threshold_seconds=180)
api = PolymarketAPI()
ai_detector = AnomalyDetector()

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

@app.route('/api/update-data')
def update_data():
    """API endpoint для обновления данных"""
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
        # Загружаем данные из кэша
        trades = api.load_from_cache()
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
        trades = api.load_from_cache()
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

if __name__ == '__main__':
    # Создаем необходимые директории
    os.makedirs('/Users/Kos/shadowflow/data', exist_ok=True)
    os.makedirs('/Users/Kos/shadowflow/templates', exist_ok=True)
    os.makedirs('/Users/Kos/shadowflow/static/css', exist_ok=True)
    os.makedirs('/Users/Kos/shadowflow/static/js', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5001)

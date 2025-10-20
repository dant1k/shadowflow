"""
Real-time мониторинг системы ShadowFlow
Отслеживает изменения в данных и отправляет уведомления через WebSocket
"""

import asyncio
import websockets
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Set
import threading
from collections import defaultdict, deque
import logging

from api.polymarket import PolymarketAPI
from analyzer.cluster import TradeClusterAnalyzer
from ai.anomaly_detector import AnomalyDetector

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealTimeMonitor:
    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        
        # Компоненты системы
        self.api = PolymarketAPI()
        self.analyzer = TradeClusterAnalyzer()
        self.ai_detector = AnomalyDetector()
        
        # Состояние мониторинга
        self.last_analysis_time = None
        self.last_risk_score = 0.0
        self.alert_thresholds = {
            'risk_score': 50.0,  # Порог риска
            'anomaly_percentage': 15.0,  # Процент аномалий
            'cluster_count': 20,  # Количество кластеров
            'volume_spike': 2.0  # Рост объема в разы
        }
        
        # История для детекции изменений
        self.volume_history = deque(maxlen=10)  # Последние 10 измерений
        self.risk_history = deque(maxlen=5)
        
        # Статистика
        self.stats = {
            'total_alerts': 0,
            'last_update': None,
            'monitoring_active': False
        }
        
    async def register_client(self, websocket, path):
        """Регистрирует нового клиента WebSocket"""
        self.connected_clients.add(websocket)
        logger.info(f"Клиент подключен. Всего клиентов: {len(self.connected_clients)}")
        
        try:
            # Отправляем текущее состояние
            await self.send_current_state(websocket)
            
            # Ожидаем сообщения от клиента
            async for message in websocket:
                await self.handle_client_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.connected_clients.remove(websocket)
            logger.info(f"Клиент отключен. Осталось клиентов: {len(self.connected_clients)}")
    
    async def handle_client_message(self, websocket, message):
        """Обрабатывает сообщения от клиентов"""
        try:
            data = json.loads(message)
            command = data.get('command')
            
            if command == 'get_status':
                await self.send_status(websocket)
            elif command == 'update_thresholds':
                self.alert_thresholds.update(data.get('thresholds', {}))
                await self.broadcast_message({
                    'type': 'thresholds_updated',
                    'thresholds': self.alert_thresholds
                })
            elif command == 'force_analysis':
                await self.perform_analysis()
                
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'Неверный формат JSON'
            }))
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
    
    async def send_current_state(self, websocket):
        """Отправляет текущее состояние системы клиенту"""
        try:
            # Загружаем текущие данные
            trades = self.api.load_from_cache()
            if not trades:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'Нет данных для анализа'
                }))
                return
            
            # Выполняем быстрый анализ
            analysis = self.ai_detector.comprehensive_analysis(trades[:1000])  # Ограничиваем для скорости
            
            state = {
                'type': 'current_state',
                'timestamp': datetime.now().isoformat(),
                'stats': {
                    'total_trades': len(trades),
                    'risk_score': analysis['risk_score'],
                    'anomalies_count': analysis['anomalies']['count'],
                    'wallet_clusters': analysis['wallet_clusters']['count'],
                    'monitoring_active': self.stats['monitoring_active']
                },
                'thresholds': self.alert_thresholds
            }
            
            await websocket.send(json.dumps(state))
            
        except Exception as e:
            logger.error(f"Ошибка отправки состояния: {e}")
            await websocket.send(json.dumps({
                'type': 'error',
                'message': f'Ошибка анализа: {str(e)}'
            }))
    
    async def send_status(self, websocket):
        """Отправляет статус системы"""
        status = {
            'type': 'status',
            'timestamp': datetime.now().isoformat(),
            'monitoring_active': self.stats['monitoring_active'],
            'connected_clients': len(self.connected_clients),
            'last_analysis': self.last_analysis_time.isoformat() if self.last_analysis_time else None,
            'total_alerts': self.stats['total_alerts']
        }
        
        await websocket.send(json.dumps(status))
    
    async def broadcast_message(self, message):
        """Отправляет сообщение всем подключенным клиентам"""
        if not self.connected_clients:
            return
        
        message_str = json.dumps(message)
        disconnected = set()
        
        for client in self.connected_clients:
            try:
                await client.send(message_str)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
        
        # Удаляем отключенных клиентов
        self.connected_clients -= disconnected
    
    async def perform_analysis(self):
        """Выполняет полный анализ и проверяет на алерты"""
        try:
            logger.info("Выполнение анализа для мониторинга...")
            
            # Загружаем данные
            trades = self.api.load_from_cache()
            if not trades:
                logger.warning("Нет данных для анализа")
                return
            
            # Выполняем AI-анализ
            analysis = self.ai_detector.comprehensive_analysis(trades)
            
            # Обновляем историю
            self.risk_history.append(analysis['risk_score'])
            self.volume_history.append(sum(trade.get('amount', 0) for trade in trades))
            
            # Проверяем алерты
            alerts = self.check_alerts(analysis, trades)
            
            # Отправляем результаты
            await self.broadcast_message({
                'type': 'analysis_update',
                'timestamp': datetime.now().isoformat(),
                'analysis': analysis,
                'alerts': alerts
            })
            
            # Обновляем статистику
            self.last_analysis_time = datetime.now()
            self.last_risk_score = analysis['risk_score']
            self.stats['last_update'] = self.last_analysis_time
            self.stats['total_alerts'] += len(alerts)
            
            logger.info(f"Анализ завершен. Риск: {analysis['risk_score']:.1f}, Алертов: {len(alerts)}")
            
        except Exception as e:
            logger.error(f"Ошибка при анализе: {e}")
            await self.broadcast_message({
                'type': 'error',
                'message': f'Ошибка анализа: {str(e)}'
            })
    
    def check_alerts(self, analysis: Dict, trades: List[Dict]) -> List[Dict]:
        """Проверяет условия для алертов"""
        alerts = []
        current_time = datetime.now()
        
        # Алерт по риск-скору
        if analysis['risk_score'] >= self.alert_thresholds['risk_score']:
            alerts.append({
                'type': 'high_risk',
                'severity': 'high' if analysis['risk_score'] >= 80 else 'medium',
                'message': f'Высокий риск-скор: {analysis["risk_score"]:.1f}/100',
                'value': analysis['risk_score'],
                'threshold': self.alert_thresholds['risk_score'],
                'timestamp': current_time.isoformat()
            })
        
        # Алерт по проценту аномалий
        anomaly_percentage = analysis['anomalies']['percentage']
        if anomaly_percentage >= self.alert_thresholds['anomaly_percentage']:
            alerts.append({
                'type': 'high_anomalies',
                'severity': 'high' if anomaly_percentage >= 25 else 'medium',
                'message': f'Высокий процент аномалий: {anomaly_percentage:.1f}%',
                'value': anomaly_percentage,
                'threshold': self.alert_thresholds['anomaly_percentage'],
                'timestamp': current_time.isoformat()
            })
        
        # Алерт по количеству кластеров
        cluster_count = analysis['wallet_clusters']['count']
        if cluster_count >= self.alert_thresholds['cluster_count']:
            alerts.append({
                'type': 'many_clusters',
                'severity': 'medium',
                'message': f'Много кластеров кошельков: {cluster_count}',
                'value': cluster_count,
                'threshold': self.alert_thresholds['cluster_count'],
                'timestamp': current_time.isoformat()
            })
        
        # Алерт по росту объема
        if len(self.volume_history) >= 2:
            current_volume = self.volume_history[-1]
            previous_volume = self.volume_history[-2]
            
            if previous_volume > 0:
                volume_growth = current_volume / previous_volume
                if volume_growth >= self.alert_thresholds['volume_spike']:
                    alerts.append({
                        'type': 'volume_spike',
                        'severity': 'high' if volume_growth >= 5 else 'medium',
                        'message': f'Резкий рост объема торгов: {volume_growth:.1f}x',
                        'value': volume_growth,
                        'threshold': self.alert_thresholds['volume_spike'],
                        'timestamp': current_time.isoformat()
                    })
        
        # Алерт по подозрительным временным паттернам
        if analysis['temporal_patterns'].get('suspicious_pattern', False):
            alerts.append({
                'type': 'suspicious_patterns',
                'severity': 'medium',
                'message': 'Обнаружены подозрительные временные паттерны',
                'value': True,
                'threshold': False,
                'timestamp': current_time.isoformat()
            })
        
        # Алерт по манипуляциям с ценами
        manipulation_markets = analysis['price_manipulation'].get('suspicious_markets', 0)
        if manipulation_markets >= 10:  # Более 10 рынков с манипуляциями
            alerts.append({
                'type': 'price_manipulation',
                'severity': 'high',
                'message': f'Манипуляции с ценами на {manipulation_markets} рынках',
                'value': manipulation_markets,
                'threshold': 10,
                'timestamp': current_time.isoformat()
            })
        
        return alerts
    
    async def start_monitoring(self, interval_seconds=60):
        """Запускает периодический мониторинг"""
        self.stats['monitoring_active'] = True
        logger.info(f"Запуск мониторинга с интервалом {interval_seconds} секунд")
        
        while self.stats['monitoring_active']:
            try:
                await self.perform_analysis()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Ошибка в цикле мониторинга: {e}")
                await asyncio.sleep(10)  # Короткая пауза при ошибке
    
    def stop_monitoring(self):
        """Останавливает мониторинг"""
        self.stats['monitoring_active'] = False
        logger.info("Мониторинг остановлен")
    
    async def start_server(self):
        """Запускает WebSocket сервер"""
        logger.info(f"Запуск WebSocket сервера на {self.host}:{self.port}")
        
        # Запускаем мониторинг в фоновом режиме
        monitoring_task = asyncio.create_task(self.start_monitoring())
        
        try:
            # Запускаем WebSocket сервер
            async with websockets.serve(self.register_client, self.host, self.port):
                logger.info("WebSocket сервер запущен")
                await asyncio.Future()  # Работаем бесконечно
        except KeyboardInterrupt:
            logger.info("Получен сигнал остановки")
        finally:
            monitoring_task.cancel()
            self.stop_monitoring()

# Функция для запуска мониторинга
async def start_realtime_monitoring():
    """Запускает real-time мониторинг"""
    monitor = RealTimeMonitor()
    await monitor.start_server()

if __name__ == "__main__":
    # Запуск мониторинга
    asyncio.run(start_realtime_monitoring())

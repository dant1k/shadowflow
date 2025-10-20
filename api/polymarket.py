"""
API клиент для получения данных с Polymarket
Анализирует активные рынки и последние сделки для выявления координированных действий
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

class PolymarketAPI:
    def __init__(self):
        # Используем официальные API endpoints из документации Polymarket
        self.gamma_api_url = "https://gamma-api.polymarket.com"
        self.data_api_url = "https://data-api.polymarket.com"
        self.clob_api_url = "https://clob.polymarket.com"
        self.cache_file = "/Users/Kos/shadowflow/data/cache.json"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ShadowFlow/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def get_active_markets(self, limit: int = 50) -> List[Dict]:
        """Получает список активных рынков используя официальный API"""
        try:
            url = f"{self.gamma_api_url}/markets"
            params = {
                'limit': limit,
                'active': 'true',
                'order': 'volume',
                'ascending': 'false'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            markets = response.json()
            
            if isinstance(markets, list) and len(markets) > 0:
                print(f"✅ Получено {len(markets)} активных рынков с Gamma API")
                return markets
            else:
                print("❌ API вернул пустой список рынков")
                return []
            
        except Exception as e:
            print(f"❌ Ошибка при получении рынков: {e}")
            return []
    
    def get_market_info(self, market_id):
        """Получает информацию о конкретном рынке используя официальный Gamma API"""
        try:
            # Используем официальный endpoint из документации
            url = f"{self.gamma_api_url}/markets/{market_id}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Извлекаем информацию согласно документации
                question = data.get('question', f'Market {market_id}')
                slug = data.get('slug', self._create_slug(question))
                
                # Используем поиск по ID - это работает надежно для всех рынков
                market_url = f"https://polymarket.com/search?q={market_id}"
                
                market_info = {
                    'id': market_id,
                    'name': question,
                    'url': market_url,
                    'description': data.get('description', ''),
                    'end_date': data.get('end_date', ''),
                    'volume': data.get('volume', 0),
                    'slug': slug
                }
                
                return market_info
                
            else:
                # Если рынок не найден, используем поиск
                return {
                    'id': market_id,
                    'name': f'Market {market_id}',
                    'url': f'https://polymarket.com/search?q={market_id}',
                    'description': '',
                    'end_date': '',
                    'volume': 0,
                    'slug': f'market-{market_id}'
                }
            
        except Exception as e:
            # В случае ошибки используем поиск
            return {
                'id': market_id,
                'name': f'Market {market_id}',
                'url': f'https://polymarket.com/search?q={market_id}',
                'description': '',
                'end_date': '',
                'volume': 0,
                'slug': f'market-{market_id}'
            }
    
    def _create_slug(self, text):
        """Создает slug из текста для URL"""
        import re
        import time
        
        # Убираем специальные символы и приводим к нижнему регистру
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        # Заменяем пробелы на дефисы
        slug = re.sub(r'[-\s]+', '-', slug)
        # Убираем дефисы в начале и конце
        slug = slug.strip('-')
        # Ограничиваем длину
        slug = slug[:50]
        
        return slug
    
    def get_market_trades(self, market_id: str, hours_back: int = 24, limit: int = 1000) -> List[Dict]:
        """Получает сделки по конкретному рынку используя Data API"""
        try:
            url = f"{self.data_api_url}/trades"
            params = {
                'market': market_id,
                'limit': limit
            }
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            trades = response.json()
            
            if isinstance(trades, list):
                # Фильтруем сделки по времени
                current_time = int(time.time())
                start_time = current_time - (hours_back * 3600)
                
                filtered_trades = []
                for trade in trades:
                    try:
                        # Парсим время сделки (может быть в разных форматах)
                        trade_time = self.parse_trade_timestamp(trade)
                        if trade_time and trade_time >= start_time:
                            filtered_trades.append(trade)
                    except:
                        continue
                
                print(f"✅ Получено {len(filtered_trades)} сделок для рынка {market_id}")
                return filtered_trades
            else:
                print(f"❌ Неожиданный формат ответа для сделок рынка {market_id}")
                return []
            
        except Exception as e:
            print(f"❌ Ошибка при получении сделок для рынка {market_id}: {e}")
            return []
    
    def parse_trade_timestamp(self, trade: Dict) -> Optional[int]:
        """Парсит timestamp из сделки в разных форматах"""
        try:
            # Пробуем разные поля для времени
            time_fields = ['timestamp', 'createdAt', 'time', 'date', 'created_at']
            
            for field in time_fields:
                if field in trade:
                    value = trade[field]
                    if isinstance(value, (int, float)):
                        return int(value)
                    elif isinstance(value, str):
                        # Пробуем парсить ISO строку
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                            return int(dt.timestamp())
                        except:
                            continue
            
            return None
        except:
            return None
    
    def get_recent_trades(self, hours_back: int = 6) -> List[Dict]:
        """Получает все недавние сделки по всем активным рынкам"""
        all_trades = []
        
        # Получаем активные рынки
        markets = self.get_active_markets()
        print(f"Найдено {len(markets)} активных рынков")
        
        for market in markets:
            market_id = market.get('id')
            market_name = market.get('question', 'Неизвестный рынок')
            
            if not market_id:
                continue
                
            print(f"Получаем сделки для рынка: {market_name}")
            
            # Получаем сделки для этого рынка
            trades = self.get_market_trades(market_id, hours_back)
            
            # Добавляем метаданные рынка к каждой сделке
            for trade in trades:
                trade['market_id'] = market_id
                trade['market_name'] = market_name
                trade['market_question'] = market.get('question', '')
                trade['market_outcomes'] = market.get('outcomes', [])
            
            all_trades.extend(trades)
            
            # Небольшая пауза между запросами
            time.sleep(0.1)
        
        print(f"Всего получено {len(all_trades)} сделок")
        return all_trades
    
    def save_to_cache(self, trades: List[Dict]) -> None:
        """Сохраняет сделки в кэш"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'trades': trades,
                'count': len(trades)
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
            print(f"Сохранено {len(trades)} сделок в кэш")
            
        except Exception as e:
            print(f"Ошибка при сохранении в кэш: {e}")
    
    def load_from_cache(self) -> List[Dict]:
        """Загружает сделки из кэша"""
        try:
            if not os.path.exists(self.cache_file):
                return []
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            trades = cache_data.get('trades', [])
            cache_time = cache_data.get('timestamp', '')
            
            print(f"Загружено {len(trades)} сделок из кэша (время: {cache_time})")
            return trades
            
        except Exception as e:
            print(f"Ошибка при загрузке из кэша: {e}")
            return []
    
    def normalize_trade_data(self, trades: List[Dict]) -> List[Dict]:
        """Нормализует данные сделок для анализа"""
        normalized_trades = []
        
        for trade in trades:
            try:
                # Извлекаем основные поля из реального API Polymarket
                normalized_trade = {
                    'id': trade.get('id', ''),
                    'market_id': trade.get('market', trade.get('market_id', '')),
                    'market_name': trade.get('market_name', ''),
                    'wallet': self.extract_wallet_address(trade),
                    'side': self.extract_side(trade),
                    'amount': self.extract_amount(trade),
                    'price': self.extract_price(trade),
                    'timestamp': self.parse_trade_timestamp(trade) or 0,
                    'datetime': self.format_datetime(self.parse_trade_timestamp(trade)),
                    'outcome': trade.get('outcome', ''),
                    'market_question': trade.get('market_question', '')
                }
                
                # Фильтруем некорректные данные
                if (normalized_trade['wallet'] and 
                    normalized_trade['market_id'] and 
                    normalized_trade['side'] in ['YES', 'NO'] and
                    normalized_trade['amount'] > 0 and
                    normalized_trade['timestamp'] > 0):
                    
                    normalized_trades.append(normalized_trade)
                    
            except Exception as e:
                print(f"Ошибка при нормализации сделки: {e}")
                continue
        
        return normalized_trades
    
    def extract_wallet_address(self, trade: Dict) -> str:
        """Извлекает адрес кошелька из сделки"""
        # Пробуем разные поля для адреса кошелька
        wallet_fields = ['proxyWallet', 'maker', 'taker', 'user', 'trader', 'address', 'wallet']
        
        for field in wallet_fields:
            if field in trade:
                value = trade[field]
                if isinstance(value, str) and value.startswith('0x'):
                    return value
                elif isinstance(value, dict) and 'address' in value:
                    return value['address']
        
        return ''
    
    def extract_side(self, trade: Dict) -> str:
        """Извлекает направление сделки (YES/NO)"""
        # Пробуем разные поля для направления
        side_fields = ['outcome', 'side', 'position', 'direction']
        
        for field in side_fields:
            if field in trade:
                value = trade[field]
                if isinstance(value, str):
                    # Преобразуем в YES/NO формат
                    if value.upper() in ['YES', 'NO']:
                        return value.upper()
                    elif value.upper() in ['UP', 'BUY', 'LONG']:
                        return 'YES'
                    elif value.upper() in ['DOWN', 'SELL', 'SHORT']:
                        return 'NO'
        
        return ''
    
    def extract_amount(self, trade: Dict) -> float:
        """Извлекает объем сделки"""
        # Пробуем разные поля для объема
        amount_fields = ['size', 'amount', 'quantity', 'volume', 'value']
        
        for field in amount_fields:
            if field in trade:
                try:
                    value = trade[field]
                    if isinstance(value, (int, float)):
                        return float(value)
                    elif isinstance(value, str):
                        return float(value)
                except:
                    continue
        
        return 0.0
    
    def extract_price(self, trade: Dict) -> float:
        """Извлекает цену сделки"""
        # Пробуем разные поля для цены
        price_fields = ['price', 'rate', 'cost', 'value']
        
        for field in price_fields:
            if field in trade:
                try:
                    value = trade[field]
                    if isinstance(value, (int, float)):
                        return float(value)
                    elif isinstance(value, str):
                        return float(value)
                except:
                    continue
        
        return 0.0
    
    def format_datetime(self, timestamp: Optional[int]) -> str:
        """Форматирует timestamp в ISO строку"""
        if timestamp:
            return datetime.fromtimestamp(timestamp).isoformat()
        return ''
    
    def update_trades_data(self, hours_back: int = 6) -> List[Dict]:
        """Обновляет данные о сделках (получает новые и сохраняет в кэш)"""
        print("Обновление данных о сделках...")
        
        # Получаем новые сделки
        raw_trades = self.get_recent_trades(hours_back)
        
        # Если API не дал результатов, пробуем скрапинг
        if not raw_trades:
            print("🔄 API не дал результатов, пробуем веб-скрапинг...")
            try:
                from api.polymarket_scraper import PolymarketScraper
                scraper = PolymarketScraper()
                raw_trades = scraper.get_recent_trades(hours_back)
                if raw_trades:
                    print(f"✅ Скрапинг дал {len(raw_trades)} сделок")
            except Exception as e:
                print(f"❌ Ошибка при скрапинге: {e}")
        
        # Нормализуем данные
        normalized_trades = self.normalize_trade_data(raw_trades)
        
        # Сохраняем в кэш
        self.save_to_cache(normalized_trades)
        
        return normalized_trades

# Пример использования
if __name__ == "__main__":
    api = PolymarketAPI()
    
    # Обновляем данные
    trades = api.update_trades_data(hours_back=6)
    
    # Показываем статистику
    if trades:
        print(f"\nСтатистика:")
        print(f"Всего сделок: {len(trades)}")
        
        # Группировка по рынкам
        markets = {}
        for trade in trades:
            market_name = trade['market_name']
            if market_name not in markets:
                markets[market_name] = 0
            markets[market_name] += 1
        
        print(f"Рынков: {len(markets)}")
        for market, count in list(markets.items())[:5]:
            print(f"  {market}: {count} сделок")

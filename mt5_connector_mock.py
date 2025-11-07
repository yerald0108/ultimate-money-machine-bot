"""
Mock MT5 Connector para despliegue en producción
Simula las funciones de MetaTrader5 para que el bot funcione sin MT5 real
"""
import random
import asyncio
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class MT5ConnectorMock:
    """Conector simulado de MetaTrader5 para producción"""
    
    def __init__(self):
        self.connected = False
        self.account_info = {
            'balance': 10000.0,
            'equity': 10000.0,
            'margin': 0.0,
            'margin_free': 10000.0,
            'margin_level': 0.0,
            'profit': 0.0,
            'currency': 'USD',
            'leverage': 100,
            'server': 'Demo-Server',
            'name': 'Demo Account'
        }
        self.positions = []
        self.trade_history = []
        
        logger.info("🎭 MT5 Mock Connector inicializado - MODO DEMO")
    
    async def connect(self, login=None, password=None, server=None):
        """Simular conexión a MT5"""
        await asyncio.sleep(1)  # Simular tiempo de conexión
        self.connected = True
        logger.info("✅ Conectado a MT5 (MODO DEMO)")
        return True
    
    async def disconnect(self):
        """Simular desconexión"""
        self.connected = False
        logger.info("🔌 Desconectado de MT5 (MODO DEMO)")
        return True
    
    async def get_account_info(self):
        """Simular información de cuenta"""
        if not self.connected:
            return None
        
        # Simular pequeñas variaciones en el balance
        variation = random.uniform(-10, 10)
        self.account_info['equity'] = self.account_info['balance'] + variation
        
        return self.account_info.copy()
    
    async def get_positions(self):
        """Simular posiciones abiertas"""
        if not self.connected:
            return []
        
        # Simular algunas posiciones demo
        demo_positions = []
        if random.random() < 0.3:  # 30% probabilidad de tener posiciones
            for i in range(random.randint(1, 3)):
                demo_positions.append({
                    'ticket': random.randint(100000, 999999),
                    'symbol': random.choice(['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']),
                    'type': random.randint(0, 1),  # 0=BUY, 1=SELL
                    'volume': round(random.uniform(0.1, 1.0), 2),
                    'price_open': round(random.uniform(1.0, 1.5), 5),
                    'price_current': round(random.uniform(1.0, 1.5), 5),
                    'profit': round(random.uniform(-50, 100), 2),
                    'time': datetime.now() - timedelta(hours=random.randint(1, 24))
                })
        
        return demo_positions
    
    async def get_rates(self, symbol='EURUSD', timeframe='M15', count=100):
        """Simular datos históricos"""
        if not self.connected:
            return pd.DataFrame()
        
        # Generar datos simulados
        dates = pd.date_range(end=datetime.now(), periods=count, freq='15T')
        
        # Simular precios realistas
        base_price = 1.1500 if symbol == 'EURUSD' else random.uniform(0.5, 2.0)
        prices = []
        current_price = base_price
        
        for _ in range(count):
            # Movimiento aleatorio pero realista
            change = random.uniform(-0.002, 0.002)
            current_price += change
            
            # OHLC simulado
            high = current_price + random.uniform(0, 0.001)
            low = current_price - random.uniform(0, 0.001)
            open_price = current_price + random.uniform(-0.0005, 0.0005)
            
            prices.append({
                'time': dates[len(prices)],
                'open': round(open_price, 5),
                'high': round(high, 5),
                'low': round(low, 5),
                'close': round(current_price, 5),
                'tick_volume': random.randint(50, 500),
                'spread': random.randint(1, 5),
                'real_volume': 0
            })
        
        df = pd.DataFrame(prices)
        df.set_index('time', inplace=True)
        
        logger.info(f"📊 Datos simulados generados: {len(df)} períodos para {symbol}")
        return df
    
    async def place_order(self, symbol, order_type, volume, price=None, sl=None, tp=None, comment=""):
        """Simular colocación de orden"""
        if not self.connected:
            return {'success': False, 'error': 'No conectado'}
        
        # Simular éxito/fallo de orden
        if random.random() < 0.9:  # 90% éxito
            ticket = random.randint(100000, 999999)
            
            # Simular trade ejecutado
            trade = {
                'ticket': ticket,
                'symbol': symbol,
                'type': order_type,
                'volume': volume,
                'price_open': price or random.uniform(1.0, 1.5),
                'sl': sl,
                'tp': tp,
                'profit': 0,
                'time': datetime.now(),
                'comment': comment + " (DEMO)"
            }
            
            self.trade_history.append(trade)
            logger.info(f"✅ Orden simulada ejecutada: {ticket} - {symbol} {volume} lotes")
            
            return {
                'success': True,
                'ticket': ticket,
                'price': trade['price_open']
            }
        else:
            logger.warning("❌ Orden simulada falló")
            return {'success': False, 'error': 'Orden rechazada (simulación)'}
    
    async def close_position(self, ticket):
        """Simular cierre de posición"""
        if not self.connected:
            return {'success': False, 'error': 'No conectado'}
        
        # Simular cierre exitoso
        profit = random.uniform(-20, 50)
        logger.info(f"🔄 Posición simulada cerrada: {ticket} - P&L: ${profit:.2f}")
        
        return {
            'success': True,
            'profit': profit,
            'price': random.uniform(1.0, 1.5)
        }
    
    async def modify_position(self, ticket, sl=None, tp=None):
        """Simular modificación de posición"""
        if not self.connected:
            return {'success': False, 'error': 'No conectado'}
        
        logger.info(f"🔧 Posición simulada modificada: {ticket}")
        return {'success': True}
    
    async def get_trade_history(self, days=30):
        """Simular historial de trades"""
        if not self.connected:
            return []
        
        # Generar historial demo si está vacío
        if not self.trade_history:
            for i in range(random.randint(5, 15)):
                self.trade_history.append({
                    'ticket': random.randint(100000, 999999),
                    'symbol': random.choice(['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']),
                    'type': random.randint(0, 1),
                    'volume': round(random.uniform(0.1, 1.0), 2),
                    'price_open': round(random.uniform(1.0, 1.5), 5),
                    'price_close': round(random.uniform(1.0, 1.5), 5),
                    'profit': round(random.uniform(-30, 80), 2),
                    'time': datetime.now() - timedelta(days=random.randint(1, days)),
                    'comment': f"Demo Trade {i+1}"
                })
        
        return self.trade_history.copy()
    
    def is_connected(self):
        """Verificar conexión simulada"""
        return self.connected

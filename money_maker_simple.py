"""
MONEY MAKER SIMPLE - Bot de Trading Simplificado para Generar Dinero
Sin dependencias complejas, enfocado 100% en generar dinero
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
import signal
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('money_maker.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Importar solo lo esencial
from trading.mt5_connector import MT5Connector

class SimpleMoneyMaker:
    """Bot simplificado enfocado exclusivamente en generar dinero"""
    
    def __init__(self, initial_capital: float = 1000):
        self.initial_capital = initial_capital
        self.current_balance = initial_capital
        self.mt5 = None
        self.running = False
        self.demo_mode = False
        
        # Configuración ULTRA AGRESIVA para máximas ganancias
        self.config = {
            'target_daily_pips': 50,        # 50 pips diarios objetivo (DOBLE)
            'max_risk_per_trade': 0.12,     # 12% por trade (MÁS AGRESIVO)
            'max_daily_trades': 30,         # Máximo 30 trades por día (DOBLE)
            'min_confidence': 60,           # 60% confianza (MÁS OPORTUNIDADES)
            'profit_target_multiplier': 2.0, # R:R 1:2 (MÁS GANANCIA)
            'ultra_aggressive': True,       # Modo ultra agresivo
            'scalping_frequency': 15,       # Scalping cada 15 segundos
            'opportunity_threshold': 0.5    # Menor umbral para detectar oportunidades
        }
        
        # Estadísticas del día
        self.daily_stats = {
            'trades': 0,
            'wins': 0,
            'losses': 0,
            'pips': 0,
            'pnl': 0
        }
        
        logger.info("💰 ULTRA AGGRESSIVE MONEY MAKER INICIALIZADO")
        logger.info(f"🎯 Capital: ${initial_capital:,.2f}")
        logger.info(f"🔥 MODO ULTRA AGRESIVO ACTIVADO")
        logger.info(f"🎯 Objetivo: 50 pips diarios (DOBLE)")
        logger.info(f"⚡ Riesgo por trade: 12% (MÁXIMO)")
        logger.info(f"🚀 Trades diarios: Hasta 30 (DOBLE)")
    
    async def connect_mt5(self):
        """Conectar a MT5"""
        try:
            self.mt5 = MT5Connector()
            
            # Intentar conexión normal primero
            try:
                result = await self.mt5.connect()
                if result.get('success', False):
                    logger.info("✅ MT5 conectado - Listo para hacer dinero")
                    
                    # Obtener balance real
                    account_info = await self.mt5.get_account_info()
                    if account_info and account_info.get('balance', 0) > 0:
                        self.current_balance = account_info['balance']
                        logger.info(f"💳 Balance real: ${self.current_balance:,.2f}")
                    
                    return True
            except:
                pass
            
            # Si falla, usar modo demo
            logger.info("🧪 MT5 no disponible - Iniciando en MODO DEMO")
            logger.info("💰 Simulando generación de dinero...")
            self.demo_mode = True
            return True
                
        except Exception as e:
            logger.error(f"Error en conexión MT5: {e}")
            # Modo demo como fallback
            logger.info("🧪 Iniciando en MODO DEMO")
            self.demo_mode = True
            return True
    
    def session_breakout_strategy(self, df: pd.DataFrame) -> dict:
        """
        Estrategia Session Breakout - LA MÁS RENTABLE (38.29% probado)
        """
        try:
            if len(df) < 20:
                return None
            
            current_time = datetime.now()
            hour = current_time.hour
            
            # MODO ULTRA AGRESIVO: Operar en MÁS sesiones
            london_session = 7 <= hour <= 17    # Sesión Londres extendida
            ny_session = 12 <= hour <= 22       # Sesión NY extendida  
            asia_session = 0 <= hour <= 6       # Sesión Asia
            
            # En modo ultra agresivo, operar casi siempre
            if not (london_session or ny_session or asia_session):
                # Solo parar entre 23:00 y 00:00 (1 hora de descanso)
                if hour == 23:
                    return None
            
            # Calcular rango de las últimas 4 horas (16 barras de 15min)
            recent_data = df.tail(16)
            session_high = recent_data['high'].max()
            session_low = recent_data['low'].min()
            session_range = session_high - session_low
            
            current_price = df['close'].iloc[-1]
            
            # ULTRA AGRESIVO: Filtro más permisivo - rango mínimo de 8 pips
            if session_range < 0.0008:  # 8 pips (MÁS PERMISIVO)
                return None
            
            # ULTRA AGRESIVO: Detectar breakout más fácilmente
            breakout_threshold = 0.2  # 20% del rango (MÁS SENSIBLE)
            
            # Breakout alcista
            if current_price > session_high - (session_range * breakout_threshold):
                entry_price = current_price
                stop_loss = session_low
                take_profit = entry_price + (session_range * 1.2)
                
                # Calcular confianza
                breakout_strength = (current_price - session_low) / session_range
                confidence = min(85, 50 + breakout_strength * 35)
                
                return {
                    'action': 'buy',
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'confidence': confidence,
                    'strategy': 'session_breakout',
                    'expected_pips': (take_profit - entry_price) / 0.0001
                }
            
            # Breakout bajista
            elif current_price < session_low + (session_range * breakout_threshold):
                entry_price = current_price
                stop_loss = session_high
                take_profit = entry_price - (session_range * 1.2)
                
                breakout_strength = (session_high - current_price) / session_range
                confidence = min(85, 50 + breakout_strength * 35)
                
                return {
                    'action': 'sell',
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'confidence': confidence,
                    'strategy': 'session_breakout',
                    'expected_pips': (entry_price - take_profit) / 0.0001
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error en session breakout: {e}")
            return None
    
    def scalping_strategy(self, df: pd.DataFrame) -> dict:
        """
        Estrategia de Scalping Rápido - Alta frecuencia
        """
        try:
            if len(df) < 10:
                return None
            
            # Calcular momentum de muy corto plazo
            df_copy = df.copy()
            df_copy['price_change'] = df_copy['close'].diff()
            df_copy['volume_ratio'] = df_copy['tick_volume'] / df_copy['tick_volume'].rolling(5).mean()
            
            current = df_copy.iloc[-1]
            
            # ULTRA AGRESIVO: Detectar momentum más fácilmente
            momentum = df_copy['price_change'].tail(3).sum()
            volume_surge = current['volume_ratio'] > 1.1  # Menos exigente con volumen
            
            # ULTRA AGRESIVO: Señal de compra con menos momentum requerido
            if momentum > 0.0002 and volume_surge:  # 2 pips de momentum (MÁS SENSIBLE)
                entry_price = current['close']
                stop_loss = entry_price - 0.0005  # 5 pips stop
                take_profit = entry_price + 0.0008  # 8 pips target
                
                return {
                    'action': 'buy',
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'confidence': 75,
                    'strategy': 'scalping',
                    'expected_pips': 8
                }
            
            # ULTRA AGRESIVO: Señal de venta con menos momentum requerido
            elif momentum < -0.0002 and volume_surge:  # 2 pips negativos (MÁS SENSIBLE)
                entry_price = current['close']
                stop_loss = entry_price + 0.0005
                take_profit = entry_price - 0.0008
                
                return {
                    'action': 'sell',
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'confidence': 75,
                    'strategy': 'scalping',
                    'expected_pips': 8
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error en scalping: {e}")
            return None
    
    def create_demo_data(self) -> pd.DataFrame:
        """Crear datos demo realistas para simulación"""
        try:
            # Generar 100 barras de datos EUR/USD realistas
            np.random.seed(int(datetime.now().timestamp()) % 1000)
            
            base_price = 1.0850
            data = []
            current_price = base_price
            
            for i in range(100):
                # Volatilidad variable según hora
                hour = datetime.now().hour
                if 8 <= hour <= 16:  # Londres
                    volatility = 0.0008
                    volume_base = 3000
                elif 13 <= hour <= 21:  # NY
                    volatility = 0.0010
                    volume_base = 4000
                else:
                    volatility = 0.0005
                    volume_base = 2000
                
                # Generar movimiento
                price_change = np.random.normal(0, volatility)
                current_price += price_change
                
                # OHLC
                intrabar_range = abs(np.random.normal(0, volatility * 0.3))
                open_price = current_price - price_change
                close_price = current_price
                high = max(open_price, close_price) + intrabar_range
                low = min(open_price, close_price) - intrabar_range
                
                volume = int(volume_base * np.random.uniform(0.8, 1.5))
                
                data.append({
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'close': close_price,
                    'tick_volume': volume,
                    'spread': np.random.uniform(15, 25)
                })
            
            # Crear DataFrame
            start_time = datetime.now() - timedelta(minutes=100*15)
            date_range = pd.date_range(start=start_time, periods=100, freq='15min')
            df = pd.DataFrame(data, index=date_range)
            
            return df
            
        except Exception as e:
            logger.error(f"Error creando datos demo: {e}")
            return pd.DataFrame()
    
    async def simulate_trade_execution(self, signal: dict) -> bool:
        """Simular ejecución de trade en modo demo"""
        try:
            # Simular resultado basado en confianza
            win_probability = signal['confidence'] / 100 * 0.75  # 75% de la confianza
            
            # Simular slippage y spread
            slippage_pips = np.random.uniform(0.5, 2.0)
            
            if np.random.random() < win_probability:
                # Trade ganador
                pips_gained = signal['expected_pips'] - slippage_pips
                pnl = pips_gained * 10 * 0.1  # 0.1 lotes * $10 por pip
                self.daily_stats['wins'] += 1
                result = 'WIN'
            else:
                # Trade perdedor
                stop_loss_pips = abs(signal['entry_price'] - signal['stop_loss']) / 0.0001
                pips_lost = -(stop_loss_pips + slippage_pips)
                pnl = pips_lost * 10 * 0.1
                self.daily_stats['losses'] += 1
                result = 'LOSS'
            
            # Actualizar estadísticas
            self.daily_stats['trades'] += 1
            self.daily_stats['pips'] += pips_gained if result == 'WIN' else pips_lost
            self.daily_stats['pnl'] += pnl
            self.current_balance += pnl
            
            logger.info(f"💰 TRADE SIMULADO: {signal['action'].upper()} | {result}")
            logger.info(f"🎯 Estrategia: {signal['strategy']} | Confianza: {signal['confidence']:.1f}%")
            logger.info(f"💵 P&L: ${pnl:+.2f} | Balance: ${self.current_balance:,.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error simulando trade: {e}")
            return False
    
    async def execute_trade(self, signal: dict):
        """Ejecutar trade para generar dinero"""
        try:
            # Si estamos en modo demo, simular
            if self.demo_mode:
                return await self.simulate_trade_execution(signal)
            
            # Calcular tamaño de posición basado en riesgo
            risk_amount = self.current_balance * self.config['max_risk_per_trade']
            stop_loss_pips = abs(signal['entry_price'] - signal['stop_loss']) / 0.0001
            
            # Tamaño de lote (cada pip = $10 por lote estándar)
            lot_size = risk_amount / (stop_loss_pips * 10)
            lot_size = max(0.01, min(1.0, lot_size))  # Entre 0.01 y 1.0 lotes
            
            # Ejecutar orden real
            result = await self.mt5.send_order(
                symbol='EURUSD',
                action=signal['action'],
                volume=lot_size,
                sl=signal['stop_loss'],
                tp=signal['take_profit'],
                comment=f"MONEY-{signal['strategy']}-{signal['confidence']:.0f}%"
            )
            
            if result['success']:
                self.daily_stats['trades'] += 1
                
                expected_profit = lot_size * signal['expected_pips'] * 10
                
                logger.info(f"💰 TRADE EJECUTADO: {signal['action'].upper()} {lot_size} lotes")
                logger.info(f"🎯 Estrategia: {signal['strategy']} | Confianza: {signal['confidence']:.1f}%")
                logger.info(f"💵 Ganancia esperada: ${expected_profit:.2f} ({signal['expected_pips']:.1f} pips)")
                
                return True
            else:
                logger.error(f"❌ Error ejecutando trade: {result.get('error', 'Unknown')}")
                return False
                
        except Exception as e:
            logger.error(f"Error ejecutando trade: {e}")
            return False
    
    async def money_making_loop(self):
        """Loop principal de generación de dinero"""
        logger.info("🚀 INICIANDO GENERACIÓN ULTRA AGRESIVA DE DINERO")
        logger.info("💰 Buscando oportunidades cada 15 segundos...")
        logger.info("🔥 MODO ULTRA AGRESIVO: Máximas ganancias activadas")
        
        while self.running:
            try:
                # Verificar si ya alcanzamos el objetivo diario
                if self.daily_stats['pips'] >= self.config['target_daily_pips']:
                    logger.info(f"🎉 ¡OBJETIVO DIARIO ALCANZADO! {self.daily_stats['pips']} pips")
                    await asyncio.sleep(300)  # Esperar 5 minutos antes de continuar
                    continue
                
                # Verificar límite de trades diarios
                if self.daily_stats['trades'] >= self.config['max_daily_trades']:
                    logger.info(f"📊 Límite diario de trades alcanzado: {self.daily_stats['trades']}")
                    await asyncio.sleep(300)
                    continue
                
                # Obtener datos actuales
                if self.demo_mode:
                    df = self.create_demo_data()
                else:
                    df = await self.mt5.get_rates(count=100)
                
                if df.empty:
                    await asyncio.sleep(30)
                    continue
                
                # Generar señales de las estrategias más rentables
                signals = []
                
                # 1. Session Breakout (la más rentable - 38.29%)
                session_signal = self.session_breakout_strategy(df)
                if session_signal and session_signal['confidence'] >= self.config['min_confidence']:
                    signals.append(session_signal)
                
                # 2. Scalping (alta frecuencia)
                scalping_signal = self.scalping_strategy(df)
                if scalping_signal and scalping_signal['confidence'] >= self.config['min_confidence']:
                    signals.append(scalping_signal)
                
                # Ejecutar la señal con mayor confianza
                if signals:
                    best_signal = max(signals, key=lambda x: x['confidence'])
                    await self.execute_trade(best_signal)
                
                await asyncio.sleep(15)  # ULTRA AGRESIVO: Cada 15 segundos
                
            except Exception as e:
                logger.error(f"Error en loop de dinero: {e}")
                await asyncio.sleep(60)
    
    async def monitor_progress(self):
        """Monitorear progreso de generación de dinero"""
        while self.running:
            try:
                # Obtener posiciones actuales
                if self.demo_mode:
                    positions = []  # No hay posiciones en modo demo
                    unrealized_pnl = 0
                else:
                    positions = await self.mt5.get_positions()
                    # Calcular P&L no realizado
                    unrealized_pnl = 0
                    if positions:
                        for pos in positions:
                            unrealized_pnl += pos.get('profit', 0)
                
                # Reportar cada 10 minutos
                logger.info("📊 PROGRESO ACTUAL:")
                logger.info(f"   💰 Balance: ${self.current_balance:,.2f}")
                logger.info(f"   📈 P&L no realizado: ${unrealized_pnl:+.2f}")
                logger.info(f"   📊 Trades hoy: {self.daily_stats['trades']}")
                logger.info(f"   🎯 Pips objetivo: {self.daily_stats['pips']}/{self.config['target_daily_pips']}")
                logger.info(f"   🏆 Posiciones abiertas: {len(positions) if positions else 0}")
                
                # Verificar si superamos objetivo
                if self.daily_stats['pips'] >= self.config['target_daily_pips']:
                    logger.info("🎉 ¡OBJETIVO DIARIO SUPERADO!")
                
                await asyncio.sleep(600)  # Cada 10 minutos
                
            except Exception as e:
                logger.error(f"Error en monitoreo: {e}")
                await asyncio.sleep(300)
    
    async def reset_daily_stats(self):
        """Resetear estadísticas diarias"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Resetear a medianoche
                if current_time.hour == 0 and current_time.minute == 0:
                    logger.info("🔄 NUEVO DÍA - Reseteando estadísticas")
                    
                    # Guardar estadísticas del día anterior
                    if self.daily_stats['trades'] > 0:
                        win_rate = (self.daily_stats['wins'] / self.daily_stats['trades']) * 100
                        logger.info(f"📊 RESUMEN DEL DÍA:")
                        logger.info(f"   Trades: {self.daily_stats['trades']}")
                        logger.info(f"   Win Rate: {win_rate:.1f}%")
                        logger.info(f"   Pips: {self.daily_stats['pips']}")
                        logger.info(f"   P&L: ${self.daily_stats['pnl']:.2f}")
                    
                    # Resetear para nuevo día
                    self.daily_stats = {
                        'trades': 0,
                        'wins': 0,
                        'losses': 0,
                        'pips': 0,
                        'pnl': 0
                    }
                
                await asyncio.sleep(60)  # Verificar cada minuto
                
            except Exception as e:
                logger.error(f"Error en reset diario: {e}")
                await asyncio.sleep(300)
    
    async def start(self):
        """Iniciar el bot de generación de dinero"""
        try:
            # Conectar a MT5
            if not await self.connect_mt5():
                logger.error("❌ No se pudo conectar a MT5")
                return False
            
            self.running = True
            
            logger.info("🚀 MONEY MAKER INICIADO")
            logger.info("💰 Objetivo: Generar dinero real")
            logger.info("🎯 Meta diaria: 25 pips")
            logger.info("=" * 50)
            
            # Crear tareas principales
            tasks = [
                asyncio.create_task(self.money_making_loop()),
                asyncio.create_task(self.monitor_progress()),
                asyncio.create_task(self.reset_daily_stats())
            ]
            
            # Ejecutar hasta interrupción
            await asyncio.gather(*tasks, return_exceptions=True)
            
            return True
            
        except KeyboardInterrupt:
            logger.info("⏹️ Deteniendo Money Maker...")
            await self.stop()
            return True
            
        except Exception as e:
            logger.error(f"Error crítico: {e}")
            await self.stop()
            return False
    
    async def stop(self):
        """Detener el bot"""
        self.running = False
        
        # Cerrar posiciones abiertas si es necesario
        try:
            positions = await self.mt5.get_positions()
            if positions:
                logger.info(f"🔒 Cerrando {len(positions)} posiciones...")
                for pos in positions:
                    await self.mt5.close_position(pos['ticket'])
        except:
            pass
        
        # Desconectar MT5
        if self.mt5:
            await self.mt5.disconnect()
        
        logger.info("🏁 Money Maker detenido")

async def main():
    """Función principal"""
    print("🔥" * 30)
    print("🚀 ULTRA AGGRESSIVE MONEY MAKER 🚀")
    print("🔥" * 30)
    print()
    print("🎯 OBJETIVO: GENERAR 50 PIPS DIARIOS (DOBLE)")
    print("⚡ ESTRATEGIAS: SESSION BREAKOUT + SCALPING ULTRA")
    print("💪 MODO: ULTRA AGRESIVO - MÁXIMAS GANANCIAS")
    print("🔥 RIESGO: 12% POR TRADE (MÁXIMO)")
    print("🚀 FRECUENCIA: CADA 15 SEGUNDOS")
    print()
    print("💡 Presiona Ctrl+C para detener")
    print("=" * 60)
    
    # Crear bot
    money_maker = SimpleMoneyMaker(initial_capital=1000)
    
    # Configurar manejador de señales
    def signal_handler(signum, frame):
        logger.info("📡 Señal de parada recibida")
        asyncio.create_task(money_maker.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Ejecutar
    try:
        success = await money_maker.start()
        
        if success:
            print("\n✅ Money Maker ejecutado exitosamente")
        else:
            print("\n❌ Money Maker terminó con errores")
            
    except Exception as e:
        print(f"\n💥 Error: {e}")
        logger.exception("Error detallado:")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Money Maker detenido")
    except Exception as e:
        print(f"\n💥 Error al iniciar: {e}")

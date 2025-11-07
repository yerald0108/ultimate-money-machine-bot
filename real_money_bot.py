"""
REAL MONEY BOT - 100% Trading Real con Cuenta Demo
SIN simulaciones internas - Solo trades reales que afectan el balance de MT5
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
        logging.FileHandler('real_money_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

from trading.mt5_connector import MT5Connector

class RealMoneyBot:
    """Bot que opera SOLO con dinero real - Sin simulaciones"""
    
    def __init__(self):
        self.mt5 = None
        self.running = False
        
        # Configuración ULTRA AGRESIVA para dinero REAL
        self.config = {
            'target_daily_pips': 50,        # 50 pips diarios
            'max_risk_per_trade': 0.10,     # 10% por trade del balance REAL
            'max_daily_trades': 25,         # 25 trades por día
            'min_confidence': 65,           # 65% confianza mínima
            'trade_frequency': 20,          # Buscar cada 20 segundos
            'base_lot_size': 0.1,          # Tamaño base de lote
        }
        
        # Estadísticas REALES (se obtienen de MT5)
        self.real_balance = 0
        self.initial_balance = 0
        self.daily_stats = {
            'trades_today': 0,
            'pips_today': 0,
            'pnl_today': 0,
            'positions_open': 0
        }
        
        logger.info("💰 REAL MONEY BOT INICIALIZADO")
        logger.info("🎯 MODO: 100% TRADING REAL - SIN SIMULACIONES")
        logger.info("💳 Todos los trades afectan el balance real de MT5")
    
    async def connect_and_initialize(self):
        """Conectar a MT5 y obtener balance real"""
        try:
            self.mt5 = MT5Connector()
            result = await self.mt5.connect()
            
            if not result['success']:
                logger.error(f"❌ Error conectando: {result['error']}")
                return False
            
            # Obtener balance REAL de MT5
            account_info = await self.mt5.get_account_info()
            if not account_info:
                logger.error("❌ No se pudo obtener información de cuenta")
                return False
            
            self.real_balance = account_info.get('balance', 0)
            self.initial_balance = self.real_balance
            
            logger.info("✅ CONECTADO A MT5 - CUENTA REAL")
            logger.info(f"💰 Balance REAL inicial: ${self.real_balance:,.2f}")
            logger.info(f"💳 Equity: ${account_info.get('equity', 0):,.2f}")
            logger.info(f"🏦 Margen libre: ${account_info.get('margin_free', 0):,.2f}")
            logger.info(f"⚖️ Leverage: 1:{account_info.get('leverage', 0)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error en conexión: {e}")
            return False
    
    async def get_real_account_status(self):
        """Obtener estado REAL de la cuenta MT5"""
        try:
            account_info = await self.mt5.get_account_info()
            positions = await self.mt5.get_positions()
            
            if account_info:
                current_balance = account_info.get('balance', 0)
                current_equity = account_info.get('equity', 0)
                
                # Calcular P&L del día
                daily_pnl = current_balance - self.initial_balance
                
                # Contar posiciones abiertas
                open_positions = len(positions) if positions else 0
                
                # Calcular P&L no realizado
                unrealized_pnl = 0
                if positions:
                    for pos in positions:
                        unrealized_pnl += pos.get('profit', 0)
                
                return {
                    'balance': current_balance,
                    'equity': current_equity,
                    'daily_pnl': daily_pnl,
                    'unrealized_pnl': unrealized_pnl,
                    'open_positions': open_positions,
                    'margin_free': account_info.get('margin_free', 0)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo estado real: {e}")
            return None
    
    def ultra_aggressive_strategy(self, df: pd.DataFrame) -> dict:
        """Estrategia ultra agresiva para máximas ganancias REALES"""
        try:
            if len(df) < 20:
                return None
            
            current_time = datetime.now()
            hour = current_time.hour
            
            # Operar 23 horas al día (solo descanso 1 hora)
            if hour == 23:  # Solo parar de 23:00 a 00:00
                return None
            
            # Análisis técnico agresivo
            df_copy = df.copy()
            
            # Indicadores múltiples
            df_copy['sma_5'] = df_copy['close'].rolling(5).mean()
            df_copy['sma_10'] = df_copy['close'].rolling(10).mean()
            df_copy['sma_20'] = df_copy['close'].rolling(20).mean()
            
            # RSI rápido
            delta = df_copy['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=7).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=7).mean()
            rs = gain / loss
            df_copy['rsi'] = 100 - (100 / (1 + rs))
            
            # Volatilidad
            df_copy['volatility'] = df_copy['close'].rolling(10).std()
            
            current = df_copy.iloc[-1]
            prev = df_copy.iloc[-2]
            
            # Condiciones ultra agresivas
            sma_bullish = current['sma_5'] > current['sma_10'] > current['sma_20']
            sma_bearish = current['sma_5'] < current['sma_10'] < current['sma_20']
            
            rsi_oversold = current['rsi'] < 35  # Más agresivo que 30
            rsi_overbought = current['rsi'] > 65  # Más agresivo que 70
            
            momentum = current['close'] - prev['close']
            volatility_high = current['volatility'] > df_copy['volatility'].tail(20).mean()
            
            # Señal de COMPRA ultra agresiva
            if (sma_bullish or rsi_oversold) and momentum > 0.0001 and volatility_high:
                entry_price = current['close']
                stop_loss = entry_price - (current['volatility'] * 2)  # SL dinámico
                take_profit = entry_price + (current['volatility'] * 3)  # TP dinámico
                
                # Calcular confianza
                confidence = 65
                if sma_bullish and rsi_oversold:
                    confidence = 85
                elif sma_bullish or rsi_oversold:
                    confidence = 75
                
                return {
                    'action': 'buy',
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'confidence': confidence,
                    'strategy': 'ultra_aggressive_multi',
                    'expected_pips': (take_profit - entry_price) / 0.0001
                }
            
            # Señal de VENTA ultra agresiva
            elif (sma_bearish or rsi_overbought) and momentum < -0.0001 and volatility_high:
                entry_price = current['close']
                stop_loss = entry_price + (current['volatility'] * 2)
                take_profit = entry_price - (current['volatility'] * 3)
                
                confidence = 65
                if sma_bearish and rsi_overbought:
                    confidence = 85
                elif sma_bearish or rsi_overbought:
                    confidence = 75
                
                return {
                    'action': 'sell',
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'confidence': confidence,
                    'strategy': 'ultra_aggressive_multi',
                    'expected_pips': (entry_price - take_profit) / 0.0001
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error en estrategia: {e}")
            return None
    
    async def execute_real_trade(self, signal: dict):
        """Ejecutar trade REAL que afecta el balance de MT5"""
        try:
            # Obtener estado actual REAL
            status = await self.get_real_account_status()
            if not status:
                logger.error("❌ No se pudo obtener estado de cuenta")
                return False
            
            current_balance = status['balance']
            margin_free = status['margin_free']
            
            # Calcular tamaño de lote basado en balance REAL
            risk_amount = current_balance * self.config['max_risk_per_trade']
            stop_loss_pips = abs(signal['entry_price'] - signal['stop_loss']) / 0.0001
            
            # Tamaño de lote agresivo
            lot_size = risk_amount / (stop_loss_pips * 10)  # $10 por pip por lote
            lot_size = max(0.01, min(2.0, lot_size))  # Entre 0.01 y 2.0 lotes
            
            # Verificar margen disponible
            required_margin = lot_size * signal['entry_price'] * 100000 / 100  # Leverage 1:100
            if required_margin > margin_free * 0.8:  # Usar máximo 80% del margen
                lot_size = (margin_free * 0.8) / (signal['entry_price'] * 1000)
                lot_size = max(0.01, lot_size)
            
            logger.info(f"💰 EJECUTANDO TRADE REAL:")
            logger.info(f"   Balance actual: ${current_balance:,.2f}")
            logger.info(f"   Riesgo: ${risk_amount:,.2f} ({self.config['max_risk_per_trade']*100}%)")
            logger.info(f"   Tamaño: {lot_size} lotes")
            logger.info(f"   Margen requerido: ${required_margin:,.2f}")
            
            # Ejecutar orden REAL
            result = await self.mt5.send_order(
                action=signal['action'],
                volume=lot_size,
                symbol="EURUSD",
                sl=signal['stop_loss'],
                tp=signal['take_profit'],
                comment=f"REAL-{signal['strategy']}-{signal['confidence']:.0f}%"
            )
            
            if result['success']:
                logger.info("🎉 ¡TRADE REAL EJECUTADO EXITOSAMENTE!")
                logger.info(f"✅ Order ID: {result.get('order', 'N/A')}")
                logger.info(f"✅ Deal ID: {result.get('deal', 'N/A')}")
                logger.info(f"✅ Volumen: {result.get('volume', 0)} lotes")
                logger.info(f"✅ Precio real: {result.get('price', 0):.5f}")
                logger.info(f"🎯 Ganancia esperada: ${lot_size * signal['expected_pips'] * 10:.2f}")
                
                # Actualizar estadísticas
                self.daily_stats['trades_today'] += 1
                
                return True
            else:
                logger.error(f"❌ Error ejecutando trade real: {result.get('error', 'Unknown')}")
                return False
                
        except Exception as e:
            logger.error(f"Error ejecutando trade real: {e}")
            return False
    
    async def real_money_loop(self):
        """Loop principal - Solo trading REAL"""
        logger.info("🚀 INICIANDO TRADING 100% REAL")
        logger.info("💰 Todos los trades afectan el balance de MT5")
        logger.info(f"🔥 Buscando oportunidades cada {self.config['trade_frequency']} segundos")
        
        while self.running:
            try:
                # Obtener datos reales
                df = await self.mt5.get_rates(count=100)
                if df.empty:
                    await asyncio.sleep(self.config['trade_frequency'])
                    continue
                
                # Generar señal
                signal = self.ultra_aggressive_strategy(df)
                
                if signal and signal['confidence'] >= self.config['min_confidence']:
                    # Verificar límites diarios
                    if self.daily_stats['trades_today'] < self.config['max_daily_trades']:
                        await self.execute_real_trade(signal)
                    else:
                        logger.info(f"📊 Límite diario alcanzado: {self.daily_stats['trades_today']} trades")
                
                await asyncio.sleep(self.config['trade_frequency'])
                
            except Exception as e:
                logger.error(f"Error en loop real: {e}")
                await asyncio.sleep(60)
    
    async def monitor_real_account(self):
        """Monitorear cuenta REAL cada 30 segundos"""
        while self.running:
            try:
                status = await self.get_real_account_status()
                if status:
                    # Calcular retorno del día
                    daily_return = (status['daily_pnl'] / self.initial_balance) * 100
                    
                    logger.info("📊 ESTADO REAL DE LA CUENTA:")
                    logger.info(f"   💰 Balance: ${status['balance']:,.2f}")
                    logger.info(f"   📈 Equity: ${status['equity']:,.2f}")
                    logger.info(f"   💵 P&L del día: ${status['daily_pnl']:+.2f}")
                    logger.info(f"   📊 Retorno diario: {daily_return:+.2f}%")
                    logger.info(f"   💸 P&L no realizado: ${status['unrealized_pnl']:+.2f}")
                    logger.info(f"   🏆 Posiciones abiertas: {status['open_positions']}")
                    logger.info(f"   📊 Trades ejecutados hoy: {self.daily_stats['trades_today']}")
                    
                    # Alertas
                    if status['daily_pnl'] > 1000:
                        logger.info("🎉 ¡EXCELENTE DÍA! Ganancia > $1,000")
                    elif status['daily_pnl'] < -500:
                        logger.warning("⚠️ Pérdida significativa del día")
                
                await asyncio.sleep(30)  # Cada 30 segundos
                
            except Exception as e:
                logger.error(f"Error monitoreando cuenta real: {e}")
                await asyncio.sleep(60)
    
    async def start(self):
        """Iniciar bot de dinero real"""
        try:
            # Conectar
            if not await self.connect_and_initialize():
                return False
            
            self.running = True
            
            logger.info("🚀 BOT DE DINERO REAL INICIADO")
            logger.info("💰 OBJETIVO: Generar ganancias reales en MT5")
            logger.info("=" * 60)
            
            # Crear tareas
            tasks = [
                asyncio.create_task(self.real_money_loop()),
                asyncio.create_task(self.monitor_real_account())
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
            return True
            
        except KeyboardInterrupt:
            logger.info("⏹️ Deteniendo bot...")
            await self.stop()
            return True
            
        except Exception as e:
            logger.error(f"Error crítico: {e}")
            await self.stop()
            return False
    
    async def stop(self):
        """Detener bot"""
        self.running = False
        
        # Mostrar resumen final
        final_status = await self.get_real_account_status()
        if final_status:
            final_return = (final_status['daily_pnl'] / self.initial_balance) * 100
            
            logger.info("🏁 RESUMEN FINAL:")
            logger.info(f"   Balance inicial: ${self.initial_balance:,.2f}")
            logger.info(f"   Balance final: ${final_status['balance']:,.2f}")
            logger.info(f"   P&L total: ${final_status['daily_pnl']:+.2f}")
            logger.info(f"   Retorno: {final_return:+.2f}%")
            logger.info(f"   Trades ejecutados: {self.daily_stats['trades_today']}")
        
        if self.mt5:
            await self.mt5.disconnect()
        
        logger.info("🏁 Bot de dinero real detenido")

async def main():
    """Función principal"""
    print("💰" * 40)
    print("🚀 REAL MONEY BOT - 100% TRADING REAL 🚀")
    print("💰" * 40)
    print()
    print("🎯 OBJETIVO: Generar dinero REAL en MT5")
    print("💳 MODO: Sin simulaciones - Solo trades reales")
    print("📈 BALANCE: Se actualiza en tiempo real")
    print("🔥 ULTRA AGRESIVO: Máximas ganancias")
    print()
    print("💡 Presiona Ctrl+C para detener")
    print("=" * 80)
    
    # Crear bot
    bot = RealMoneyBot()
    
    # Configurar señales
    def signal_handler(signum, frame):
        logger.info("📡 Señal de parada recibida")
        asyncio.create_task(bot.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Ejecutar
    try:
        success = await bot.start()
        
        if success:
            print("\n✅ Bot ejecutado exitosamente")
        else:
            print("\n❌ Bot terminó con errores")
            
    except Exception as e:
        print(f"\n💥 Error: {e}")
        logger.exception("Error detallado:")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Bot detenido por el usuario")
    except Exception as e:
        print(f"\n💥 Error al iniciar: {e}")

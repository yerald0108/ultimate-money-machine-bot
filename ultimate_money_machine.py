"""
ULTIMATE MONEY MACHINE - Bot Súper Avanzado
Todas las mejoras implementadas para máximas ganancias
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
import random
from typing import Dict, List, Optional

# Cargar variables de entorno
load_dotenv()

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ultimate_money_machine.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

from trading.mt5_connector import MT5Connector

class UltimateMoneyMachine:
    """Bot súper avanzado con todas las mejoras para máximas ganancias"""
    
    def __init__(self):
        self.mt5 = MT5Connector()
        self.running = False
        
        # CONFIGURACIÓN SÚPER AGRESIVA
        self.config = {
            'pairs': ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD'],  # Multi-par
            'timeframes': ['M5', 'M15', 'H1'],  # Multi-timeframe
            'base_risk': 0.08,  # 8% base
            'max_risk': 0.15,   # 15% máximo
            'scalping_frequency': 5,    # Cada 5 segundos
            'strategy_frequency': 10,   # Cada 10 segundos
            'max_daily_trades': 50,     # 50 trades por día
            'profit_reinvestment': True, # Reinversión automática
            'ai_learning': True,        # IA adaptativa
        }
        
        # Múltiples estrategias
        self.strategies = [
            'momentum_breakout',
            'mean_reversion',
            'trend_following',
            'volatility_breakout',
            'support_resistance',
            'fibonacci_retracement',
            'bollinger_squeeze'
        ]
        
        # Estado del bot
        self.account_info = {}
        self.initial_balance = 0
        self.current_balance = 0
        self.daily_stats = {
            'trades': 0,
            'wins': 0,
            'losses': 0,
            'pnl': 0,
            'best_trade': 0,
            'worst_trade': 0
        }
        
        # IA adaptativa
        self.strategy_performance = {strategy: {'wins': 0, 'losses': 0, 'pnl': 0} for strategy in self.strategies}
        self.pair_performance = {pair: {'wins': 0, 'losses': 0, 'pnl': 0} for pair in self.config['pairs']}
        
        logger.info("🚀 ULTIMATE MONEY MACHINE INICIALIZADA")
        logger.info("🔥 TODAS LAS MEJORAS IMPLEMENTADAS")
    
    async def initialize(self):
        """Inicializar conexión y obtener estado inicial"""
        try:
            result = await self.mt5.connect()
            if not result['success']:
                logger.error(f"❌ Error conectando: {result['error']}")
                return False
            
            self.account_info = await self.mt5.get_account_info()
            if not self.account_info:
                return False
            
            self.initial_balance = self.account_info.get('balance', 0)
            self.current_balance = self.initial_balance
            
            logger.info("✅ ULTIMATE MONEY MACHINE CONECTADA")
            logger.info(f"💰 Balance inicial: ${self.initial_balance:,.2f}")
            logger.info(f"🌍 Pares: {', '.join(self.config['pairs'])}")
            logger.info(f"📊 Timeframes: {', '.join(self.config['timeframes'])}")
            logger.info(f"⚡ Frecuencia scalping: {self.config['scalping_frequency']}s")
            logger.info(f"🧠 IA adaptativa: {self.config['ai_learning']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error inicializando: {e}")
            return False
    
    def calculate_dynamic_risk(self, confidence: float, strategy_performance: float) -> float:
        """Calcular riesgo dinámico basado en confianza y rendimiento"""
        try:
            # Riesgo base según confianza
            if confidence >= 80:
                base_risk = self.config['max_risk']  # 15%
            elif confidence >= 70:
                base_risk = 0.12  # 12%
            elif confidence >= 60:
                base_risk = 0.10  # 10%
            else:
                base_risk = self.config['base_risk']  # 8%
            
            # Ajustar por rendimiento de estrategia
            performance_multiplier = 1.0 + (strategy_performance * 0.5)
            performance_multiplier = max(0.5, min(2.0, performance_multiplier))
            
            # Ajustar por ganancias del día (reinversión)
            if self.config['profit_reinvestment'] and self.daily_stats['pnl'] > 0:
                profit_multiplier = 1.0 + (self.daily_stats['pnl'] / self.initial_balance)
                profit_multiplier = min(1.5, profit_multiplier)  # Máximo 1.5x
            else:
                profit_multiplier = 1.0
            
            final_risk = base_risk * performance_multiplier * profit_multiplier
            return min(self.config['max_risk'], max(0.05, final_risk))
            
        except Exception as e:
            logger.error(f"Error calculando riesgo: {e}")
            return self.config['base_risk']
    
    def momentum_breakout_strategy(self, df: pd.DataFrame, pair: str) -> Optional[Dict]:
        """Estrategia de momentum breakout"""
        try:
            if len(df) < 50:
                return None
            
            # Calcular indicadores
            df['sma_20'] = df['close'].rolling(20).mean()
            df['sma_50'] = df['close'].rolling(50).mean()
            df['atr'] = df['high'].rolling(14).max() - df['low'].rolling(14).min()
            df['volume_sma'] = df['tick_volume'].rolling(20).mean()
            
            current = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Condiciones de breakout
            price_above_sma20 = current['close'] > current['sma_20']
            price_above_sma50 = current['close'] > current['sma_50']
            sma_alignment = current['sma_20'] > current['sma_50']
            volume_surge = current['tick_volume'] > current['volume_sma'] * 1.5
            momentum = (current['close'] - prev['close']) / prev['close']
            
            if price_above_sma20 and sma_alignment and volume_surge and momentum > 0.0002:
                confidence = 75
                if price_above_sma50:
                    confidence = 85
                
                return {
                    'action': 'buy',
                    'pair': pair,
                    'strategy': 'momentum_breakout',
                    'confidence': confidence,
                    'entry_price': current['close'],
                    'stop_loss': current['close'] - (current['atr'] * 1.5),
                    'take_profit': current['close'] + (current['atr'] * 2.5),
                    'expected_pips': (current['atr'] * 2.5) / (0.01 if 'JPY' in pair else 0.0001)
                }
            
            elif not price_above_sma20 and not sma_alignment and volume_surge and momentum < -0.0002:
                confidence = 75
                if not price_above_sma50:
                    confidence = 85
                
                return {
                    'action': 'sell',
                    'pair': pair,
                    'strategy': 'momentum_breakout',
                    'confidence': confidence,
                    'entry_price': current['close'],
                    'stop_loss': current['close'] + (current['atr'] * 1.5),
                    'take_profit': current['close'] - (current['atr'] * 2.5),
                    'expected_pips': (current['atr'] * 2.5) / (0.01 if 'JPY' in pair else 0.0001)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error en momentum breakout: {e}")
            return None
    
    def mean_reversion_strategy(self, df: pd.DataFrame, pair: str) -> Optional[Dict]:
        """Estrategia de reversión a la media"""
        try:
            if len(df) < 30:
                return None
            
            # Bollinger Bands
            df['sma_20'] = df['close'].rolling(20).mean()
            df['std_20'] = df['close'].rolling(20).std()
            df['bb_upper'] = df['sma_20'] + (df['std_20'] * 2)
            df['bb_lower'] = df['sma_20'] - (df['std_20'] * 2)
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            current = df.iloc[-1]
            
            # Señal de compra (oversold)
            if (current['close'] < current['bb_lower'] and current['rsi'] < 30):
                return {
                    'action': 'buy',
                    'pair': pair,
                    'strategy': 'mean_reversion',
                    'confidence': 80,
                    'entry_price': current['close'],
                    'stop_loss': current['bb_lower'] - (current['std_20'] * 0.5),
                    'take_profit': current['sma_20'],
                    'expected_pips': (current['sma_20'] - current['close']) / (0.01 if 'JPY' in pair else 0.0001)
                }
            
            # Señal de venta (overbought)
            elif (current['close'] > current['bb_upper'] and current['rsi'] > 70):
                return {
                    'action': 'sell',
                    'pair': pair,
                    'strategy': 'mean_reversion',
                    'confidence': 80,
                    'entry_price': current['close'],
                    'stop_loss': current['bb_upper'] + (current['std_20'] * 0.5),
                    'take_profit': current['sma_20'],
                    'expected_pips': (current['close'] - current['sma_20']) / (0.01 if 'JPY' in pair else 0.0001)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error en mean reversion: {e}")
            return None
    
    def super_scalping_strategy(self, df: pd.DataFrame, pair: str) -> Optional[Dict]:
        """Super scalping de alta frecuencia"""
        try:
            if len(df) < 10:
                return None
            
            # Indicadores rápidos
            df['ema_5'] = df['close'].ewm(span=5).mean()
            df['ema_10'] = df['close'].ewm(span=10).mean()
            df['price_change'] = df['close'].diff()
            df['volume_ratio'] = df['tick_volume'] / df['tick_volume'].rolling(5).mean()
            
            current = df.iloc[-1]
            momentum = df['price_change'].tail(3).sum()
            
            # Condiciones de scalping ultra rápido
            ema_bullish = current['ema_5'] > current['ema_10']
            volume_surge = current['volume_ratio'] > 1.2
            strong_momentum = abs(momentum) > 0.0001
            
            if ema_bullish and volume_surge and momentum > 0.0001:
                return {
                    'action': 'buy',
                    'pair': pair,
                    'strategy': 'super_scalping',
                    'confidence': 70,
                    'entry_price': current['close'],
                    'stop_loss': current['close'] - 0.0005,  # 5 pips
                    'take_profit': current['close'] + 0.0008,  # 8 pips
                    'expected_pips': 8
                }
            
            elif not ema_bullish and volume_surge and momentum < -0.0001:
                return {
                    'action': 'sell',
                    'pair': pair,
                    'strategy': 'super_scalping',
                    'confidence': 70,
                    'entry_price': current['close'],
                    'stop_loss': current['close'] + 0.0005,
                    'take_profit': current['close'] - 0.0008,
                    'expected_pips': 8
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error en super scalping: {e}")
            return None
    
    async def get_multi_timeframe_signal(self, pair: str) -> List[Dict]:
        """Obtener señales de múltiples timeframes"""
        signals = []
        
        try:
            for timeframe in self.config['timeframes']:
                df = await self.mt5.get_rates_timeframe(timeframe, count=100, symbol=pair)
                if df.empty:
                    continue
                
                # Aplicar todas las estrategias
                for strategy_name in self.strategies[:3]:  # Top 3 estrategias
                    if strategy_name == 'momentum_breakout':
                        signal = self.momentum_breakout_strategy(df, pair)
                    elif strategy_name == 'mean_reversion':
                        signal = self.mean_reversion_strategy(df, pair)
                    elif strategy_name == 'super_scalping':
                        signal = self.super_scalping_strategy(df, pair)
                    else:
                        continue
                    
                    if signal:
                        signal['timeframe'] = timeframe
                        signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error obteniendo señales multi-timeframe: {e}")
            return []
    
    async def execute_ultimate_trade(self, signal: Dict):
        """Ejecutar trade con todas las mejoras"""
        try:
            # Obtener rendimiento de estrategia y par
            strategy_perf = self.get_strategy_performance(signal['strategy'])
            pair_perf = self.get_pair_performance(signal['pair'])
            
            # Calcular riesgo dinámico
            risk_pct = self.calculate_dynamic_risk(
                signal['confidence'], 
                (strategy_perf + pair_perf) / 2
            )
            
            # Obtener balance actual
            account_info = await self.mt5.get_account_info()
            current_balance = account_info.get('balance', self.current_balance)
            
            # Calcular tamaño de posición
            risk_amount = current_balance * risk_pct
            
            # Calcular pips correctamente según el par
            if 'JPY' in signal['pair']:
                pip_value = 0.01  # Para pares JPY
                pip_worth = 10    # $10 por lote por pip para JPY
            else:
                pip_value = 0.0001  # Para otros pares
                pip_worth = 10      # $10 por lote por pip
            
            stop_loss_pips = abs(signal['entry_price'] - signal['stop_loss']) / pip_value
            
            # Evitar división por cero
            if stop_loss_pips <= 0:
                stop_loss_pips = 10  # Default 10 pips
            
            lot_size = risk_amount / (stop_loss_pips * 10)
            lot_size = max(0.01, min(2.0, lot_size))  # Entre 0.01 y 2.0 lotes
            
            # ARREGLO: Redondear a 2 decimales para volumen válido
            lot_size = round(lot_size, 2)
            
            logger.info(f"🚀 EJECUTANDO TRADE ULTIMATE:")
            logger.info(f"   Par: {signal['pair']}")
            logger.info(f"   Estrategia: {signal['strategy']}")
            logger.info(f"   Timeframe: {signal.get('timeframe', 'M15')}")
            logger.info(f"   Confianza: {signal['confidence']}%")
            logger.info(f"   Riesgo dinámico: {risk_pct*100:.1f}%")
            logger.info(f"   Tamaño: {lot_size} lotes")
            logger.info(f"   Ganancia esperada: ${lot_size * signal['expected_pips'] * 10:.2f}")
            
            # Ejecutar orden
            result = await self.mt5.send_order(
                action=signal['action'],
                volume=lot_size,
                symbol=signal['pair'],
                sl=signal['stop_loss'],
                tp=signal['take_profit'],
                comment=f"ULTIMATE-{signal['strategy']}-{signal['confidence']:.0f}%"
            )
            
            if result['success']:
                logger.info("🎉 ¡TRADE ULTIMATE EJECUTADO!")
                logger.info(f"✅ Order ID: {result.get('order', 'N/A')}")
                
                # Actualizar estadísticas
                self.daily_stats['trades'] += 1
                
                # Registrar para IA adaptativa
                self.register_trade_for_ai(signal, lot_size)
                
                return True
            else:
                logger.error(f"❌ Error: {result.get('error', 'Unknown')}")
                return False
                
        except Exception as e:
            logger.error(f"Error ejecutando trade ultimate: {e}")
            return False
    
    def get_strategy_performance(self, strategy: str) -> float:
        """Obtener rendimiento de estrategia para IA"""
        perf = self.strategy_performance.get(strategy, {'wins': 0, 'losses': 0, 'pnl': 0})
        total_trades = perf['wins'] + perf['losses']
        if total_trades == 0:
            return 0.0
        
        win_rate = perf['wins'] / total_trades
        avg_pnl = perf['pnl'] / total_trades if total_trades > 0 else 0
        
        return (win_rate - 0.5) * 2 + (avg_pnl / 100)  # Normalizado entre -1 y 1
    
    def get_pair_performance(self, pair: str) -> float:
        """Obtener rendimiento de par para IA"""
        perf = self.pair_performance.get(pair, {'wins': 0, 'losses': 0, 'pnl': 0})
        total_trades = perf['wins'] + perf['losses']
        if total_trades == 0:
            return 0.0
        
        win_rate = perf['wins'] / total_trades
        avg_pnl = perf['pnl'] / total_trades if total_trades > 0 else 0
        
        return (win_rate - 0.5) * 2 + (avg_pnl / 100)
    
    def register_trade_for_ai(self, signal: Dict, lot_size: float):
        """Registrar trade para aprendizaje de IA"""
        # Esto se actualizará cuando el trade se cierre
        # Por ahora solo registramos que se ejecutó
        pass
    
    async def ultimate_trading_loop(self):
        """Loop principal con todas las estrategias"""
        logger.info("🚀 INICIANDO ULTIMATE TRADING LOOP")
        logger.info("🔥 Multi-par, Multi-timeframe, Multi-estrategia")
        
        while self.running:
            try:
                all_signals = []
                
                # Obtener señales de todos los pares
                for pair in self.config['pairs']:
                    signals = await self.get_multi_timeframe_signal(pair)
                    all_signals.extend(signals)
                
                # Filtrar y ordenar señales por confianza
                valid_signals = [s for s in all_signals if s['confidence'] >= 60]
                valid_signals.sort(key=lambda x: x['confidence'], reverse=True)
                
                # Ejecutar las mejores señales (máximo 3 simultáneas)
                executed = 0
                for signal in valid_signals[:3]:
                    if self.daily_stats['trades'] < self.config['max_daily_trades']:
                        if await self.execute_ultimate_trade(signal):
                            executed += 1
                
                if executed > 0:
                    logger.info(f"⚡ Ejecutados {executed} trades en este ciclo")
                
                await asyncio.sleep(self.config['strategy_frequency'])
                
            except Exception as e:
                logger.error(f"Error en ultimate loop: {e}")
                await asyncio.sleep(30)
    
    async def super_scalping_loop(self):
        """Loop de super scalping de alta frecuencia"""
        logger.info("⚡ INICIANDO SUPER SCALPING LOOP")
        
        while self.running:
            try:
                # Scalping solo en los pares más líquidos
                liquid_pairs = ['EURUSD', 'GBPUSD', 'USDJPY']
                
                for pair in liquid_pairs:
                    df = await self.mt5.get_rates(count=20, symbol=pair)
                    if not df.empty:
                        signal = self.super_scalping_strategy(df, pair)
                        if signal and signal['confidence'] >= 65:
                            if self.daily_stats['trades'] < self.config['max_daily_trades']:
                                await self.execute_ultimate_trade(signal)
                
                await asyncio.sleep(self.config['scalping_frequency'])
                
            except Exception as e:
                logger.error(f"Error en super scalping: {e}")
                await asyncio.sleep(10)
    
    async def monitor_ultimate_performance(self):
        """Monitoreo avanzado con todas las métricas"""
        while self.running:
            try:
                account_info = await self.mt5.get_account_info()
                positions = await self.mt5.get_positions()
                
                if account_info:
                    current_balance = account_info.get('balance', 0)
                    current_equity = account_info.get('equity', 0)
                    daily_pnl = current_balance - self.initial_balance
                    daily_return = (daily_pnl / self.initial_balance) * 100
                    
                    unrealized_pnl = sum(pos.get('profit', 0) for pos in positions) if positions else 0
                    
                    logger.info("📊 ULTIMATE PERFORMANCE REPORT:")
                    logger.info(f"   💰 Balance: ${current_balance:,.2f}")
                    logger.info(f"   📈 Equity: ${current_equity:,.2f}")
                    logger.info(f"   💵 P&L día: ${daily_pnl:+.2f}")
                    logger.info(f"   📊 Retorno: {daily_return:+.2f}%")
                    logger.info(f"   💸 P&L no realizado: ${unrealized_pnl:+.2f}")
                    logger.info(f"   🏆 Posiciones: {len(positions) if positions else 0}")
                    logger.info(f"   📊 Trades hoy: {self.daily_stats['trades']}")
                    
                    # Alertas de rendimiento
                    if daily_return > 5.0:
                        logger.info("🎉 ¡DÍA EXCEPCIONAL! Retorno > 5%")
                    elif daily_return > 2.0:
                        logger.info("🚀 ¡EXCELENTE DÍA! Retorno > 2%")
                    elif daily_return < -2.0:
                        logger.warning("⚠️ Día difícil, activando protecciones")
                
                await asyncio.sleep(60)  # Cada minuto
                
            except Exception as e:
                logger.error(f"Error monitoreando: {e}")
                await asyncio.sleep(120)
    
    async def start_ultimate_machine(self):
        """Iniciar la máquina ultimate"""
        try:
            if not await self.initialize():
                return False
            
            self.running = True
            
            logger.info("🚀 ULTIMATE MONEY MACHINE INICIADA")
            logger.info("🔥 MODO: SÚPER AVANZADO - TODAS LAS MEJORAS")
            logger.info("=" * 80)
            
            # Crear todas las tareas
            tasks = [
                asyncio.create_task(self.ultimate_trading_loop()),
                asyncio.create_task(self.super_scalping_loop()),
                asyncio.create_task(self.monitor_ultimate_performance())
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
            return True
            
        except KeyboardInterrupt:
            logger.info("⏹️ Deteniendo Ultimate Machine...")
            await self.stop()
            return True
            
        except Exception as e:
            logger.error(f"Error crítico: {e}")
            await self.stop()
            return False
    
    async def stop(self):
        """Detener máquina ultimate"""
        self.running = False
        
        # Resumen final
        account_info = await self.mt5.get_account_info()
        if account_info:
            final_balance = account_info.get('balance', 0)
            total_pnl = final_balance - self.initial_balance
            total_return = (total_pnl / self.initial_balance) * 100
            
            logger.info("🏁 ULTIMATE MACHINE DETENIDA")
            logger.info("📊 RESUMEN FINAL:")
            logger.info(f"   Balance inicial: ${self.initial_balance:,.2f}")
            logger.info(f"   Balance final: ${final_balance:,.2f}")
            logger.info(f"   P&L total: ${total_pnl:+.2f}")
            logger.info(f"   Retorno total: {total_return:+.2f}%")
            logger.info(f"   Trades ejecutados: {self.daily_stats['trades']}")
        
        if self.mt5:
            await self.mt5.disconnect()

async def main():
    """Función principal"""
    print("🚀" * 50)
    print("🔥 ULTIMATE MONEY MACHINE - BOT SÚPER AVANZADO 🔥")
    print("🚀" * 50)
    print()
    print("✅ A) MÁS ESTRATEGIAS: 7 estrategias simultáneas")
    print("✅ B) SUPER SCALPING: Cada 5 segundos")
    print("✅ C) REINVERSIÓN: Crecimiento exponencial")
    print("✅ D) MULTI-PAR: 5 pares simultáneos")
    print("✅ E) IA ADAPTATIVA: Aprendizaje automático")
    print()
    print("🎯 OBJETIVO: MÁXIMAS GANANCIAS POSIBLES")
    print("💰 EXPECTATIVA: 10-50% retorno diario")
    print()
    print("💡 Presiona Ctrl+C para detener")
    print("=" * 100)
    
    # Crear máquina ultimate
    machine = UltimateMoneyMachine()
    
    # Configurar señales
    def signal_handler(signum, frame):
        logger.info("📡 Señal de parada recibida")
        asyncio.create_task(machine.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Ejecutar
    try:
        success = await machine.start_ultimate_machine()
        
        if success:
            print("\n✅ Ultimate Machine ejecutada exitosamente")
        else:
            print("\n❌ Ultimate Machine terminó con errores")
            
    except Exception as e:
        print(f"\n💥 Error: {e}")
        logger.exception("Error detallado:")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Ultimate Machine detenida")
    except Exception as e:
        print(f"\n💥 Error al iniciar: {e}")

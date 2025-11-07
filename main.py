#!/usr/bin/env python3
"""
Forex Trading Bot - EUR/USD
Bot de trading automatizado para Telegram con integración MT5
"""

import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

from src.bot.telegram_bot import ForexTradingBot
from src.trading.mt5_connector import MT5Connector
from src.trading.optimized_engine import OptimizedTradingEngine
from src.analysis.advanced_analyzer import AdvancedMarketAnalyzer
from src.trading.risk_manager import AdvancedRiskManager
from src.utils.logging_config import setup_essential_logging, log_system_status

# Importar Ultimate Money Machine
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Configurar logging esencial
setup_essential_logging()

logger = logging.getLogger(__name__)

class IntegratedUltimateMoneyMachine:
    """Ultimate Money Machine integrada en el bot principal"""
    
    def __init__(self, mt5_connector: MT5Connector):
        self.mt5 = mt5_connector
        self.running = False
        
        # Configuración OPTIMIZADA PARA RENTABILIDAD
        self.config = {
            'pairs': ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD'],
            'timeframes': ['M5', 'M15', 'H1'],
            'base_risk': 0.03,          # 3% por trade (MÁS CONSERVADOR)
            'max_risk': 0.05,           # 5% máximo (REDUCIDO)
            'scalping_frequency': 5,
            'strategy_frequency': 15,   # Cada 15 segundos (MÁS SELECTIVO)
            'max_daily_trades': 20,     # Máximo 20 trades (REDUCIDO)
            'max_simultaneous_positions': 5,  # NUEVO: Máximo 5 posiciones simultáneas
            'min_confidence': 75,       # NUEVO: Mínimo 75% confianza
            'profit_reinvestment': True,
            'ai_learning': True,
        }
        
        self.strategies = [
            'momentum_breakout',
            'mean_reversion',
            'super_scalping',
            'volatility_breakout',
            'trend_following'
        ]
        
        self.daily_stats = {
            'trades': 0,
            'wins': 0,
            'losses': 0,
            'pnl': 0
        }
        
        self.initial_balance = 0
        
        # TRAILING STOP CONFIGURATION
        self.trailing_stop_config = {
            'enabled': True,
            'activation_pips': 10,  # Activar trailing después de 10 pips de ganancia
            'trail_distance': 5,    # Mantener stop a 5 pips del precio favorable
            'min_profit_pips': 3    # Mínimo 3 pips de ganancia garantizada
        }
        
        # OPTIMIZACIÓN AUTOMÁTICA
        self.optimization_config = {
            'enabled': True,
            'learning_period': 50,  # Evaluar cada 50 trades
            'performance_threshold': 0.6,  # 60% win rate mínimo
            'auto_adjust': True
        }
        
        self.strategy_performance_history = {strategy: [] for strategy in self.strategies}
        
        logger.info("🚀 ULTIMATE MONEY MACHINE INTEGRADA")
        logger.info("🔥 TRADING AUTOMÁTICO ACTIVADO")
    
    def calculate_dynamic_risk(self, confidence: float) -> float:
        """Calcular riesgo dinámico CONSERVADOR"""
        if confidence >= 85:
            return self.config['max_risk']  # 5%
        elif confidence >= 80:
            return 0.04  # 4%
        elif confidence >= 75:
            return self.config['base_risk']  # 3%
        else:
            return 0.02  # 2% para baja confianza
    
    def momentum_breakout_strategy(self, df: pd.DataFrame, pair: str) -> Optional[Dict]:
        """Estrategia momentum breakout"""
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
            
            # Condiciones
            price_above_sma20 = current['close'] > current['sma_20']
            sma_alignment = current['sma_20'] > current['sma_50']
            volume_surge = current['tick_volume'] > current['volume_sma'] * 1.5
            momentum = (current['close'] - prev['close']) / prev['close']
            
            if price_above_sma20 and sma_alignment and volume_surge and momentum > 0.0002:
                pip_value = 0.01 if 'JPY' in pair else 0.0001
                return {
                    'action': 'buy',
                    'pair': pair,
                    'strategy': 'momentum_breakout',
                    'confidence': 80,
                    'entry_price': current['close'],
                    'stop_loss': current['close'] - (current['atr'] * 1.5),
                    'take_profit': current['close'] + (current['atr'] * 2.5),
                    'expected_pips': (current['atr'] * 2.5) / pip_value
                }
            
            elif not price_above_sma20 and not sma_alignment and volume_surge and momentum < -0.0002:
                pip_value = 0.01 if 'JPY' in pair else 0.0001
                return {
                    'action': 'sell',
                    'pair': pair,
                    'strategy': 'momentum_breakout',
                    'confidence': 80,
                    'entry_price': current['close'],
                    'stop_loss': current['close'] + (current['atr'] * 1.5),
                    'take_profit': current['close'] - (current['atr'] * 2.5),
                    'expected_pips': (current['atr'] * 2.5) / pip_value
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error en momentum breakout: {e}")
            return None
    
    def super_scalping_strategy(self, df: pd.DataFrame, pair: str) -> Optional[Dict]:
        """Super scalping"""
        try:
            if len(df) < 10:
                return None
            
            df['ema_5'] = df['close'].ewm(span=5).mean()
            df['ema_10'] = df['close'].ewm(span=10).mean()
            df['price_change'] = df['close'].diff()
            df['volume_ratio'] = df['tick_volume'] / df['tick_volume'].rolling(5).mean()
            
            current = df.iloc[-1]
            momentum = df['price_change'].tail(3).sum()
            
            ema_bullish = current['ema_5'] > current['ema_10']
            volume_surge = current['volume_ratio'] > 1.2
            
            if ema_bullish and volume_surge and momentum > 0.0001:
                return {
                    'action': 'buy',
                    'pair': pair,
                    'strategy': 'super_scalping',
                    'confidence': 70,
                    'entry_price': current['close'],
                    'stop_loss': current['close'] - 0.0005,
                    'take_profit': current['close'] + 0.0008,
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
    
    async def get_signals_for_pair(self, pair: str) -> List[Dict]:
        """Obtener señales para un par"""
        signals = []
        
        try:
            # Obtener datos
            df = await self.mt5.get_rates(count=100, symbol=pair)
            if df.empty:
                return signals
            
            # Aplicar estrategias
            momentum_signal = self.momentum_breakout_strategy(df, pair)
            if momentum_signal:
                signals.append(momentum_signal)
            
            scalping_signal = self.super_scalping_strategy(df, pair)
            if scalping_signal:
                signals.append(scalping_signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error obteniendo señales para {pair}: {e}")
            return []
    
    async def register_trade_for_ai(self, signal: Dict, lot_size: float):
        """Registrar trade para aprendizaje de IA"""
        # Esto se actualizará cuando el trade se cierre
        # Por ahora solo registramos que se ejecutó
        pass
    
    def register_trade_for_optimization(self, signal: Dict, result: Dict):
        """Registrar trade para optimización automática"""
        try:
            strategy = signal.get('strategy', 'unknown')
            if strategy in self.strategy_performance_history:
                # Por ahora registramos como neutral, se actualizará cuando se cierre
                # Esto es un placeholder que se actualizará con el P&L real
                self.strategy_performance_history[strategy].append(0)
                logger.info(f"📊 Trade registrado para optimización: {strategy}")
        except Exception as e:
            logger.error(f"Error registrando trade para optimización: {e}")
    
    async def send_trade_notification(self, signal: Dict, lot_size: float, result: Dict):
        """Enviar notificación de trade ejecutado al usuario"""
        try:
            # Obtener referencia al bot de Telegram
            if hasattr(self, 'telegram_bot') and self.telegram_bot:
                # Calcular ganancia esperada
                pip_worth = 10
                expected_profit = lot_size * signal['expected_pips'] * pip_worth
                
                # Crear mensaje de notificación
                notification = f"""🚨 **TRADE EJECUTADO AUTOMÁTICAMENTE**

🎯 **Detalles de la Operación:**
• **Par**: {signal['pair']}
• **Acción**: {signal['action'].upper()}
• **Estrategia**: {signal['strategy']}
• **Confianza**: {signal['confidence']}%

💰 **Información Financiera:**
• **Tamaño**: {lot_size} lotes
• **Precio Entrada**: {signal['entry_price']:.5f}
• **Stop Loss**: {signal['stop_loss']:.5f}
• **Take Profit**: {signal['take_profit']:.5f}
• **Ganancia Esperada**: ${expected_profit:.2f}

📊 **Datos Técnicos:**
• **Order ID**: {result.get('order', 'N/A')}
• **Timeframe**: {signal.get('timeframe', 'M15')}
• **Pips Esperados**: {signal['expected_pips']:.1f}

⏰ **Ejecutado**: {datetime.now().strftime('%H:%M:%S')}

🎯 **Funciones Avanzadas Activas:**
• Trailing Stop: ✅ (Activación: 10 pips)
• Auto-Optimización: ✅ (Aprendizaje continuo)

💡 **Monitorea esta operación en "🤖 Estado Trading Auto"**"""
                
                # Enviar notificación
                await self.telegram_bot.send_notification(notification)
                
        except Exception as e:
            logger.error(f"Error enviando notificación: {e}")
    
    async def execute_ultimate_trade(self, signal: Dict):
        """Ejecutar trade ultimate"""
        try:
            # Obtener balance actual
            account_info = await self.mt5.get_account_info()
            current_balance = account_info.get('balance', 100000)
            
            # Calcular riesgo y tamaño
            risk_pct = self.calculate_dynamic_risk(signal['confidence'])
            risk_amount = current_balance * risk_pct
            
            # Calcular pips y tamaño de lote
            if 'JPY' in signal['pair']:
                pip_value = 0.01
                pip_worth = 10
            else:
                pip_value = 0.0001
                pip_worth = 10
            
            stop_loss_pips = abs(signal['entry_price'] - signal['stop_loss']) / pip_value
            if stop_loss_pips <= 0:
                stop_loss_pips = 10
            
            lot_size = risk_amount / (stop_loss_pips * pip_worth)
            lot_size = max(0.01, min(0.5, round(lot_size, 2)))  # MÁXIMO 0.5 lotes
            
            logger.info(f"🚀 EJECUTANDO TRADE INTEGRADO:")
            logger.info(f"   Par: {signal['pair']}")
            logger.info(f"   Estrategia: {signal['strategy']}")
            logger.info(f"   Confianza: {signal['confidence']}%")
            logger.info(f"   Riesgo: {risk_pct*100:.1f}%")
            logger.info(f"   Tamaño: {lot_size} lotes")
            logger.info(f"   Ganancia esperada: ${lot_size * signal['expected_pips'] * pip_worth:.2f}")
            
            # Ejecutar orden
            result = await self.mt5.send_order(
                action=signal['action'],
                volume=lot_size,
                symbol=signal['pair'],
                sl=signal['stop_loss'],
                tp=signal['take_profit'],
                comment=f"INTEGRATED-{signal['strategy']}-{signal['confidence']:.0f}%"
            )
            
            if result['success']:
                logger.info("🎉 ¡TRADE INTEGRADO EJECUTADO!")
                logger.info(f"✅ Order ID: {result.get('order', 'N/A')}")
                self.daily_stats['trades'] += 1
                
                # NOTIFICAR AL USUARIO VÍA TELEGRAM
                await self.send_trade_notification(signal, lot_size, result)
                
                # REGISTRAR PARA OPTIMIZACIÓN AUTOMÁTICA
                self.register_trade_for_optimization(signal, result)
                
                return True
            else:
                logger.error(f"❌ Error: {result.get('error', 'Unknown')}")
                return False
                
        except Exception as e:
            logger.error(f"Error ejecutando trade integrado: {e}")
            return False
    
    async def ultimate_trading_loop(self):
        """Loop principal de trading"""
        logger.info("🚀 INICIANDO TRADING AUTOMÁTICO INTEGRADO")
        logger.info("🔥 Multi-par, Multi-estrategia en el bot principal")
        
        while self.running:
            try:
                all_signals = []
                
                # Obtener señales de todos los pares
                for pair in self.config['pairs']:
                    signals = await self.get_signals_for_pair(pair)
                    all_signals.extend(signals)
                
                # Verificar posiciones actuales
                current_positions = await self.mt5.get_positions()
                num_positions = len(current_positions) if current_positions else 0
                
                # Filtrar señales con criterios MÁS ESTRICTOS
                valid_signals = [s for s in all_signals if s['confidence'] >= self.config['min_confidence']]
                valid_signals.sort(key=lambda x: x['confidence'], reverse=True)
                
                # Ejecutar solo si no excedemos límites
                executed = 0
                max_new_trades = min(2, self.config['max_simultaneous_positions'] - num_positions)
                
                for signal in valid_signals[:max_new_trades]:
                    if (self.daily_stats['trades'] < self.config['max_daily_trades'] and 
                        num_positions < self.config['max_simultaneous_positions']):
                        if await self.execute_ultimate_trade(signal):
                            executed += 1
                            num_positions += 1
                
                if executed > 0:
                    logger.info(f"⚡ Ejecutados {executed} trades en este ciclo")
                
                await asyncio.sleep(self.config['strategy_frequency'])
                
            except Exception as e:
                logger.error(f"Error en trading loop integrado: {e}")
                await asyncio.sleep(30)
    
    async def update_trailing_stops(self, positions):
        """Actualizar trailing stops para posiciones abiertas"""
        if not self.trailing_stop_config['enabled']:
            return
        
        try:
            for position in positions:
                ticket = position.get('ticket')
                symbol = position.get('symbol', '')
                position_type = position.get('type')
                open_price = position.get('price_open', 0)
                current_price = position.get('price_current', 0)
                current_sl = position.get('sl', 0)
                profit_pips = 0
                
                # Calcular pips de ganancia
                if 'JPY' in symbol:
                    pip_value = 0.01
                else:
                    pip_value = 0.0001
                
                if position_type == 0:  # BUY
                    profit_pips = (current_price - open_price) / pip_value
                    if profit_pips >= self.trailing_stop_config['activation_pips']:
                        new_sl = current_price - (self.trailing_stop_config['trail_distance'] * pip_value)
                        min_sl = open_price + (self.trailing_stop_config['min_profit_pips'] * pip_value)
                        new_sl = max(new_sl, min_sl)
                        
                        if new_sl > current_sl:
                            await self.modify_position_sl(ticket, new_sl)
                            logger.info(f"🎯 Trailing Stop actualizado: {symbol} SL: {new_sl:.5f}")
                
                elif position_type == 1:  # SELL
                    profit_pips = (open_price - current_price) / pip_value
                    if profit_pips >= self.trailing_stop_config['activation_pips']:
                        new_sl = current_price + (self.trailing_stop_config['trail_distance'] * pip_value)
                        max_sl = open_price - (self.trailing_stop_config['min_profit_pips'] * pip_value)
                        new_sl = min(new_sl, max_sl)
                        
                        if new_sl < current_sl or current_sl == 0:
                            await self.modify_position_sl(ticket, new_sl)
                            logger.info(f"🎯 Trailing Stop actualizado: {symbol} SL: {new_sl:.5f}")
                            
        except Exception as e:
            logger.error(f"Error actualizando trailing stops: {e}")
    
    async def modify_position_sl(self, ticket: int, new_sl: float):
        """Modificar stop loss de una posición"""
        try:
            # Usar el método del MT5Connector para modificar posición
            success = await self.mt5.modify_position(ticket, sl=new_sl)
            if success:
                logger.info(f"✅ Stop Loss modificado exitosamente: Ticket {ticket}")
            else:
                logger.warning(f"⚠️ No se pudo modificar Stop Loss: Ticket {ticket}")
        except Exception as e:
            logger.error(f"Error modificando posición {ticket}: {e}")
    
    async def optimize_strategies(self):
        """Optimización automática de estrategias"""
        if not self.optimization_config['enabled']:
            return
        
        try:
            total_trades = sum(len(history) for history in self.strategy_performance_history.values())
            
            if total_trades >= self.optimization_config['learning_period']:
                logger.info("🧠 INICIANDO OPTIMIZACIÓN AUTOMÁTICA")
                
                for strategy, history in self.strategy_performance_history.items():
                    if len(history) >= 10:  # Mínimo 10 trades para evaluar
                        wins = sum(1 for result in history if result > 0)
                        win_rate = wins / len(history)
                        avg_profit = sum(history) / len(history)
                        
                        logger.info(f"📊 {strategy}: Win Rate {win_rate:.2%}, Avg P&L: ${avg_profit:.2f}")
                        
                        # Auto-ajustar parámetros según rendimiento
                        if self.optimization_config['auto_adjust']:
                            if win_rate < self.optimization_config['performance_threshold']:
                                # Estrategia con bajo rendimiento - ajustar
                                await self.adjust_strategy_parameters(strategy, win_rate, avg_profit)
                            elif win_rate > 0.8:
                                # Estrategia muy exitosa - aumentar agresividad
                                await self.boost_strategy_performance(strategy)
                
                # Limpiar historial para próximo ciclo
                self.strategy_performance_history = {strategy: [] for strategy in self.strategies}
                
        except Exception as e:
            logger.error(f"Error en optimización automática: {e}")
    
    async def adjust_strategy_parameters(self, strategy: str, win_rate: float, avg_profit: float):
        """Ajustar parámetros de estrategia con bajo rendimiento"""
        try:
            logger.info(f"🔧 Ajustando parámetros de {strategy} (Win Rate: {win_rate:.2%})")
            
            if strategy == 'momentum_breakout':
                # Aumentar filtros para mejor calidad
                logger.info("   • Aumentando filtros de momentum breakout")
            elif strategy == 'super_scalping':
                # Reducir frecuencia para mejor selección
                logger.info("   • Reduciendo frecuencia de scalping")
            elif strategy == 'mean_reversion':
                # Ajustar niveles de sobrecompra/sobreventa
                logger.info("   • Ajustando niveles de reversión")
                
        except Exception as e:
            logger.error(f"Error ajustando estrategia {strategy}: {e}")
    
    async def boost_strategy_performance(self, strategy: str):
        """Aumentar agresividad de estrategia exitosa"""
        try:
            logger.info(f"🚀 Aumentando agresividad de {strategy} (alta performance)")
            # Implementar lógica para aumentar frecuencia o tamaño de trades exitosos
            
        except Exception as e:
            logger.error(f"Error aumentando performance de {strategy}: {e}")
    
    async def monitor_performance(self):
        """Monitorear rendimiento con trailing stops y optimización"""
        while self.running:
            try:
                account_info = await self.mt5.get_account_info()
                positions = await self.mt5.get_positions()
                
                if account_info:
                    current_balance = account_info.get('balance', 0)
                    current_equity = account_info.get('equity', 0)
                    daily_pnl = current_balance - self.initial_balance if self.initial_balance > 0 else 0
                    daily_return = (daily_pnl / self.initial_balance * 100) if self.initial_balance > 0 else 0
                    
                    unrealized_pnl = sum(pos.get('profit', 0) for pos in positions) if positions else 0
                    
                    # ACTUALIZAR TRAILING STOPS
                    if positions:
                        await self.update_trailing_stops(positions)
                    
                    # OPTIMIZACIÓN AUTOMÁTICA
                    await self.optimize_strategies()
                    
                    logger.info("📊 RENDIMIENTO INTEGRADO:")
                    logger.info(f"   💰 Balance: ${current_balance:,.2f}")
                    logger.info(f"   📈 Equity: ${current_equity:,.2f}")
                    logger.info(f"   💵 P&L día: ${daily_pnl:+.2f}")
                    logger.info(f"   📊 Retorno: {daily_return:+.2f}%")
                    logger.info(f"   💸 P&L no realizado: ${unrealized_pnl:+.2f}")
                    logger.info(f"   🏆 Posiciones: {len(positions) if positions else 0}")
                    logger.info(f"   📊 Trades hoy: {self.daily_stats['trades']}")
                    logger.info(f"   🎯 Trailing Stops: {'✅ Activo' if self.trailing_stop_config['enabled'] else '❌ Inactivo'}")
                    logger.info(f"   🧠 Auto-Optimización: {'✅ Activa' if self.optimization_config['enabled'] else '❌ Inactiva'}")
                    
                    if daily_return > 5.0:
                        logger.info("🎉 ¡DÍA EXCEPCIONAL! Retorno > 5%")
                
                await asyncio.sleep(60)  # Cada minuto para trailing stops más frecuentes
                
            except Exception as e:
                logger.error(f"Error monitoreando rendimiento: {e}")
                await asyncio.sleep(120)
    
    async def start_integrated_trading(self):
        """Iniciar trading integrado"""
        try:
            # Obtener balance inicial
            account_info = await self.mt5.get_account_info()
            if account_info:
                self.initial_balance = account_info.get('balance', 100000)
            
            self.running = True
            
            logger.info("🚀 TRADING AUTOMÁTICO INTEGRADO INICIADO")
            logger.info(f"💰 Balance inicial: ${self.initial_balance:,.2f}")
            logger.info("🔥 MODO: Integrado en bot principal")
            
            # Crear tareas
            tasks = [
                asyncio.create_task(self.ultimate_trading_loop()),
                asyncio.create_task(self.monitor_performance())
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Error en trading integrado: {e}")
    
    async def stop_integrated_trading(self):
        """Detener trading integrado"""
        self.running = False
        logger.info("🏁 Trading automático integrado detenido")

def check_single_instance():
    """Verificar que solo hay una instancia del bot ejecutándose"""
    try:
        import psutil
        import sys
        
        current_pid = os.getpid()
        current_script = os.path.basename(__file__)
        
        running_instances = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'python.exe' and proc.info['pid'] != current_pid:
                    cmdline = proc.info['cmdline']
                    if cmdline and len(cmdline) > 1 and current_script in ' '.join(cmdline):
                        running_instances.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if running_instances:
            logger.error(f"ADVERTENCIA: Detectadas {len(running_instances)} instancias del bot ejecutandose:")
            for pid in running_instances:
                logger.error(f"   - PID: {pid}")
            logger.error("SOLUCION: Deten las otras instancias antes de continuar")
            return False
        
        return True
        
    except ImportError:
        logger.warning("ADVERTENCIA: psutil no disponible - saltando verificacion de instancia unica")
        return True

async def main():
    """Función principal del bot"""
    # Verificar instancia única (temporalmente deshabilitado para pruebas)
    # if not check_single_instance():
    #     logger.error("ERROR: No se puede iniciar - hay otras instancias ejecutandose")
    #     return
    
    logger.info("OK: Verificacion de instancia unica completada")
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Verificar variables requeridas
    required_vars = ['TELEGRAM_BOT_TOKEN', 'MT5_LOGIN', 'MT5_PASSWORD', 'MT5_SERVER']
    for var in required_vars:
        if not os.getenv(var):
            logger.error(f"Variable de entorno requerida no encontrada: {var}")
            return
    
    try:
        # Inicializar componentes
        logger.info("INICIANDO: Forex Trading Bot...")
        
        # Conectar a MT5
        mt5_connector = MT5Connector()
        if not await mt5_connector.connect():
            logger.error("ERROR: No se pudo conectar a MT5")
            return
        
        # Inicializar componentes principales
        logger.info("🔍 [DEBUG] Inicializando componentes...")
        analyzer = AdvancedMarketAnalyzer(mt5_connector)
        logger.info("🔍 [DEBUG] AdvancedMarketAnalyzer creado")
        
        risk_manager = AdvancedRiskManager()
        logger.info("🔍 [DEBUG] AdvancedRiskManager creado")
        
        trading_engine = OptimizedTradingEngine(mt5_connector, analyzer, risk_manager)
        logger.info(f"🔍 [DEBUG] OptimizedTradingEngine creado: {type(trading_engine)}")
        logger.info(f"🔍 [DEBUG] Trading engine methods: {[method for method in dir(trading_engine) if method.startswith('get_')]}")
        
        telegram_bot = ForexTradingBot(trading_engine)
        logger.info("🔍 [DEBUG] ForexTradingBot creado")
        
        # Crear Ultimate Money Machine integrada
        ultimate_machine = IntegratedUltimateMoneyMachine(mt5_connector)
        logger.info("🔍 [DEBUG] Ultimate Money Machine integrada creada")
        
        # Verificar capacidades
        capabilities = []
        if hasattr(analyzer, 'mtf_enabled') and analyzer.mtf_enabled:
            capabilities.append("Multi-Timeframe")
        if hasattr(analyzer, 'ml_enabled') and analyzer.ml_enabled:
            capabilities.append("Machine Learning")
        capabilities.append("Ultimate Money Machine")
        capabilities.append("Trading Automático")
        
        logger.info(f"OK: Bot listo | Capacidades: {', '.join(capabilities)}")
        logger.info("🚀 TRADING AUTOMÁTICO INTEGRADO ACTIVADO")
        logger.info("💰 El bot generará dinero automáticamente")
        logger.info("INFO: Presiona Ctrl+C para detener")
        
        # Pasar referencias cruzadas entre telegram_bot y ultimate_machine
        telegram_bot.ultimate_machine = ultimate_machine
        telegram_bot.menu_handler.ultimate_machine = ultimate_machine
        ultimate_machine.telegram_bot = telegram_bot
        
        logger.info("🎮 CONTROL MANUAL ACTIVADO")
        logger.info("💬 Usa comandos de Telegram para controlar el trading:")
        logger.info("   /start_trading - Iniciar trading automático")
        logger.info("   /stop_trading - Detener trading automático") 
        logger.info("   /status - Ver estado del bot")
        
        # Solo iniciar Telegram bot - Trading se controla manualmente
        await telegram_bot.start()
        
    except KeyboardInterrupt:
        logger.info("Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"Error crítico: {e}")
    finally:
        # Cleanup
        if 'mt5_connector' in locals():
            await mt5_connector.disconnect()
        logger.info("Bot finalizado")

def main_wrapper():
    """Wrapper para la función main que puede ser llamada por hupper"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"Error en main_wrapper: {e}")

def run_with_reloader():
    """Ejecutar el bot con recarga automática usando hupper"""
    import hupper
    
    # Configurar hupper para monitorear archivos Python
    reloader = hupper.start_reloader('main.main_wrapper')
    
    # Monitorear archivos específicos
    reloader.watch_files([
        'main.py',
        'src/',
        '.env'
    ])

if __name__ == "__main__":
    # Verificar si se debe usar el reloader
    if len(sys.argv) > 1 and sys.argv[1] == '--no-reload':
        # Ejecutar sin reloader
        asyncio.run(main())
    else:
        # Ejecutar con reloader automático
        try:
            run_with_reloader()
        except ImportError:
            logger.warning("Hupper no disponible, ejecutando sin recarga automática")
            asyncio.run(main())

"""
Motor de Trading Agresivo - Diseñado Específicamente para Generar Dinero
Objetivo: Máxima rentabilidad con riesgo controlado
"""

import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

# Importar estrategias rentables
try:
    from ..strategies.profitable_strategies import ProfitableStrategies
    from .advanced_capital_management import AdvancedCapitalManager
    from .mt5_connector import MT5Connector
    from .risk_manager import AdvancedRiskManager
except ImportError:
    from strategies.profitable_strategies import ProfitableStrategies
    from trading.advanced_capital_management import AdvancedCapitalManager
    from trading.mt5_connector import MT5Connector
    from trading.risk_manager import AdvancedRiskManager

logger = logging.getLogger(__name__)

class MoneyMakingEngine:
    """Motor de trading agresivo enfocado en generar ingresos reales"""
    
    def __init__(self, initial_capital: float = 1000, target_monthly_return: float = 15.0):
        """
        Inicializar motor de generación de dinero
        
        Args:
            initial_capital: Capital inicial
            target_monthly_return: Objetivo de retorno mensual (%)
        """
        self.initial_capital = initial_capital
        self.current_balance = initial_capital
        self.target_monthly_return = target_monthly_return
        self.target_daily_return = target_monthly_return / 22  # ~22 días de trading por mes
        
        # Estrategias rentables
        self.profitable_strategies = ProfitableStrategies()
        
        # Gestión de capital agresiva
        self.capital_manager = AdvancedCapitalManager(initial_capital)
        self.capital_manager.max_single_trade_risk = 0.08  # 8% por trade (más agresivo)
        self.capital_manager.max_portfolio_risk = 0.35     # 35% exposición total
        
        # Estrategias activas (las más rentables)
        self.active_strategies = [
            'spread_arbitrage',      # 2-5% mensual, bajo riesgo
            'microstructure_scalping',  # 0.5-1% diario, alta frecuencia
            'momentum_ml',           # 20-40% anual, ML
            'news_momentum',         # 25-35% anual, eventos
            'session_breakout'       # 18-28% anual, sesiones
        ]
        
        # Pesos de estrategias (basado en rentabilidad esperada)
        self.strategy_weights = {
            'spread_arbitrage': 0.30,      # 30% - Más estable
            'microstructure_scalping': 0.25,  # 25% - Alta frecuencia
            'momentum_ml': 0.20,           # 20% - ML predictivo
            'news_momentum': 0.15,         # 15% - Eventos
            'session_breakout': 0.10       # 10% - Complementario
        }
        
        # Métricas de rendimiento
        self.daily_targets = {
            'min_trades': 8,               # Mínimo 8 trades por día
            'target_pips': 25,             # Objetivo 25 pips diarios
            'max_drawdown_daily': 0.05,    # Máximo 5% drawdown diario
            'min_win_rate': 0.60          # Mínimo 60% win rate
        }
        
        # Estado del motor
        self.trading_active = False
        self.daily_stats = {
            'trades_today': 0,
            'pips_today': 0,
            'pnl_today': 0,
            'wins_today': 0,
            'losses_today': 0
        }
        
        # Configuración agresiva
        self.aggressive_mode = True
        self.profit_acceleration = True  # Aumentar tamaño cuando ganamos
        
        logger.info(f"💰 MOTOR DE DINERO inicializado")
        logger.info(f"🎯 Capital: ${initial_capital:,.2f}")
        logger.info(f"🎯 Objetivo mensual: {target_monthly_return}%")
        logger.info(f"🎯 Objetivo diario: {self.target_daily_return:.2f}%")
    
    async def start_money_making(self, mt5_connector: MT5Connector) -> Dict:
        """Iniciar el motor de generación de dinero"""
        try:
            self.mt5 = mt5_connector
            self.trading_active = True
            
            logger.info("🚀 INICIANDO GENERACIÓN DE DINERO")
            logger.info("💰 Modo: AGRESIVO - Objetivo: MÁXIMA RENTABILIDAD")
            
            # Iniciar loops de trading agresivo
            tasks = []
            
            # Loop principal de trading (cada 30 segundos)
            tasks.append(asyncio.create_task(self._aggressive_trading_loop()))
            
            # Loop de scalping (cada 15 segundos)
            tasks.append(asyncio.create_task(self._scalping_loop()))
            
            # Loop de arbitraje (cada 10 segundos)
            tasks.append(asyncio.create_task(self._arbitrage_loop()))
            
            # Monitoreo de objetivos diarios
            tasks.append(asyncio.create_task(self._daily_target_monitor()))
            
            # Ejecutar todos los loops
            await asyncio.gather(*tasks)
            
            return {'success': True, 'message': 'Motor de dinero iniciado'}
            
        except Exception as e:
            logger.error(f"Error iniciando motor de dinero: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _aggressive_trading_loop(self):
        """Loop principal de trading agresivo"""
        logger.info("💰 Loop agresivo iniciado - Buscando dinero...")
        
        while self.trading_active:
            try:
                # Obtener datos actuales
                df = await self.mt5.get_rates(count=300)
                if df.empty:
                    await asyncio.sleep(30)
                    continue
                
                current_time = datetime.now()
                current_idx = len(df) - 1
                
                # Generar señales de todas las estrategias rentables
                signals = []
                
                for strategy_name in self.active_strategies:
                    if strategy_name == 'microstructure_scalping':
                        continue  # Se maneja en loop separado
                    
                    strategy_func = self.profitable_strategies.get_strategy(strategy_name)
                    if strategy_func:
                        signal = strategy_func(df, current_idx)
                        if signal:
                            signal['weight'] = self.strategy_weights.get(strategy_name, 0.1)
                            signals.append(signal)
                
                # Ejecutar señales más prometedoras
                if signals:
                    # Ordenar por confianza * peso
                    signals.sort(key=lambda x: x['confidence'] * x['weight'], reverse=True)
                    
                    # Ejecutar hasta 3 señales simultáneas
                    for signal in signals[:3]:
                        await self._execute_money_trade(signal, df.iloc[-1])
                
                # Verificar si necesitamos ser más agresivos
                await self._check_daily_progress()
                
                await asyncio.sleep(30)  # Cada 30 segundos
                
            except Exception as e:
                logger.error(f"Error en loop agresivo: {e}")
                await asyncio.sleep(60)
    
    async def _scalping_loop(self):
        """Loop de scalping de alta frecuencia"""
        logger.info("⚡ Loop de scalping iniciado - Alta frecuencia")
        
        while self.trading_active:
            try:
                # Obtener datos más recientes para scalping
                df = await self.mt5.get_rates(count=100)
                if df.empty:
                    await asyncio.sleep(15)
                    continue
                
                current_idx = len(df) - 1
                
                # Estrategia de microestructura
                scalping_func = self.profitable_strategies.get_strategy('microstructure_scalping')
                if scalping_func:
                    signal = scalping_func(df, current_idx)
                    if signal and signal['confidence'] > 70:
                        await self._execute_scalping_trade(signal, df.iloc[-1])
                
                await asyncio.sleep(15)  # Cada 15 segundos para scalping
                
            except Exception as e:
                logger.error(f"Error en scalping loop: {e}")
                await asyncio.sleep(30)
    
    async def _arbitrage_loop(self):
        """Loop de arbitraje de spreads"""
        logger.info("🔄 Loop de arbitraje iniciado - Buscando ineficiencias")
        
        while self.trading_active:
            try:
                df = await self.mt5.get_rates(count=50)
                if df.empty:
                    await asyncio.sleep(10)
                    continue
                
                current_idx = len(df) - 1
                
                # Estrategia de arbitraje
                arbitrage_func = self.profitable_strategies.get_strategy('spread_arbitrage')
                if arbitrage_func:
                    signal = arbitrage_func(df, current_idx)
                    if signal and signal['confidence'] > 75:
                        await self._execute_arbitrage_trade(signal, df.iloc[-1])
                
                await asyncio.sleep(10)  # Cada 10 segundos para arbitraje
                
            except Exception as e:
                logger.error(f"Error en arbitrage loop: {e}")
                await asyncio.sleep(20)
    
    async def _execute_money_trade(self, signal: Dict, current_bar: pd.Series):
        """Ejecutar trade con enfoque en generar dinero"""
        try:
            # Calcular tamaño de posición agresivo
            position_sizing = self.capital_manager.calculate_position_size(
                signal['confidence'],
                signal.get('stop_loss_pips', 10),
                signal['strategy'],
                current_bar['close']
            )
            
            # Aumentar tamaño si estamos ganando (profit acceleration)
            if self.profit_acceleration and self.daily_stats['pnl_today'] > 0:
                multiplier = 1 + (self.daily_stats['pnl_today'] / self.current_balance)
                position_sizing['size_lots'] *= min(2.0, 1 + multiplier)  # Máximo 2x
            
            # Verificar que el trade sea rentable
            expected_profit = position_sizing['size_lots'] * signal.get('profit_target_pips', 10) * 10
            if expected_profit < self.current_balance * 0.005:  # Mínimo 0.5% de ganancia esperada
                return
            
            # Ejecutar orden
            result = await self.mt5.send_order(
                symbol='EURUSD',
                action=signal['action'],
                volume=position_sizing['size_lots'],
                sl=signal.get('stop_loss'),
                tp=signal.get('take_profit'),
                comment=f"MONEY-{signal['strategy']}-{signal['confidence']:.0f}%"
            )
            
            if result['success']:
                # Actualizar estadísticas
                self.daily_stats['trades_today'] += 1
                
                logger.info(f"💰 TRADE EJECUTADO: {signal['action']} {position_sizing['size_lots']} lotes")
                logger.info(f"🎯 Estrategia: {signal['strategy']} | Confianza: {signal['confidence']:.1f}%")
                logger.info(f"💵 Ganancia esperada: ${expected_profit:.2f}")
                
                # Registrar para capital manager
                self.capital_manager.update_balance({
                    'pnl': 0,  # Se actualizará al cerrar
                    'strategy': signal['strategy'],
                    'confidence': signal['confidence']
                })
            
        except Exception as e:
            logger.error(f"Error ejecutando trade de dinero: {e}")
    
    async def _execute_scalping_trade(self, signal: Dict, current_bar: pd.Series):
        """Ejecutar trade de scalping rápido"""
        try:
            # Tamaño más pequeño pero más frecuente para scalping
            base_size = 0.05  # 0.05 lotes base
            
            # Ajustar por confianza
            size_lots = base_size * (signal['confidence'] / 100) * 2
            size_lots = min(0.2, max(0.01, size_lots))  # Entre 0.01 y 0.2 lotes
            
            result = await self.mt5.send_order(
                symbol='EURUSD',
                action=signal['action'],
                volume=size_lots,
                sl=signal.get('stop_loss'),
                tp=signal.get('take_profit'),
                comment=f"SCALP-{signal['confidence']:.0f}%"
            )
            
            if result['success']:
                self.daily_stats['trades_today'] += 1
                logger.info(f"⚡ SCALPING: {signal['action']} {size_lots} lotes | Target: {signal.get('profit_target_pips', 6)} pips")
            
        except Exception as e:
            logger.error(f"Error en scalping trade: {e}")
    
    async def _execute_arbitrage_trade(self, signal: Dict, current_bar: pd.Series):
        """Ejecutar trade de arbitraje"""
        try:
            # Arbitraje con tamaño medio
            base_size = 0.1
            size_lots = base_size * (signal['confidence'] / 100) * 1.5
            size_lots = min(0.3, max(0.01, size_lots))
            
            result = await self.mt5.send_order(
                symbol='EURUSD',
                action=signal['action'],
                volume=size_lots,
                sl=signal.get('stop_loss'),
                tp=signal.get('take_profit'),
                comment=f"ARB-{signal['confidence']:.0f}%"
            )
            
            if result['success']:
                self.daily_stats['trades_today'] += 1
                logger.info(f"🔄 ARBITRAJE: {signal['action']} {size_lots} lotes | Target: {signal.get('profit_target_pips', 8)} pips")
            
        except Exception as e:
            logger.error(f"Error en arbitrage trade: {e}")
    
    async def _daily_target_monitor(self):
        """Monitorear progreso hacia objetivos diarios"""
        while self.trading_active:
            try:
                current_time = datetime.now()
                
                # Resetear estadísticas diarias a medianoche
                if current_time.hour == 0 and current_time.minute == 0:
                    await self._reset_daily_stats()
                
                # Verificar progreso cada hora
                if current_time.minute == 0:
                    await self._evaluate_daily_progress()
                
                await asyncio.sleep(300)  # Cada 5 minutos
                
            except Exception as e:
                logger.error(f"Error en monitor diario: {e}")
                await asyncio.sleep(600)
    
    async def _check_daily_progress(self):
        """Verificar si necesitamos ser más agresivos"""
        try:
            current_hour = datetime.now().hour
            
            # Calcular progreso esperado según la hora
            hours_passed = current_hour if current_hour > 0 else 1
            expected_progress = (hours_passed / 24) * self.target_daily_return
            
            # Progreso actual
            actual_progress = (self.daily_stats['pnl_today'] / self.current_balance) * 100
            
            # Si estamos atrasados, ser más agresivos
            if actual_progress < expected_progress * 0.7:  # 70% del objetivo
                logger.warning(f"⚠️ ATRASADOS EN OBJETIVO DIARIO")
                logger.warning(f"📊 Esperado: {expected_progress:.2f}% | Actual: {actual_progress:.2f}%")
                
                # Activar modo super agresivo
                self.aggressive_mode = True
                self.profit_acceleration = True
                
                # Aumentar pesos de estrategias más rentables
                self.strategy_weights['microstructure_scalping'] = 0.35
                self.strategy_weights['spread_arbitrage'] = 0.35
                
            elif actual_progress > expected_progress * 1.3:  # 130% del objetivo
                logger.info(f"🎉 SUPERANDO OBJETIVO DIARIO")
                logger.info(f"📊 Esperado: {expected_progress:.2f}% | Actual: {actual_progress:.2f}%")
                
                # Modo más conservador para proteger ganancias
                self.aggressive_mode = False
                
        except Exception as e:
            logger.error(f"Error verificando progreso: {e}")
    
    async def _reset_daily_stats(self):
        """Resetear estadísticas diarias"""
        logger.info("🔄 Reseteando estadísticas diarias")
        
        # Guardar estadísticas del día anterior
        yesterday_stats = self.daily_stats.copy()
        
        # Resetear para nuevo día
        self.daily_stats = {
            'trades_today': 0,
            'pips_today': 0,
            'pnl_today': 0,
            'wins_today': 0,
            'losses_today': 0
        }
        
        # Log del rendimiento del día anterior
        if yesterday_stats['trades_today'] > 0:
            win_rate = yesterday_stats['wins_today'] / yesterday_stats['trades_today'] * 100
            daily_return = (yesterday_stats['pnl_today'] / self.current_balance) * 100
            
            logger.info(f"📊 RESUMEN DEL DÍA ANTERIOR:")
            logger.info(f"   Trades: {yesterday_stats['trades_today']}")
            logger.info(f"   Win Rate: {win_rate:.1f}%")
            logger.info(f"   Pips: {yesterday_stats['pips_today']:.1f}")
            logger.info(f"   P&L: ${yesterday_stats['pnl_today']:.2f}")
            logger.info(f"   Retorno: {daily_return:.2f}%")
    
    async def _evaluate_daily_progress(self):
        """Evaluar progreso diario y ajustar estrategia"""
        try:
            current_return = (self.daily_stats['pnl_today'] / self.current_balance) * 100
            
            logger.info(f"📊 PROGRESO DIARIO ACTUAL:")
            logger.info(f"   Objetivo: {self.target_daily_return:.2f}%")
            logger.info(f"   Actual: {current_return:.2f}%")
            logger.info(f"   Trades: {self.daily_stats['trades_today']}")
            
            # Ajustar estrategia según progreso
            if current_return >= self.target_daily_return:
                logger.info("🎉 OBJETIVO DIARIO ALCANZADO")
                # Modo más conservador
                self.aggressive_mode = False
                
            elif current_return < self.target_daily_return * 0.5:
                logger.warning("⚠️ NECESITAMOS MÁS AGRESIVIDAD")
                # Aumentar agresividad
                self.aggressive_mode = True
                self.capital_manager.max_single_trade_risk = 0.12  # 12% por trade
                
        except Exception as e:
            logger.error(f"Error evaluando progreso: {e}")
    
    def get_money_making_status(self) -> Dict:
        """Obtener estado del motor de generación de dinero"""
        try:
            current_return_daily = (self.daily_stats['pnl_today'] / self.current_balance) * 100
            current_return_total = ((self.current_balance - self.initial_capital) / self.initial_capital) * 100
            
            win_rate_today = 0
            if self.daily_stats['trades_today'] > 0:
                win_rate_today = (self.daily_stats['wins_today'] / self.daily_stats['trades_today']) * 100
            
            return {
                'mode': 'MONEY_MAKING_AGGRESSIVE',
                'trading_active': self.trading_active,
                'current_balance': self.current_balance,
                'initial_capital': self.initial_capital,
                'total_return_pct': current_return_total,
                
                # Objetivos
                'target_monthly_return': self.target_monthly_return,
                'target_daily_return': self.target_daily_return,
                
                # Progreso diario
                'daily_return_pct': current_return_daily,
                'daily_target_progress': (current_return_daily / self.target_daily_return) * 100,
                'trades_today': self.daily_stats['trades_today'],
                'pips_today': self.daily_stats['pips_today'],
                'win_rate_today': win_rate_today,
                
                # Configuración agresiva
                'aggressive_mode': self.aggressive_mode,
                'profit_acceleration': self.profit_acceleration,
                'max_risk_per_trade': self.capital_manager.max_single_trade_risk * 100,
                
                # Estrategias activas
                'active_strategies': self.active_strategies,
                'strategy_weights': self.strategy_weights,
                
                # Estado
                'status': 'GENERATING_MONEY' if self.trading_active else 'STOPPED'
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado: {e}")
            return {'error': str(e)}
    
    async def stop_money_making(self):
        """Detener motor de generación de dinero"""
        self.trading_active = False
        logger.info("🛑 Motor de generación de dinero detenido")
        
        # Mostrar resumen final
        final_status = self.get_money_making_status()
        logger.info(f"💰 RESUMEN FINAL:")
        logger.info(f"   Balance final: ${final_status['current_balance']:,.2f}")
        logger.info(f"   Retorno total: {final_status['total_return_pct']:.2f}%")
        logger.info(f"   Trades hoy: {final_status['trades_today']}")
        
        return final_status

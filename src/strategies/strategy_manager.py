"""
Sistema de Gestión Multi-Estrategia
Coordina múltiples estrategias de trading para maximizar oportunidades y diversificar riesgos
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import pandas as pd

logger = logging.getLogger(__name__)

class StrategyType(Enum):
    SCALPING = "scalping"
    SWING = "swing"
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"

class MarketCondition(Enum):
    TRENDING = "trending"
    RANGING = "ranging"
    VOLATILE = "volatile"
    QUIET = "quiet"
    NEWS_EVENT = "news_event"

class StrategyManager:
    def __init__(self, mt5_connector, analyzer, risk_manager):
        self.mt5 = mt5_connector
        self.analyzer = analyzer
        self.risk_manager = risk_manager
        
        # Estrategias disponibles
        self.strategies = {}
        self.active_strategies = set()
        
        # Estado del mercado
        self.current_market_condition = MarketCondition.RANGING
        self.market_condition_history = []
        
        # Configuración de estrategias
        self.strategy_config = {
            StrategyType.SCALPING: {
                'timeframes': ['M1', 'M5'],
                'max_positions': 3,
                'risk_per_trade': 0.5,  # 0.5% por trade
                'active_sessions': ['london', 'new_york', 'overlap'],
                'min_confidence': 70,
                'max_spread': 2.0,  # pips
                'target_pips': 5,
                'stop_pips': 3
            },
            StrategyType.SWING: {
                'timeframes': ['H1', 'H4'],
                'max_positions': 2,
                'risk_per_trade': 2.0,  # 2% por trade
                'active_sessions': ['london', 'new_york'],
                'min_confidence': 80,
                'max_spread': 3.0,
                'target_pips': 50,
                'stop_pips': 25
            },
            StrategyType.TREND_FOLLOWING: {
                'timeframes': ['H4', 'D1'],
                'max_positions': 1,
                'risk_per_trade': 3.0,  # 3% por trade
                'active_sessions': ['any'],
                'min_confidence': 85,
                'max_spread': 4.0,
                'target_pips': 100,
                'stop_pips': 40
            },
            StrategyType.MEAN_REVERSION: {
                'timeframes': ['M15', 'M30'],
                'max_positions': 2,
                'risk_per_trade': 1.5,  # 1.5% por trade
                'active_sessions': ['asian', 'london'],
                'min_confidence': 75,
                'max_spread': 2.5,
                'target_pips': 20,
                'stop_pips': 15
            },
            StrategyType.BREAKOUT: {
                'timeframes': ['M15', 'H1'],
                'max_positions': 2,
                'risk_per_trade': 2.5,  # 2.5% por trade
                'active_sessions': ['london', 'new_york'],
                'min_confidence': 78,
                'max_spread': 3.0,
                'target_pips': 40,
                'stop_pips': 20
            }
        }
        
        # Estadísticas de rendimiento por estrategia
        self.strategy_performance = {
            strategy: {
                'total_trades': 0,
                'winning_trades': 0,
                'total_profit': 0.0,
                'avg_profit': 0.0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'last_updated': datetime.now()
            } for strategy in StrategyType
        }
        
        # Control de exposición
        self.max_total_risk = 8.0  # Máximo 8% de riesgo total
        self.max_correlation_exposure = 5.0  # Máximo 5% en pares correlacionados
        
        # Inicializar estrategias
        self._initialize_strategies()
    
    def _initialize_strategies(self):
        """Inicializar todas las estrategias disponibles"""
        try:
            from .scalping_strategy import ScalpingStrategy
            from .swing_strategy import SwingStrategy
            from .trend_following_strategy import TrendFollowingStrategy
            from .mean_reversion_strategy import MeanReversionStrategy
            from .breakout_strategy import BreakoutStrategy
            
            self.strategies = {
                StrategyType.SCALPING: ScalpingStrategy(self.mt5, self.analyzer, self.risk_manager),
                StrategyType.SWING: SwingStrategy(self.mt5, self.analyzer, self.risk_manager),
                StrategyType.TREND_FOLLOWING: TrendFollowingStrategy(self.mt5, self.analyzer, self.risk_manager),
                StrategyType.MEAN_REVERSION: MeanReversionStrategy(self.mt5, self.analyzer, self.risk_manager),
                StrategyType.BREAKOUT: BreakoutStrategy(self.mt5, self.analyzer, self.risk_manager)
            }
            
            # Activar estrategias por defecto
            self.active_strategies = {
                StrategyType.SCALPING,
                StrategyType.SWING,
                StrategyType.MEAN_REVERSION
            }
            
            logger.info(f"✅ Inicializadas {len(self.strategies)} estrategias")
            logger.info(f"🎯 Estrategias activas: {[s.value for s in self.active_strategies]}")
            
        except ImportError as e:
            logger.warning(f"⚠️ Algunas estrategias no están disponibles: {e}")
            # Usar estrategia básica como fallback
            self.active_strategies = set()
    
    async def analyze_market_condition(self) -> MarketCondition:
        """Analizar condición actual del mercado para seleccionar estrategias óptimas"""
        try:
            # Obtener datos de múltiples timeframes
            df_m15 = await self.mt5.get_rates(symbol="EURUSD", timeframe="M15", count=100)
            df_h1 = await self.mt5.get_rates(symbol="EURUSD", timeframe="H1", count=50)
            
            if df_m15.empty or df_h1.empty:
                return self.current_market_condition
            
            # Calcular indicadores para determinar condición
            df_m15 = self.analyzer.calculate_advanced_indicators(df_m15)
            df_h1 = self.analyzer.calculate_advanced_indicators(df_h1)
            
            latest_m15 = df_m15.iloc[-1]
            latest_h1 = df_h1.iloc[-1]
            
            # Determinar volatilidad
            atr_m15 = latest_m15.get('atr', 0.001)
            atr_avg_m15 = df_m15['atr'].tail(20).mean()
            volatility_ratio = atr_m15 / atr_avg_m15 if atr_avg_m15 > 0 else 1
            
            # Determinar tendencia
            adx_h1 = latest_h1.get('adx', 25)
            ema_alignment = self._check_ema_alignment(df_h1)
            
            # Clasificar condición del mercado
            if volatility_ratio > 2.0:
                condition = MarketCondition.VOLATILE
            elif adx_h1 > 30 and abs(ema_alignment) > 0.7:
                condition = MarketCondition.TRENDING
            elif adx_h1 < 20:
                condition = MarketCondition.RANGING
            elif volatility_ratio < 0.5:
                condition = MarketCondition.QUIET
            else:
                condition = MarketCondition.RANGING  # Default
            
            # Actualizar historial
            self.current_market_condition = condition
            self.market_condition_history.append({
                'timestamp': datetime.now(),
                'condition': condition,
                'volatility_ratio': volatility_ratio,
                'adx': adx_h1,
                'ema_alignment': ema_alignment
            })
            
            # Mantener solo últimas 100 observaciones
            if len(self.market_condition_history) > 100:
                self.market_condition_history = self.market_condition_history[-100:]
            
            logger.info(f"📊 Condición del mercado: {condition.value.upper()}")
            logger.info(f"📈 Volatilidad: {volatility_ratio:.2f}x, ADX: {adx_h1:.1f}")
            
            return condition
            
        except Exception as e:
            logger.error(f"Error analizando condición del mercado: {e}")
            return self.current_market_condition
    
    def detect_market_condition(self, market_data: Dict = None) -> str:
        """Alias para analyze_market_condition (para compatibilidad)"""
        try:
            # Versión simplificada para pruebas
            if market_data is None:
                return self.current_market_condition.value if hasattr(self.current_market_condition, 'value') else 'ranging'
            
            # Análisis básico basado en datos proporcionados
            volatility = market_data.get('volatility', 1.0)
            trend_strength = market_data.get('trend_strength', 0.5)
            
            if volatility > 2.0:
                return 'volatile'
            elif trend_strength > 0.7:
                return 'trending'
            elif trend_strength < 0.3:
                return 'ranging'
            else:
                return 'ranging'
                
        except Exception as e:
            logger.error(f"Error detectando condición del mercado: {e}")
            return 'ranging'
    
    def _check_ema_alignment(self, df: pd.DataFrame) -> float:
        """Verificar alineación de EMAs para determinar fuerza de tendencia"""
        try:
            latest = df.iloc[-1]
            
            emas = ['ema_8', 'ema_13', 'ema_21', 'ema_55']
            ema_values = [latest.get(ema, latest['close']) for ema in emas]
            
            # Verificar si están ordenadas (alcista o bajista)
            is_bullish = all(ema_values[i] >= ema_values[i+1] for i in range(len(ema_values)-1))
            is_bearish = all(ema_values[i] <= ema_values[i+1] for i in range(len(ema_values)-1))
            
            if is_bullish:
                return 1.0  # Tendencia alcista fuerte
            elif is_bearish:
                return -1.0  # Tendencia bajista fuerte
            else:
                # Calcular parcial alignment
                alignment_score = 0
                for i in range(len(ema_values)-1):
                    if ema_values[i] > ema_values[i+1]:
                        alignment_score += 1
                    elif ema_values[i] < ema_values[i+1]:
                        alignment_score -= 1
                
                return alignment_score / (len(ema_values) - 1)
                
        except Exception as e:
            logger.error(f"Error calculando alineación EMA: {e}")
            return 0.0
    
    def select_optimal_strategies(self, market_condition: MarketCondition) -> List[StrategyType]:
        """Seleccionar estrategias óptimas basadas en condición del mercado"""
        try:
            optimal_strategies = []
            
            # Mapeo de condiciones a estrategias óptimas
            strategy_mapping = {
                MarketCondition.TRENDING: [
                    StrategyType.TREND_FOLLOWING,
                    StrategyType.BREAKOUT,
                    StrategyType.SWING
                ],
                MarketCondition.RANGING: [
                    StrategyType.MEAN_REVERSION,
                    StrategyType.SCALPING,
                    StrategyType.SWING
                ],
                MarketCondition.VOLATILE: [
                    StrategyType.BREAKOUT,
                    StrategyType.SCALPING  # Solo si spread es bajo
                ],
                MarketCondition.QUIET: [
                    StrategyType.MEAN_REVERSION,
                    StrategyType.SCALPING
                ],
                MarketCondition.NEWS_EVENT: [
                    # Pausar todas las estrategias durante noticias
                ]
            }
            
            candidate_strategies = strategy_mapping.get(market_condition, [])
            
            # Filtrar por rendimiento histórico
            for strategy in candidate_strategies:
                if strategy in self.active_strategies:
                    performance = self.strategy_performance[strategy]
                    
                    # Solo incluir estrategias con buen rendimiento
                    if (performance['total_trades'] < 10 or  # Nuevas estrategias
                        performance['win_rate'] >= 0.55 or   # Win rate decente
                        performance['profit_factor'] >= 1.2): # Profit factor positivo
                        optimal_strategies.append(strategy)
            
            # Asegurar diversificación mínima
            if len(optimal_strategies) == 0 and market_condition != MarketCondition.NEWS_EVENT:
                # Fallback a estrategias más conservadoras
                optimal_strategies = [StrategyType.MEAN_REVERSION]
            
            logger.info(f"🎯 Estrategias seleccionadas para {market_condition.value}: {[s.value for s in optimal_strategies]}")
            
            return optimal_strategies
            
        except Exception as e:
            logger.error(f"Error seleccionando estrategias óptimas: {e}")
            return [StrategyType.MEAN_REVERSION]  # Fallback seguro
    
    async def execute_multi_strategy_analysis(self) -> List[Dict]:
        """Ejecutar análisis con múltiples estrategias y retornar mejores oportunidades"""
        try:
            # Analizar condición del mercado
            market_condition = await self.analyze_market_condition()
            
            # Seleccionar estrategias óptimas
            optimal_strategies = self.select_optimal_strategies(market_condition)
            
            if not optimal_strategies:
                logger.info("🚫 No hay estrategias activas para la condición actual del mercado")
                return []
            
            # Verificar exposición total
            current_risk = await self._calculate_current_risk_exposure()
            if current_risk >= self.max_total_risk:
                logger.warning(f"⚠️ Exposición máxima alcanzada: {current_risk:.1f}%")
                return []
            
            # Ejecutar análisis con cada estrategia
            all_opportunities = []
            
            for strategy_type in optimal_strategies:
                try:
                    if strategy_type not in self.strategies:
                        continue
                    
                    strategy = self.strategies[strategy_type]
                    config = self.strategy_config[strategy_type]
                    
                    # Verificar si la estrategia puede operar ahora
                    if not await self._can_strategy_trade(strategy_type, config):
                        continue
                    
                    # Obtener oportunidades de la estrategia
                    opportunities = await strategy.find_opportunities(config)
                    
                    # Agregar metadata de estrategia
                    for opp in opportunities:
                        opp['strategy_type'] = strategy_type.value
                        opp['market_condition'] = market_condition.value
                        opp['priority'] = self._calculate_opportunity_priority(opp, strategy_type)
                    
                    all_opportunities.extend(opportunities)
                    
                except Exception as strategy_error:
                    logger.error(f"Error en estrategia {strategy_type.value}: {strategy_error}")
                    continue
            
            # Ordenar por prioridad y filtrar conflictos
            filtered_opportunities = self._filter_and_prioritize_opportunities(all_opportunities)
            
            logger.info(f"🎯 Encontradas {len(filtered_opportunities)} oportunidades de {len(all_opportunities)} analizadas")
            
            return filtered_opportunities
            
        except Exception as e:
            logger.error(f"Error en análisis multi-estrategia: {e}")
            return []
    
    async def _can_strategy_trade(self, strategy_type: StrategyType, config: Dict) -> bool:
        """Verificar si una estrategia puede operar en este momento"""
        try:
            # Verificar sesión activa
            current_session = self._get_current_session()
            active_sessions = config['active_sessions']
            
            if 'any' not in active_sessions and current_session not in active_sessions:
                return False
            
            # Verificar spread
            current_spread = await self._get_current_spread()
            if current_spread > config['max_spread']:
                return False
            
            # Verificar posiciones existentes
            current_positions = await self._count_strategy_positions(strategy_type)
            if current_positions >= config['max_positions']:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verificando si estrategia puede operar: {e}")
            return False
    
    def _calculate_opportunity_priority(self, opportunity: Dict, strategy_type: StrategyType) -> float:
        """Calcular prioridad de una oportunidad"""
        try:
            base_priority = opportunity.get('confidence', 50) / 100
            
            # Bonus por rendimiento histórico de la estrategia
            performance = self.strategy_performance[strategy_type]
            performance_bonus = min(0.3, performance['win_rate'] * 0.5)
            
            # Bonus por condición del mercado
            market_bonus = 0.1 if self.current_market_condition in [
                MarketCondition.TRENDING, MarketCondition.RANGING
            ] else 0.0
            
            # Penalty por volatilidad extrema
            volatility_penalty = 0.2 if self.current_market_condition == MarketCondition.VOLATILE else 0.0
            
            priority = base_priority + performance_bonus + market_bonus - volatility_penalty
            
            return max(0.0, min(1.0, priority))
            
        except Exception as e:
            logger.error(f"Error calculando prioridad: {e}")
            return 0.5
    
    def _filter_and_prioritize_opportunities(self, opportunities: List[Dict]) -> List[Dict]:
        """Filtrar conflictos y priorizar oportunidades"""
        try:
            if not opportunities:
                return []
            
            # Ordenar por prioridad
            sorted_opportunities = sorted(opportunities, key=lambda x: x['priority'], reverse=True)
            
            # Filtrar conflictos (misma dirección en mismo símbolo)
            filtered = []
            used_symbols = set()
            
            for opp in sorted_opportunities:
                symbol = opp.get('symbol', 'EURUSD')
                signal = opp.get('signal', 'HOLD')
                
                # Crear clave única para evitar conflictos
                conflict_key = f"{symbol}_{signal}"
                
                if conflict_key not in used_symbols:
                    filtered.append(opp)
                    used_symbols.add(conflict_key)
                    
                    # Limitar número total de oportunidades simultáneas
                    if len(filtered) >= 3:
                        break
            
            return filtered
            
        except Exception as e:
            logger.error(f"Error filtrando oportunidades: {e}")
            return opportunities[:3]  # Fallback: primeras 3
    
    async def _calculate_current_risk_exposure(self) -> float:
        """Calcular exposición de riesgo actual"""
        try:
            positions = await self.mt5.get_positions()
            if not positions:
                return 0.0
            
            account_info = await self.mt5.get_account_info()
            balance = account_info.get('balance', 10000)
            
            total_risk = 0.0
            for position in positions:
                # Calcular riesgo de cada posición
                volume = position.get('volume', 0.01)
                entry_price = position.get('price_open', 1.0)
                sl = position.get('sl', 0)
                
                if sl > 0:
                    risk_pips = abs(entry_price - sl) * 10000
                    risk_amount = risk_pips * volume * 10  # $10 per pip per lot
                    risk_percentage = (risk_amount / balance) * 100
                    total_risk += risk_percentage
            
            return total_risk
            
        except Exception as e:
            logger.error(f"Error calculando exposición de riesgo: {e}")
            return 0.0
    
    async def _count_strategy_positions(self, strategy_type: StrategyType) -> int:
        """Contar posiciones activas de una estrategia específica"""
        try:
            positions = await self.mt5.get_positions()
            if not positions:
                return 0
            
            count = 0
            strategy_prefix = f"Multi-{strategy_type.value}"
            
            for position in positions:
                comment = position.get('comment', '')
                if strategy_prefix in comment:
                    count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Error contando posiciones de estrategia: {e}")
            return 0
    
    async def _get_current_spread(self) -> float:
        """Obtener spread actual en pips"""
        try:
            symbol_info = await self.mt5.get_symbol_info("EURUSD")
            if symbol_info:
                spread = symbol_info.get('spread', 20) / 10  # Convertir a pips
                return spread
            return 2.0  # Default
            
        except Exception as e:
            logger.error(f"Error obteniendo spread: {e}")
            return 2.0
    
    def _get_current_session(self) -> str:
        """Determinar sesión de mercado actual"""
        hour = datetime.utcnow().hour
        
        if 13 <= hour <= 17:
            return 'overlap'
        elif 8 <= hour <= 17:
            return 'london'
        elif 13 <= hour <= 22:
            return 'new_york'
        else:
            return 'asian'
    
    def update_strategy_performance(self, strategy_type: StrategyType, trade_result: Dict):
        """Actualizar estadísticas de rendimiento de una estrategia"""
        try:
            stats = self.strategy_performance[strategy_type]
            
            stats['total_trades'] += 1
            profit = trade_result.get('profit', 0)
            stats['total_profit'] += profit
            
            if profit > 0:
                stats['winning_trades'] += 1
            
            # Recalcular métricas
            stats['win_rate'] = stats['winning_trades'] / stats['total_trades']
            stats['avg_profit'] = stats['total_profit'] / stats['total_trades']
            
            # Calcular profit factor (ganancias/pérdidas)
            if stats['total_trades'] >= 10:
                recent_trades = 10  # Usar últimos 10 trades para profit factor
                # Simplificado: asumir distribución equilibrada
                avg_win = stats['avg_profit'] * (stats['win_rate'] / (1 - stats['win_rate'])) if stats['win_rate'] < 1 else stats['avg_profit']
                avg_loss = abs(stats['avg_profit'] - avg_win)
                stats['profit_factor'] = avg_win / avg_loss if avg_loss > 0 else 2.0
            
            stats['last_updated'] = datetime.now()
            
            logger.info(f"📊 Rendimiento {strategy_type.value}: WR={stats['win_rate']:.1%}, PF={stats['profit_factor']:.2f}")
            
        except Exception as e:
            logger.error(f"Error actualizando rendimiento de estrategia: {e}")
    
    def get_strategy_statistics(self) -> Dict:
        """Obtener estadísticas completas de todas las estrategias"""
        try:
            stats = {
                'market_condition': self.current_market_condition.value,
                'active_strategies': [s.value for s in self.active_strategies],
                'strategy_performance': {}
            }
            
            for strategy_type, performance in self.strategy_performance.items():
                if performance['total_trades'] > 0:
                    stats['strategy_performance'][strategy_type.value] = {
                        'total_trades': performance['total_trades'],
                        'win_rate': f"{performance['win_rate']:.1%}",
                        'avg_profit': f"${performance['avg_profit']:.2f}",
                        'profit_factor': f"{performance['profit_factor']:.2f}",
                        'total_profit': f"${performance['total_profit']:.2f}"
                    }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def activate_strategy(self, strategy_type: StrategyType):
        """Activar una estrategia específica"""
        self.active_strategies.add(strategy_type)
        logger.info(f"✅ Estrategia {strategy_type.value} activada")
    
    def deactivate_strategy(self, strategy_type: StrategyType):
        """Desactivar una estrategia específica"""
        self.active_strategies.discard(strategy_type)
        logger.info(f"❌ Estrategia {strategy_type.value} desactivada")
    
    async def emergency_stop_all_strategies(self):
        """Parar todas las estrategias en caso de emergencia"""
        try:
            logger.warning("🚨 PARADA DE EMERGENCIA - Desactivando todas las estrategias")
            self.active_strategies.clear()
            
            # Cerrar todas las posiciones si es necesario
            positions = await self.mt5.get_positions()
            if positions:
                logger.warning(f"⚠️ Cerrando {len(positions)} posiciones abiertas")
                for position in positions:
                    await self.mt5.close_position(position.get('ticket'))
            
        except Exception as e:
            logger.error(f"Error en parada de emergencia: {e}")

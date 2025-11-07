"""
Gestor Multi-Pair
Coordina trading simultáneo en múltiples pares de divisas con gestión de correlaciones
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd

logger = logging.getLogger(__name__)

class MultiPairManager:
    def __init__(self, mt5_connector, analyzer, risk_manager, correlation_analyzer):
        self.mt5 = mt5_connector
        self.analyzer = analyzer
        self.risk_manager = risk_manager
        self.correlation_analyzer = correlation_analyzer
        
        # Configuración multi-pair
        self.max_pairs_active = 4  # Máximo 4 pares simultáneos
        self.max_positions_per_pair = 2  # Máximo 2 posiciones por par
        self.max_total_positions = 6  # Máximo 6 posiciones totales
        
        # Pares activos actuales
        self.active_pairs = []
        self.pair_performance = {}
        self.pair_last_analysis = {}
        
        # Control de exposición
        self.max_correlation_risk = 0.6  # 60% máximo riesgo correlación
        self.max_currency_exposure = 0.4  # 40% máximo exposición por divisa
        
        # Intervalos de análisis por par
        self.analysis_intervals = {
            'EURUSD': 120,  # 2 minutos
            'GBPUSD': 150,  # 2.5 minutos
            'USDJPY': 180,  # 3 minutos
            'USDCHF': 200,  # 3.3 minutos
            'AUDUSD': 240,  # 4 minutos
            'NZDUSD': 300,  # 5 minutos
            'EURGBP': 180,  # 3 minutos
            'EURJPY': 160   # 2.7 minutos
        }
        
    async def initialize_multi_pair_trading(self) -> Dict:
        """Inicializar trading multi-pair"""
        try:
            # Obtener sesión actual
            current_session = self._get_current_session()
            
            # Seleccionar pares óptimos para la sesión
            optimal_pairs = await self.correlation_analyzer.get_optimal_pairs_for_session(
                current_session, max_pairs=self.max_pairs_active
            )
            
            # Actualizar correlaciones dinámicas
            await self.correlation_analyzer.update_dynamic_correlations(optimal_pairs)
            
            # Activar pares seleccionados
            self.active_pairs = optimal_pairs
            
            # Inicializar tracking de rendimiento
            for pair in self.active_pairs:
                if pair not in self.pair_performance:
                    self.pair_performance[pair] = {
                        'total_trades': 0,
                        'winning_trades': 0,
                        'total_profit': 0.0,
                        'win_rate': 0.0,
                        'avg_profit': 0.0,
                        'last_trade_time': None
                    }
                self.pair_last_analysis[pair] = datetime.now() - timedelta(minutes=10)
            
            logger.info(f"🌍 Multi-pair trading inicializado")
            logger.info(f"📊 Sesión: {current_session}")
            logger.info(f"🎯 Pares activos: {self.active_pairs}")
            
            return {
                'success': True,
                'active_pairs': self.active_pairs,
                'session': current_session,
                'correlation_risk': await self._calculate_current_correlation_risk()
            }
            
        except Exception as e:
            logger.error(f"Error inicializando multi-pair trading: {e}")
            return {'success': False, 'error': str(e)}
    
    async def execute_multi_pair_analysis(self) -> List[Dict]:
        """Ejecutar análisis en todos los pares activos"""
        try:
            all_opportunities = []
            current_time = datetime.now()
            
            # Obtener posiciones actuales
            current_positions = await self.mt5.get_positions()
            
            # Verificar límites globales
            if len(current_positions) >= self.max_total_positions:
                logger.info(f"⚠️ Límite de posiciones totales alcanzado: {len(current_positions)}")
                return []
            
            # Analizar cada par activo
            analysis_tasks = []
            for pair in self.active_pairs:
                # Verificar si es tiempo de analizar este par
                if self._should_analyze_pair(pair, current_time):
                    task = self._analyze_single_pair(pair, current_positions)
                    analysis_tasks.append(task)
            
            # Ejecutar análisis en paralelo
            if analysis_tasks:
                pair_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
                
                # Procesar resultados
                for result in pair_results:
                    if isinstance(result, Exception):
                        logger.error(f"Error en análisis de par: {result}")
                        continue
                    
                    if result and isinstance(result, list):
                        all_opportunities.extend(result)
            
            # Filtrar y priorizar oportunidades
            filtered_opportunities = await self._filter_multi_pair_opportunities(
                all_opportunities, current_positions
            )
            
            logger.info(f"🌍 Multi-pair analysis: {len(filtered_opportunities)} oportunidades de {len(all_opportunities)} analizadas")
            
            return filtered_opportunities
            
        except Exception as e:
            logger.error(f"Error en análisis multi-pair: {e}")
            return []
    
    async def _analyze_single_pair(self, pair: str, current_positions: List[Dict]) -> List[Dict]:
        """Analizar un par específico"""
        try:
            # Verificar posiciones existentes para este par
            pair_positions = [pos for pos in current_positions if pos.get('symbol') == pair]
            if len(pair_positions) >= self.max_positions_per_pair:
                return []
            
            # Obtener datos del par
            df_m15 = await self.mt5.get_rates(symbol=pair, timeframe="M15", count=100)
            df_h1 = await self.mt5.get_rates(symbol=pair, timeframe="H1", count=50)
            
            if df_m15.empty or df_h1.empty:
                return []
            
            # Usar analizador avanzado adaptado para el par
            df_m15 = self.analyzer.calculate_advanced_indicators(df_m15)
            df_h1 = self.analyzer.calculate_advanced_indicators(df_h1)
            
            # Generar señales para el par
            signals_m15 = self.analyzer.generate_premium_signals(df_m15)
            signals_h1 = self.analyzer.generate_premium_signals(df_h1)
            
            opportunities = []
            
            # Procesar señal M15
            if signals_m15['signal'] != 'HOLD' and signals_m15['confidence'] >= 75:
                opportunity = await self._create_pair_opportunity(
                    pair, signals_m15, df_m15, 'M15'
                )
                if opportunity:
                    opportunities.append(opportunity)
            
            # Procesar señal H1 (mayor peso)
            if signals_h1['signal'] != 'HOLD' and signals_h1['confidence'] >= 80:
                opportunity = await self._create_pair_opportunity(
                    pair, signals_h1, df_h1, 'H1'
                )
                if opportunity:
                    opportunity['confidence'] += 5  # Bonus por timeframe mayor
                    opportunities.append(opportunity)
            
            # Actualizar tiempo de último análisis
            self.pair_last_analysis[pair] = datetime.now()
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error analizando par {pair}: {e}")
            return []
    
    async def _create_pair_opportunity(self, pair: str, signals: Dict, df: pd.DataFrame, timeframe: str) -> Optional[Dict]:
        """Crear oportunidad de trading para un par específico"""
        try:
            latest = df.iloc[-1]
            
            # Calcular SL y TP dinámicos
            entry_price = latest['close']
            atr = latest.get('atr', 0.001)
            
            # Ajustar SL/TP por características del par
            pair_info = self.correlation_analyzer.get_pair_info(pair)
            volatility_multiplier = 1.0
            
            # Ajustar por volatilidad del par
            if 'JPY' in pair:
                volatility_multiplier = 0.8  # JPY pares más volátiles
            elif 'GBP' in pair:
                volatility_multiplier = 1.2  # GBP más volátil
            elif 'AUD' in pair or 'NZD' in pair:
                volatility_multiplier = 1.1  # Commodities más volátiles
            
            if signals['signal'] == 'BUY':
                stop_loss = entry_price - (atr * 1.5 * volatility_multiplier)
                take_profit = entry_price + (atr * 3.0 * volatility_multiplier)
            else:
                stop_loss = entry_price + (atr * 1.5 * volatility_multiplier)
                take_profit = entry_price - (atr * 3.0 * volatility_multiplier)
            
            # Calcular métricas de riesgo
            risk_pips = abs(entry_price - stop_loss) * 10000
            reward_pips = abs(take_profit - entry_price) * 10000
            
            # Verificar R:R mínimo
            if reward_pips / risk_pips < 1.5:
                return None
            
            # Ajustar confianza por rendimiento histórico del par
            historical_performance = self.pair_performance.get(pair, {})
            win_rate = historical_performance.get('win_rate', 0.5)
            
            # Bonus/penalty por rendimiento histórico
            performance_adjustment = (win_rate - 0.5) * 20  # ±10% max
            adjusted_confidence = signals['confidence'] + performance_adjustment
            
            opportunity = {
                'signal': signals['signal'],
                'confidence': min(95, max(50, adjusted_confidence)),
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'symbol': pair,
                'timeframe': timeframe,
                'strategy': 'multi_pair_analysis',
                'reasons': signals.get('reasons', []) + [f"Multi-pair analysis {pair}"],
                'risk_pips': risk_pips,
                'reward_pips': reward_pips,
                'risk_reward_ratio': reward_pips / risk_pips,
                'pair_performance': {
                    'win_rate': win_rate,
                    'total_trades': historical_performance.get('total_trades', 0)
                },
                'volatility_multiplier': volatility_multiplier,
                'market_regime': signals.get('market_regime', {}),
                'priority': self._calculate_pair_priority(pair, signals['confidence'])
            }
            
            return opportunity
            
        except Exception as e:
            logger.error(f"Error creando oportunidad para {pair}: {e}")
            return None
    
    def _calculate_pair_priority(self, pair: str, confidence: float) -> float:
        """Calcular prioridad de un par basado en múltiples factores"""
        try:
            base_priority = confidence / 100
            
            # Bonus por rendimiento histórico
            performance = self.pair_performance.get(pair, {})
            win_rate_bonus = (performance.get('win_rate', 0.5) - 0.5) * 0.3
            
            # Bonus por sesión óptima
            current_session = self._get_current_session()
            pair_info = self.correlation_analyzer.get_pair_info(pair)
            session_bonus = 0.1 if current_session in pair_info.get('session_preference', []) else 0
            
            # Penalty por número de trades recientes
            recent_trades = performance.get('total_trades', 0)
            frequency_penalty = min(0.2, recent_trades * 0.02)  # Penalty por overtrading
            
            priority = base_priority + win_rate_bonus + session_bonus - frequency_penalty
            
            return max(0.0, min(1.0, priority))
            
        except Exception as e:
            logger.error(f"Error calculando prioridad de {pair}: {e}")
            return 0.5
    
    async def _filter_multi_pair_opportunities(self, opportunities: List[Dict], current_positions: List[Dict]) -> List[Dict]:
        """Filtrar oportunidades considerando correlaciones y límites"""
        try:
            if not opportunities:
                return []
            
            # Ordenar por prioridad
            sorted_opportunities = sorted(opportunities, key=lambda x: x['priority'], reverse=True)
            
            filtered = []
            simulated_positions = current_positions.copy()
            
            for opp in sorted_opportunities:
                # Verificar si se puede agregar esta posición
                can_add, reason = self.correlation_analyzer.can_add_position(
                    opp['symbol'], opp['signal'], simulated_positions
                )
                
                if can_add:
                    # Verificar límites de exposición por divisa
                    if await self._check_currency_exposure_limits(opp['symbol'], simulated_positions):
                        filtered.append(opp)
                        
                        # Simular adición para próximas verificaciones
                        simulated_positions.append({
                            'symbol': opp['symbol'],
                            'type': opp['signal'],
                            'volume': 0.1
                        })
                        
                        # Limitar número total de oportunidades
                        if len(filtered) >= 3:
                            break
                else:
                    logger.debug(f"Oportunidad {opp['symbol']} filtrada: {reason}")
            
            return filtered
            
        except Exception as e:
            logger.error(f"Error filtrando oportunidades multi-pair: {e}")
            return opportunities[:2]  # Fallback: primeras 2
    
    async def _check_currency_exposure_limits(self, new_pair: str, current_positions: List[Dict]) -> bool:
        """Verificar límites de exposición por divisa"""
        try:
            # Obtener información de cuenta
            account_info = await self.mt5.get_account_info()
            if not account_info:
                return False
            
            balance = account_info.get('balance', 10000)
            
            # Calcular exposición actual por divisa
            currency_exposure = {}
            
            for pos in current_positions:
                pair = pos.get('symbol', '')
                volume = pos.get('volume', 0)
                
                if len(pair) >= 6:
                    base, quote = pair[:3], pair[3:]
                    
                    # Calcular valor de exposición (simplificado)
                    exposure_value = volume * 100000  # Valor nocional aproximado
                    
                    currency_exposure[base] = currency_exposure.get(base, 0) + exposure_value
                    currency_exposure[quote] = currency_exposure.get(quote, 0) + exposure_value
            
            # Verificar si nuevo par excedería límites
            if len(new_pair) >= 6:
                new_base, new_quote = new_pair[:3], new_pair[3:]
                estimated_volume = balance * 0.02 / 1000  # 2% de riesgo estimado
                estimated_exposure = estimated_volume * 100000
                
                for currency in [new_base, new_quote]:
                    current_exp = currency_exposure.get(currency, 0)
                    total_exp = current_exp + estimated_exposure
                    exposure_pct = total_exp / balance
                    
                    if exposure_pct > self.max_currency_exposure:
                        logger.debug(f"Límite de exposición {currency}: {exposure_pct:.1%}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verificando límites de exposición: {e}")
            return True  # Permitir si hay error
    
    def _should_analyze_pair(self, pair: str, current_time: datetime) -> bool:
        """Determinar si es momento de analizar un par específico"""
        try:
            last_analysis = self.pair_last_analysis.get(pair)
            if not last_analysis:
                return True
            
            interval = self.analysis_intervals.get(pair, 180)  # Default 3 minutos
            time_diff = (current_time - last_analysis).total_seconds()
            
            return time_diff >= interval
            
        except Exception as e:
            logger.error(f"Error verificando si analizar {pair}: {e}")
            return True
    
    async def _calculate_current_correlation_risk(self) -> float:
        """Calcular riesgo de correlación actual"""
        try:
            current_positions = await self.mt5.get_positions()
            return self.correlation_analyzer.get_correlation_risk_score(current_positions)
            
        except Exception as e:
            logger.error(f"Error calculando riesgo de correlación: {e}")
            return 0.0
    
    def _get_current_session(self) -> str:
        """Obtener sesión de mercado actual"""
        hour = datetime.utcnow().hour
        
        if 13 <= hour <= 17:
            return 'overlap'
        elif 8 <= hour <= 17:
            return 'london'
        elif 13 <= hour <= 22:
            return 'new_york'
        else:
            return 'asian'
    
    def update_pair_performance(self, pair: str, trade_result: Dict):
        """Actualizar rendimiento de un par específico"""
        try:
            if pair not in self.pair_performance:
                self.pair_performance[pair] = {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'total_profit': 0.0,
                    'win_rate': 0.0,
                    'avg_profit': 0.0,
                    'last_trade_time': None
                }
            
            stats = self.pair_performance[pair]
            stats['total_trades'] += 1
            stats['total_profit'] += trade_result.get('profit', 0)
            stats['last_trade_time'] = datetime.now()
            
            if trade_result.get('profit', 0) > 0:
                stats['winning_trades'] += 1
            
            # Recalcular métricas
            stats['win_rate'] = stats['winning_trades'] / stats['total_trades']
            stats['avg_profit'] = stats['total_profit'] / stats['total_trades']
            
            logger.info(f"📊 {pair} performance updated: WR={stats['win_rate']:.1%}, Avg=${stats['avg_profit']:.2f}")
            
        except Exception as e:
            logger.error(f"Error actualizando rendimiento de {pair}: {e}")
    
    def get_multi_pair_status(self) -> Dict:
        """Obtener estado del sistema multi-pair"""
        try:
            return {
                'active_pairs': self.active_pairs,
                'max_pairs_active': self.max_pairs_active,
                'max_total_positions': self.max_total_positions,
                'current_session': self._get_current_session(),
                'pair_performance': {
                    pair: {
                        'total_trades': stats['total_trades'],
                        'win_rate': f"{stats['win_rate']:.1%}",
                        'avg_profit': f"${stats['avg_profit']:.2f}"
                    }
                    for pair, stats in self.pair_performance.items()
                    if stats['total_trades'] > 0
                },
                'analysis_intervals': self.analysis_intervals,
                'correlation_limits': {
                    'max_correlation_risk': f"{self.max_correlation_risk:.1%}",
                    'max_currency_exposure': f"{self.max_currency_exposure:.1%}"
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado multi-pair: {e}")
            return {'error': str(e)}
    
    async def rebalance_active_pairs(self):
        """Rebalancear pares activos basado en rendimiento y sesión"""
        try:
            current_session = self._get_current_session()
            
            # Obtener nuevas recomendaciones
            new_optimal_pairs = await self.correlation_analyzer.get_optimal_pairs_for_session(
                current_session, max_pairs=self.max_pairs_active
            )
            
            # Comparar con pares actuales
            pairs_to_add = set(new_optimal_pairs) - set(self.active_pairs)
            pairs_to_remove = set(self.active_pairs) - set(new_optimal_pairs)
            
            if pairs_to_add or pairs_to_remove:
                logger.info(f"🔄 Rebalanceando pares activos:")
                logger.info(f"  + Agregar: {list(pairs_to_add)}")
                logger.info(f"  - Remover: {list(pairs_to_remove)}")
                
                # Actualizar pares activos
                self.active_pairs = new_optimal_pairs
                
                # Inicializar tracking para nuevos pares
                for pair in pairs_to_add:
                    if pair not in self.pair_performance:
                        self.pair_performance[pair] = {
                            'total_trades': 0,
                            'winning_trades': 0,
                            'total_profit': 0.0,
                            'win_rate': 0.0,
                            'avg_profit': 0.0,
                            'last_trade_time': None
                        }
                    self.pair_last_analysis[pair] = datetime.now() - timedelta(minutes=10)
            
        except Exception as e:
            logger.error(f"Error rebalanceando pares activos: {e}")
    
    async def get_correlation_report(self) -> Dict:
        """Obtener reporte de correlaciones actual"""
        try:
            current_positions = await self.mt5.get_positions()
            correlation_risk = self.correlation_analyzer.get_correlation_risk_score(current_positions)
            
            report = self.correlation_analyzer.get_correlation_report(self.active_pairs)
            report['current_correlation_risk'] = f"{correlation_risk:.1%}"
            report['active_positions'] = len(current_positions)
            report['session_recommendations'] = await self.correlation_analyzer.get_session_pair_recommendations()
            
            return report
            
        except Exception as e:
            logger.error(f"Error generando reporte de correlaciones: {e}")
            return {'error': str(e)}

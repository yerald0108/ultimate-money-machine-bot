"""
Motor de Trading Optimizado para Máxima Rentabilidad
Integra análisis avanzado, gestión de riesgo optimizada y estrategias adaptativas
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import MetaTrader5 as mt5

try:
    # Importaciones relativas (cuando se usa como módulo)
    from .mt5_connector import MT5Connector
    from .risk_manager import AdvancedRiskManager
    from ..analysis.advanced_analyzer import AdvancedMarketAnalyzer
    from ..analysis.news_filter import EconomicNewsFilter
    from ..analysis.correlation_analyzer import CorrelationAnalyzer
    from ..strategies.strategy_manager import StrategyManager
    from .multi_pair_manager import MultiPairManager
    from ..ml.real_time_ml_system import RealTimeMLSystem
    from ..ml.genetic_optimizer import GeneticOptimizer
except ImportError:
    # Importaciones absolutas (cuando se ejecuta directamente)
    from trading.mt5_connector import MT5Connector
    from trading.risk_manager import AdvancedRiskManager
    from analysis.advanced_analyzer import AdvancedMarketAnalyzer
    from analysis.news_filter import EconomicNewsFilter
    from analysis.correlation_analyzer import CorrelationAnalyzer
    from strategies.strategy_manager import StrategyManager
    from trading.multi_pair_manager import MultiPairManager
    from ml.real_time_ml_system import RealTimeMLSystem
    from ml.genetic_optimizer import GeneticOptimizer

logger = logging.getLogger(__name__)

class OptimizedTradingEngine:
    def __init__(self, mt5_connector: MT5Connector, analyzer: AdvancedMarketAnalyzer, risk_manager: AdvancedRiskManager):
        self.mt5 = mt5_connector
        self.analyzer = analyzer
        self.risk_manager = risk_manager
        
        # Pasar conector MT5 al analizador para Multi-Timeframe
        if hasattr(self.analyzer, 'mt5_connector') and self.analyzer.mt5_connector is None:
            self.analyzer.mt5_connector = mt5_connector
            # Reinicializar MTF analyzer si está disponible
            if hasattr(self.analyzer, 'MTF_AVAILABLE') and self.analyzer.MTF_AVAILABLE:
                try:
                    from ..analysis.multi_timeframe_analyzer import MultiTimeframeAnalyzer
                    self.analyzer.mtf_analyzer = MultiTimeframeAnalyzer(mt5_connector)
                    self.analyzer.mtf_enabled = True
                    logger.info("✅ Multi-Timeframe Analysis activado")
                except ImportError:
                    logger.warning("⚠️ Multi-Timeframe Analysis no disponible")
        
        self.trading_active = False
        self.last_analysis_time = None
        self.analysis_interval = 180  # 3 minutos para análisis más frecuente
        
        # Configuración optimizada
        self.max_daily_trades = 8  # Reducido para mayor selectividad
        self.min_confidence = 75   # Aumentado para mayor precisión
        
        # Tracking avanzado
        self.trade_history = []
        self.performance_metrics = {}
        self.market_sessions = self._get_market_sessions()
        
        # Filtro de noticias económicas
        self.news_filter = EconomicNewsFilter()
        
        # Sistema de análisis de correlaciones
        self.correlation_analyzer = CorrelationAnalyzer(mt5_connector)
        
        # Sistema de gestión multi-estrategia
        self.strategy_manager = StrategyManager(mt5_connector, analyzer, risk_manager)
        
        # Gestor multi-pair
        self.multi_pair_manager = MultiPairManager(
            mt5_connector, analyzer, risk_manager, self.correlation_analyzer
        )
        
        # Sistema de Machine Learning en tiempo real
        self.ml_system = RealTimeMLSystem()
        
        # Optimizador genético
        self.genetic_optimizer = GeneticOptimizer()
        
        # Inicializar ML
        self._initialize_ml_system()
        
        # Task para análisis continuo
        self.analysis_task = None
        self.trailing_stop_task = None
        self.multi_strategy_task = None
        self.multi_pair_task = None
        self.ml_optimization_task = None
    
    def _get_market_sessions(self) -> Dict:
        """Definir sesiones de mercado para optimizar timing"""
        return {
            'asian': {'start': 0, 'end': 9},      # 00:00 - 09:00 UTC
            'london': {'start': 8, 'end': 17},    # 08:00 - 17:00 UTC  
            'new_york': {'start': 13, 'end': 22}, # 13:00 - 22:00 UTC
            'overlap_london_ny': {'start': 13, 'end': 17}  # Mejor momento
        }
    
    def _get_current_session(self) -> str:
        """Determinar sesión de mercado actual"""
        current_hour = datetime.utcnow().hour
        
        if (self.market_sessions['overlap_london_ny']['start'] <= current_hour <= 
            self.market_sessions['overlap_london_ny']['end']):
            return 'overlap_london_ny'
        elif (self.market_sessions['london']['start'] <= current_hour <= 
              self.market_sessions['london']['end']):
            return 'london'
        elif (self.market_sessions['new_york']['start'] <= current_hour <= 
              self.market_sessions['new_york']['end']):
            return 'new_york'
        elif (self.market_sessions['asian']['start'] <= current_hour <= 
              self.market_sessions['asian']['end']):
            return 'asian'
        else:
            return 'off_hours'
    
    def _initialize_ml_system(self):
        """Inicializar sistema de Machine Learning"""
        try:
            # Intentar cargar modelo previo
            model_path = "data/ml_model.json"
            try:
                self.ml_system.load_model(model_path)
                logger.info("🤖 Modelo ML cargado exitosamente")
            except:
                logger.info("🤖 Inicializando nuevo modelo ML")
            
            # Inicializar población genética
            self.genetic_optimizer.initialize_population()
            logger.info("🧬 Optimizador genético inicializado")
            
        except Exception as e:
            logger.error(f"Error inicializando ML: {e}")
    
    async def start_trading(self) -> Dict:
        """Iniciar trading optimizado"""
        try:
            if not self.mt5.is_connected():
                return {'success': False, 'error': 'No hay conexión con MT5'}
            
            self.trading_active = True
            
            # Iniciar análisis continuo optimizado
            if self.analysis_task is None or self.analysis_task.done():
                self.analysis_task = asyncio.create_task(self._continuous_analysis_optimized())
            
            # Iniciar gestión de trailing stops
            try:
                if self.trailing_stop_task is None or self.trailing_stop_task.done():
                    self.trailing_stop_task = asyncio.create_task(self._manage_trailing_stops())
                    logger.info("Tarea de trailing stops iniciada")
            except Exception as trailing_error:
                logger.error(f"Error iniciando trailing stops: {trailing_error}")
                # Continuar sin trailing stops si hay error
            
            # Iniciar análisis multi-estrategia
            try:
                if self.multi_strategy_task is None or self.multi_strategy_task.done():
                    self.multi_strategy_task = asyncio.create_task(self._multi_strategy_analysis_loop())
                    logger.info("🎯 Sistema multi-estrategia iniciado")
            except Exception as strategy_error:
                logger.error(f"Error iniciando multi-estrategia: {strategy_error}")
                # Continuar con análisis básico si hay error
            
            # Iniciar análisis multi-pair
            try:
                # Inicializar multi-pair trading
                init_result = await self.multi_pair_manager.initialize_multi_pair_trading()
                if init_result.get('success'):
                    if self.multi_pair_task is None or self.multi_pair_task.done():
                        self.multi_pair_task = asyncio.create_task(self._multi_pair_analysis_loop())
                        logger.info("🌍 Sistema multi-pair iniciado")
                else:
                    logger.warning(f"⚠️ Multi-pair no inicializado: {init_result.get('error')}")
            except Exception as pair_error:
                logger.error(f"Error iniciando multi-pair: {pair_error}")
                # Continuar sin multi-pair si hay error
            
            # Iniciar optimización ML periódica
            try:
                if self.ml_optimization_task is None or self.ml_optimization_task.done():
                    self.ml_optimization_task = asyncio.create_task(self._ml_optimization_loop())
                    logger.info("🤖 Sistema de optimización ML iniciado")
            except Exception as ml_error:
                logger.error(f"Error iniciando optimización ML: {ml_error}")
                # Continuar sin optimización ML si hay error
            
            logger.info("Trading optimizado iniciado")
            return {'success': True, 'message': 'Trading optimizado iniciado correctamente'}
            
        except Exception as e:
            logger.error(f"Error iniciando trading optimizado: {e}")
            return {'success': False, 'error': str(e)}
    
    async def stop_trading(self) -> Dict:
        """Pausar trading optimizado"""
        try:
            self.trading_active = False
            
            # Cancelar tasks
            if self.analysis_task and not self.analysis_task.done():
                self.analysis_task.cancel()
            
            if self.trailing_stop_task and not self.trailing_stop_task.done():
                self.trailing_stop_task.cancel()
            
            if self.multi_strategy_task and not self.multi_strategy_task.done():
                self.multi_strategy_task.cancel()
            
            if self.multi_pair_task and not self.multi_pair_task.done():
                self.multi_pair_task.cancel()
            
            if self.ml_optimization_task and not self.ml_optimization_task.done():
                self.ml_optimization_task.cancel()
            
            logger.info("Trading optimizado pausado")
            return {'success': True, 'message': 'Trading optimizado pausado correctamente'}
            
        except Exception as e:
            logger.error(f"Error pausando trading optimizado: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _continuous_analysis_optimized(self):
        """Análisis continuo optimizado con timing de mercado"""
        while self.trading_active:
            try:
                current_session = self._get_current_session()
                
                # Ajustar frecuencia según sesión
                if current_session == 'overlap_london_ny':
                    interval = 120  # 2 minutos en la mejor sesión
                elif current_session in ['london', 'new_york']:
                    interval = 180  # 3 minutos en sesiones activas
                else:
                    interval = 300  # 5 minutos en sesiones menos activas
                
                # Realizar análisis optimizado
                await self._analyze_and_trade_optimized()
                
                # Esperar intervalo ajustado
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                logger.info("Análisis optimizado cancelado")
                break
            except Exception as e:
                logger.error(f"Error en análisis optimizado: {e}")
                await asyncio.sleep(60)
    
    async def _analyze_and_trade_optimized(self):
        """Análisis y trading optimizado"""
        try:
            # Análisis Multi-Timeframe si está disponible, sino single-timeframe
            if hasattr(self.analyzer, 'should_trade_premium_mtf'):
                should_trade, signal, trade_info = await self.analyzer.should_trade_premium_mtf()
            else:
                # Fallback al análisis single-timeframe
                df = await self.mt5.get_rates(count=200)
                if df.empty:
                    logger.warning("No se pudieron obtener datos de mercado")
                    return
                df = self.analyzer.calculate_advanced_indicators(df)
                should_trade, signal, trade_info = self.analyzer.should_trade_premium(df)
                
                # INTEGRACIÓN ML: Obtener predicción adicional
                ml_signal, ml_confidence, ml_reason = await self._get_ml_prediction(df, trade_info)
                
                # Combinar análisis tradicional con ML
                if ml_signal != 'HOLD' and ml_confidence > 70:
                    # Si ML está muy confiado, considerar su señal
                    if ml_signal == signal:
                        # ML confirma señal tradicional - aumentar confianza
                        trade_info['confidence'] = min(95, trade_info['confidence'] + 10)
                        trade_info['ml_confirmation'] = True
                        logger.info(f"🤖 ML confirma señal: {ml_signal} (confianza ML: {ml_confidence:.1f}%)")
                    elif trade_info['confidence'] < 80:
                        # ML sugiere señal diferente y confianza tradicional no es muy alta
                        signal = ml_signal
                        trade_info['confidence'] = ml_confidence
                        trade_info['ml_override'] = True
                        should_trade = True
                        logger.info(f"🤖 ML override: {ml_signal} (confianza ML: {ml_confidence:.1f}%)")
                
                # Registrar predicción ML para aprendizaje futuro
                trade_info['ml_prediction'] = {
                    'signal': ml_signal,
                    'confidence': ml_confidence,
                    'reason': ml_reason
                }
            
            if should_trade and signal != 'HOLD':
                # FILTRO DE NOTICIAS ECONÓMICAS
                should_avoid_news, news_reason = self.news_filter.should_avoid_trading()
                if should_avoid_news:
                    logger.info(f"🚫 Trade rechazado por filtro de noticias: {news_reason}")
                    return
                
                # Verificar condiciones adicionales
                current_positions = await self.mt5.get_positions(self.mt5.symbol)
                account_info = await self.mt5.get_account_info()
                
                if not account_info:
                    logger.error("No se pudo obtener información de la cuenta")
                    return
                
                # Calcular profit diario
                daily_profit = await self._calculate_daily_profit()
                
                # Verificar con risk manager
                can_trade, reason = self.risk_manager.should_allow_new_trade(
                    current_positions, daily_profit, trade_info['confidence']
                )
                
                if can_trade:
                    # Verificar timing de mercado
                    current_session = self._get_current_session()
                    
                    # Bonus de confianza para mejores sesiones
                    session_bonus = 0
                    if current_session == 'overlap_london_ny':
                        session_bonus = 5  # +5% confianza en overlap
                    elif current_session in ['london', 'new_york']:
                        session_bonus = 2  # +2% confianza en sesiones principales
                    
                    adjusted_confidence = trade_info['confidence'] + session_bonus
                    
                    if adjusted_confidence >= self.min_confidence:
                        logger.info(f"Señal optimizada detectada: {signal}")
                        logger.info(f"Confianza: {adjusted_confidence:.1f}% (sesión: {current_session})")
                        
                        # Log de régimen de mercado con manejo de errores
                        try:
                            regime = trade_info.get('market_regime', {}).get('regime', 'UNKNOWN')
                            logger.info(f"Régimen de mercado: {regime}")
                        except Exception as e:
                            logger.warning(f"Error accediendo a market_regime: {e}")
                        
                        # Ejecutar trade optimizado
                        await self._execute_optimized_trade(signal, trade_info, account_info)
                    else:
                        logger.info(f"Señal rechazada por confianza insuficiente: {adjusted_confidence:.1f}%")
                else:
                    logger.info(f"Trade rechazado por risk manager: {reason}")
            
            self.last_analysis_time = datetime.now()
            
        except Exception as e:
            logger.error(f"Error en análisis optimizado: {e}")
    
    async def _execute_optimized_trade(self, signal: str, trade_info: Dict, account_info: Dict):
        """Ejecutar trade con optimizaciones avanzadas"""
        try:
            # Calcular tamaño de posición optimizado
            recent_performance = self.trade_history[-20:] if len(self.trade_history) >= 20 else self.trade_history
            market_regime = trade_info.get('market_regime', {
                'regime': 'UNKNOWN', 
                'strength': 50, 
                'trend_direction': 0
            })
            
            lot_size = self.risk_manager.calculate_optimal_position_size(
                balance=account_info['balance'],
                confidence=trade_info['confidence'],
                market_regime=market_regime,
                recent_performance=recent_performance,
                stop_loss_pips=20  # Calculado dinámicamente después
            )
            
            # Usar SL/TP dinámicos del analizador avanzado
            entry_price = trade_info['entry_price']
            stop_loss = trade_info['stop_loss']
            take_profit = trade_info['take_profit']
            
            # Ejecutar orden con manejo robusto de market_regime
            regime_str = market_regime.get('regime', 'UNKNOWN')
            result = await self.mt5.send_order(
                action=signal,
                volume=lot_size,
                sl=stop_loss,
                tp=take_profit,
                comment=f"OptBot-{signal}-{trade_info['confidence']:.0f}%-{regime_str}"
            )
            
            if result['success']:
                # Registrar trade
                trade_record = {
                    'timestamp': datetime.now(),
                    'signal': signal,
                    'confidence': trade_info['confidence'],
                    'lot_size': lot_size,
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'market_regime': market_regime,
                    'session': self._get_current_session(),
                    'order_id': result['order'],
                    'reasons': trade_info['reasons'],
                    'ml_status': trade_info.get('ml_status', 'N/A')
                }
            
                self.trade_history.append(trade_record)
                
                logger.info(f"🎯 TRADE EJECUTADO: {signal} | Confianza: {trade_info['confidence']:.1f}% | Lotes: {lot_size}")
                
                # Registrar trade para aprendizaje ML
                self._record_trade_for_ml(trade_record)
                    
            else:
                logger.error(f"Error ejecutando trade optimizado: {result['error']}")
                
        except Exception as e:
            logger.error(f"Error ejecutando trade optimizado: {e}")
    
    async def _record_trade_closure(self, position: Dict, close_reason: str):
        """Registrar cierre de trade para ML"""
        try:
            # Buscar el trade en el historial
            for trade in reversed(self.trade_history):
                if trade.get('order_id') == position.get('ticket'):
                    # Calcular profit
                    profit = position.get('profit', 0)
                    
                    # Crear datos para ML
                    ml_trade_data = {
                        'entry_time': trade['timestamp'],
                        'exit_time': datetime.now(),
                        'signal': trade['signal'],
                        'confidence': trade['confidence'],
                        'profit': profit,
                        'success': profit > 0,
                        'close_reason': close_reason,
                        'market_regime': trade['market_regime'],
                        'session': trade['session'],
                        'reasons': trade['reasons'],
                        'indicators': trade.get('indicators', {}),
                        'pips': (profit / trade['lot_size']) / 10 if trade['lot_size'] > 0 else 0
                    }
                    
                    # Registrar en ML
                    if hasattr(self.analyzer, 'record_trade_result'):
                        self.analyzer.record_trade_result(ml_trade_data)
                        logger.info(f"Trade cerrado registrado en ML: ${profit:.2f}")
                    
                    break
                    
        except Exception as e:
            logger.error(f"Error registrando cierre de trade en ML: {e}")
    
    async def _manage_trailing_stops(self):
        """Gestionar trailing stops dinámicos"""
        logger.info("Iniciando gestión de trailing stops")
        
        while self.trading_active:
            try:
                # Obtener posiciones abiertas
                positions = await self.mt5.get_positions()
                
                if positions:
                    logger.debug(f"Gestionando trailing stops para {len(positions)} posiciones")
                    
                    # Obtener datos actuales para ATR
                    df = await self.mt5.get_rates(count=50)
                    if not df.empty:
                        df = self.analyzer.calculate_advanced_indicators(df)
                        current_atr = df.iloc[-1].get('atr', 0.0010)
                        current_price = df.iloc[-1]['close']
                        
                        for position in positions:
                            try:
                                # Calcular nuevo trailing stop si el risk manager lo soporta
                                if hasattr(self.risk_manager, 'calculate_trailing_stop'):
                                    new_sl = self.risk_manager.calculate_trailing_stop(
                                        position, current_price, current_atr
                                    )
                                    
                                    if new_sl:
                                        logger.info(f"Trailing stop calculado para posición {position.get('ticket', 'N/A')}: {new_sl}")
                                        
                                        # Aplicar trailing stop
                                        modify_result = await self.mt5.modify_position(
                                            ticket=position.get('ticket'),
                                            new_sl=new_sl
                                        )
                                        
                                        if modify_result['success']:
                                            logger.info(f"✅ Trailing stop aplicado: {new_sl}")
                                        else:
                                            logger.warning(f"❌ Error aplicando trailing stop: {modify_result['error']}")
                                        
                            except Exception as pos_error:
                                logger.warning(f"Error procesando posición: {pos_error}")
                
                # Verificar cada 30 segundos
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                logger.info("Gestión de trailing stops cancelada")
                break
            except Exception as e:
                logger.error(f"Error en gestión de trailing stops: {e}")
                await asyncio.sleep(60)  # Esperar más tiempo en caso de error
                
        logger.info("Gestión de trailing stops finalizada")
    
    async def _multi_strategy_analysis_loop(self):
        """Loop principal del sistema multi-estrategia"""
        logger.info("🎯 Iniciando loop de análisis multi-estrategia")
        
        while self.trading_active:
            try:
                # Ejecutar análisis multi-estrategia
                opportunities = await self.strategy_manager.execute_multi_strategy_analysis()
                
                if opportunities:
                    logger.info(f"🎯 Multi-Strategy: {len(opportunities)} oportunidades encontradas")
                    
                    # Procesar cada oportunidad
                    for opportunity in opportunities:
                        try:
                            # Verificar filtro de noticias
                            should_avoid_news, news_reason = self.news_filter.should_avoid_trading()
                            if should_avoid_news:
                                logger.info(f"🚫 Oportunidad {opportunity['strategy']} rechazada por noticias: {news_reason}")
                                continue
                            
                            # Verificar condiciones adicionales
                            account_info = await self.mt5.get_account_info()
                            if not account_info:
                                continue
                            
                            # Calcular profit diario
                            daily_profit = await self._calculate_daily_profit()
                            
                            # Verificar con risk manager
                            can_trade, reason = self.risk_manager.should_allow_new_trade(
                                [], daily_profit, opportunity['confidence']
                            )
                            
                            if can_trade:
                                # Ejecutar trade multi-estrategia
                                await self._execute_multi_strategy_trade(opportunity, account_info)
                            else:
                                logger.info(f"🚫 Oportunidad {opportunity['strategy']} rechazada por risk manager: {reason}")
                                
                        except Exception as opp_error:
                            logger.error(f"Error procesando oportunidad: {opp_error}")
                            continue
                
                # Esperar antes del próximo análisis (más frecuente que el análisis básico)
                await asyncio.sleep(90)  # 1.5 minutos
                
            except asyncio.CancelledError:
                logger.info("🎯 Loop multi-estrategia cancelado")
                break
            except Exception as e:
                logger.error(f"Error en loop multi-estrategia: {e}")
                await asyncio.sleep(120)  # Esperar más tiempo en caso de error
                
        logger.info("🎯 Loop multi-estrategia finalizado")
    
    async def _execute_multi_strategy_trade(self, opportunity: Dict, account_info: Dict):
        """Ejecutar trade del sistema multi-estrategia"""
        try:
            strategy_type = opportunity.get('strategy_type', 'unknown')
            signal = opportunity['signal']
            
            logger.info(f"🎯 Ejecutando trade multi-estrategia: {strategy_type} - {signal}")
            
            # Calcular tamaño de posición específico para la estrategia
            strategy_config = self.strategy_manager.strategy_config.get(
                getattr(self.strategy_manager.StrategyType, strategy_type.upper(), None),
                {'risk_per_trade': 2.0}
            )
            
            risk_percentage = strategy_config['risk_per_trade']
            
            # Calcular lot size basado en el riesgo de la estrategia
            risk_pips = opportunity.get('risk_pips', 20)
            balance = account_info['balance']
            risk_amount = balance * (risk_percentage / 100)
            pip_value = 10  # Para EUR/USD
            lot_size = risk_amount / (risk_pips * pip_value)
            lot_size = round(max(0.01, min(2.0, lot_size)), 2)
            
            # Ejecutar orden
            result = await self.mt5.send_order(
                action=signal,
                volume=lot_size,
                sl=opportunity.get('stop_loss'),
                tp=opportunity.get('take_profit'),
                comment=f"Multi-{strategy_type}-{opportunity['confidence']:.0f}%"
            )
            
            if result['success']:
                # Registrar trade
                trade_record = {
                    'timestamp': datetime.now(),
                    'signal': signal,
                    'strategy_type': strategy_type,
                    'confidence': opportunity['confidence'],
                    'lot_size': lot_size,
                    'entry_price': opportunity['entry_price'],
                    'stop_loss': opportunity.get('stop_loss'),
                    'take_profit': opportunity.get('take_profit'),
                    'timeframe': opportunity.get('timeframe', 'multi'),
                    'session': self._get_current_session(),
                    'order_id': result['order'],
                    'reasons': opportunity.get('reasons', []),
                    'risk_pips': risk_pips,
                    'reward_pips': opportunity.get('reward_pips', risk_pips * 2)
                }
                
                self.trade_history.append(trade_record)
                
                # Notificar al strategy manager para estadísticas
                if hasattr(self.strategy_manager, 'StrategyType'):
                    try:
                        strategy_enum = getattr(self.strategy_manager.StrategyType, strategy_type.upper())
                        # Registrar ejecución en la estrategia específica
                        if strategy_type == 'scalping' and hasattr(self.strategy_manager.strategies.get(strategy_enum), 'record_trade_execution'):
                            self.strategy_manager.strategies[strategy_enum].record_trade_execution(opportunity)
                    except:
                        pass
                
                logger.info(f"🎯 MULTI-STRATEGY TRADE EJECUTADO: {strategy_type} {signal} | Confianza: {opportunity['confidence']:.1f}% | Lotes: {lot_size}")
                
            else:
                logger.error(f"Error ejecutando trade multi-estrategia: {result['error']}")
                
        except Exception as e:
            logger.error(f"Error ejecutando trade multi-estrategia: {e}")
    
    async def _multi_pair_analysis_loop(self):
        """Loop principal del sistema multi-pair"""
        logger.info("🌍 Iniciando loop de análisis multi-pair")
        
        while self.trading_active:
            try:
                # Ejecutar análisis multi-pair
                opportunities = await self.multi_pair_manager.execute_multi_pair_analysis()
                
                if opportunities:
                    logger.info(f"🌍 Multi-Pair: {len(opportunities)} oportunidades encontradas")
                    
                    # Procesar cada oportunidad
                    for opportunity in opportunities:
                        try:
                            # Verificar filtro de noticias
                            should_avoid_news, news_reason = self.news_filter.should_avoid_trading()
                            if should_avoid_news:
                                logger.info(f"🚫 Oportunidad {opportunity['symbol']} rechazada por noticias: {news_reason}")
                                continue
                            
                            # Verificar condiciones adicionales
                            account_info = await self.mt5.get_account_info()
                            if not account_info:
                                continue
                            
                            # Calcular profit diario
                            daily_profit = await self._calculate_daily_profit()
                            
                            # Verificar con risk manager
                            can_trade, reason = self.risk_manager.should_allow_new_trade(
                                [], daily_profit, opportunity['confidence']
                            )
                            
                            if can_trade:
                                # Ejecutar trade multi-pair
                                await self._execute_multi_pair_trade(opportunity, account_info)
                            else:
                                logger.info(f"🚫 Oportunidad {opportunity['symbol']} rechazada por risk manager: {reason}")
                                
                        except Exception as opp_error:
                            logger.error(f"Error procesando oportunidad multi-pair: {opp_error}")
                            continue
                
                # Rebalancear pares activos cada 30 minutos
                if datetime.now().minute % 30 == 0:
                    await self.multi_pair_manager.rebalance_active_pairs()
                
                # Esperar antes del próximo análisis
                await asyncio.sleep(180)  # 3 minutos
                
            except asyncio.CancelledError:
                logger.info("🌍 Loop multi-pair cancelado")
                break
            except Exception as e:
                logger.error(f"Error en loop multi-pair: {e}")
                await asyncio.sleep(240)  # Esperar más tiempo en caso de error
                
        logger.info("🌍 Loop multi-pair finalizado")
    
    async def _execute_multi_pair_trade(self, opportunity: Dict, account_info: Dict):
        """Ejecutar trade del sistema multi-pair"""
        try:
            pair = opportunity.get('symbol', 'EURUSD')
            signal = opportunity['signal']
            
            logger.info(f"🌍 Ejecutando trade multi-pair: {pair} - {signal}")
            
            # Calcular tamaño de posición basado en correlaciones
            correlation_weights = self.correlation_analyzer.get_optimal_pair_weights([pair])
            base_risk = 2.0  # 2% base
            adjusted_risk = base_risk * correlation_weights.get(pair, 1.0)
            
            # Calcular lot size
            risk_pips = opportunity.get('risk_pips', 20)
            balance = account_info['balance']
            risk_amount = balance * (adjusted_risk / 100)
            pip_value = 10  # Para la mayoría de pares
            lot_size = risk_amount / (risk_pips * pip_value)
            lot_size = round(max(0.01, min(1.0, lot_size)), 2)
            
            # Ejecutar orden
            result = await self.mt5.send_order(
                symbol=pair,
                action=signal,
                volume=lot_size,
                sl=opportunity.get('stop_loss'),
                tp=opportunity.get('take_profit'),
                comment=f"MultiPair-{pair}-{opportunity['confidence']:.0f}%"
            )
            
            if result['success']:
                # Registrar trade
                trade_record = {
                    'timestamp': datetime.now(),
                    'signal': signal,
                    'symbol': pair,
                    'strategy_type': 'multi_pair',
                    'confidence': opportunity['confidence'],
                    'lot_size': lot_size,
                    'entry_price': opportunity['entry_price'],
                    'stop_loss': opportunity.get('stop_loss'),
                    'take_profit': opportunity.get('take_profit'),
                    'timeframe': opportunity.get('timeframe', 'M15'),
                    'session': self._get_current_session(),
                    'order_id': result['order'],
                    'reasons': opportunity.get('reasons', []),
                    'risk_pips': risk_pips,
                    'reward_pips': opportunity.get('reward_pips', risk_pips * 2),
                    'correlation_weight': correlation_weights.get(pair, 1.0)
                }
                
                self.trade_history.append(trade_record)
                
                # Actualizar rendimiento del par
                self.multi_pair_manager.update_pair_performance(pair, {'profit': 0})  # Se actualizará al cerrar
                
                logger.info(f"🌍 MULTI-PAIR TRADE EJECUTADO: {pair} {signal} | Confianza: {opportunity['confidence']:.1f}% | Lotes: {lot_size}")
                
            else:
                logger.error(f"Error ejecutando trade multi-pair: {result['error']}")
                
        except Exception as e:
            logger.error(f"Error ejecutando trade multi-pair: {e}")
    
    async def _get_ml_prediction(self, df, trade_info: Dict) -> Tuple[str, float, str]:
        """Obtener predicción del sistema ML"""
        try:
            # Extraer indicadores del DataFrame
            latest = df.iloc[-1]
            indicators = {
                'rsi': latest.get('rsi', 50),
                'macd': latest.get('macd', 0),
                'bb_position': latest.get('bb_position', 0.5),
                'ema_alignment': latest.get('ema_alignment', 0),
                'atr': latest.get('atr', 0.001),
                'adx': latest.get('adx', 25),
                'momentum': latest.get('momentum', 0),
                'volume_ratio': latest.get('volume_ratio', 1.0)
            }
            
            # Datos de mercado adicionales
            market_data = {
                'session': self._get_current_session(),
                'volatility': indicators['atr'],
                'trend_strength': indicators['adx'] / 100
            }
            
            # Obtener predicción ML
            ml_signal, ml_confidence, ml_reason = self.ml_system.predict_market_signal(indicators, market_data)
            
            return ml_signal, ml_confidence, ml_reason
            
        except Exception as e:
            logger.error(f"Error obteniendo predicción ML: {e}")
            return 'HOLD', 50.0, 'Error en ML'
    
    def _record_trade_for_ml(self, trade_result: Dict):
        """Registrar resultado de trade para aprendizaje ML"""
        try:
            # Preparar datos para ML
            ml_data = {
                'success': trade_result.get('profit', 0) > 0,
                'profit': trade_result.get('profit', 0),
                'confidence': trade_result.get('confidence', 50),
                'signal': trade_result.get('signal', 'HOLD'),
                'indicators': trade_result.get('indicators', {}),
                'session': trade_result.get('session', 'unknown'),
                'market_regime': trade_result.get('market_regime', 'unknown'),
                'predicted_signal': trade_result.get('ml_prediction', {}).get('signal', 'HOLD')
            }
            
            # Registrar en sistema ML
            self.ml_system.record_trade_result(ml_data)
            
        except Exception as e:
            logger.error(f"Error registrando trade para ML: {e}")
    
    async def _optimize_parameters_with_genetic(self):
        """Optimizar parámetros usando algoritmo genético"""
        try:
            # Solo ejecutar si tenemos suficientes datos
            if len(self.trade_history) < 50:
                return
            
            logger.info("🧬 Iniciando optimización genética de parámetros...")
            
            # Preparar datos de trades para evaluación
            recent_trades = self.trade_history[-100:]  # Últimos 100 trades
            
            # Simular resultados para cada individuo de la población
            trade_results_per_individual = []
            
            for individual in self.genetic_optimizer.population:
                # Simular cómo habría funcionado este conjunto de parámetros
                simulated_results = self._simulate_trades_with_parameters(individual, recent_trades)
                trade_results_per_individual.append(simulated_results)
            
            # Evolucionar población
            self.genetic_optimizer.evolve_generation(trade_results_per_individual)
            
            # Aplicar mejores parámetros si hay mejora significativa
            best_params = self.genetic_optimizer.get_best_parameters()
            if best_params and self.genetic_optimizer.best_fitness > 50:  # Umbral mínimo
                self._apply_optimized_parameters(best_params)
                logger.info(f"🧬 Parámetros optimizados aplicados. Fitness: {self.genetic_optimizer.best_fitness:.2f}")
            
        except Exception as e:
            logger.error(f"Error en optimización genética: {e}")
    
    def _simulate_trades_with_parameters(self, parameters: Dict, historical_trades: List[Dict]) -> List[Dict]:
        """Simular trades con parámetros específicos"""
        try:
            simulated_results = []
            
            for trade in historical_trades:
                # Simular si este trade habría sido ejecutado con los nuevos parámetros
                would_execute = self._would_execute_with_parameters(trade, parameters)
                
                if would_execute:
                    # Simular resultado (usar resultado real pero ajustar por parámetros)
                    simulated_profit = trade.get('profit', 0)
                    
                    # Ajustar profit basado en nuevos parámetros de SL/TP
                    sl_multiplier = parameters.get('stop_loss_atr', 1.5)
                    tp_multiplier = parameters.get('take_profit_atr', 3.0)
                    
                    # Ajuste simplificado del profit
                    if simulated_profit > 0:
                        simulated_profit *= (tp_multiplier / 3.0)  # Normalizar a parámetros base
                    else:
                        simulated_profit *= (sl_multiplier / 1.5)  # Normalizar a parámetros base
                    
                    simulated_results.append({
                        'profit': simulated_profit,
                        'success': simulated_profit > 0,
                        'confidence': trade.get('confidence', 50)
                    })
            
            return simulated_results
            
        except Exception as e:
            logger.error(f"Error simulando trades: {e}")
            return []
    
    def _would_execute_with_parameters(self, trade: Dict, parameters: Dict) -> bool:
        """Determinar si un trade habría sido ejecutado con parámetros específicos"""
        try:
            # Verificar umbral de confianza
            min_confidence = parameters.get('min_confidence', 75)
            if trade.get('confidence', 0) < min_confidence:
                return False
            
            # Verificar otros filtros basados en parámetros
            # (simplificado para este ejemplo)
            
            return True
            
        except Exception as e:
            logger.error(f"Error evaluando ejecución con parámetros: {e}")
            return False
    
    def _apply_optimized_parameters(self, parameters: Dict):
        """Aplicar parámetros optimizados al sistema"""
        try:
            # Actualizar parámetros del sistema ML
            ml_params = self.ml_system.get_adaptive_parameters()
            
            # Mapear parámetros genéticos a parámetros ML
            if 'min_confidence' in parameters:
                ml_params['min_confidence'] = parameters['min_confidence']
            
            if 'rsi_oversold' in parameters:
                ml_params['rsi_oversold'] = parameters['rsi_oversold']
            
            if 'rsi_overbought' in parameters:
                ml_params['rsi_overbought'] = parameters['rsi_overbought']
            
            # Actualizar otros parámetros del motor
            if 'min_confidence' in parameters:
                self.min_confidence = parameters['min_confidence']
            
            logger.info("🧬 Parámetros optimizados aplicados al sistema")
            
        except Exception as e:
            logger.error(f"Error aplicando parámetros optimizados: {e}")
    
    def get_ml_statistics(self) -> Dict:
        """Obtener estadísticas del sistema ML"""
        try:
            ml_stats = self.ml_system.get_learning_statistics()
            genetic_stats = self.genetic_optimizer.get_evolution_statistics()
            
            return {
                'ml_system': ml_stats,
                'genetic_optimizer': genetic_stats,
                'adaptive_parameters': self.ml_system.get_adaptive_parameters(),
                'indicator_weights': self.ml_system.get_indicator_weights(),
                'model_summary': self.ml_system.get_model_summary()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas ML: {e}")
            return {'error': str(e)}
    
    async def _ml_optimization_loop(self):
        """Loop de optimización ML y genética"""
        logger.info("🤖 Iniciando loop de optimización ML")
        
        while self.trading_active:
            try:
                # Optimización cada 2 horas
                await asyncio.sleep(7200)  # 2 horas
                
                if not self.trading_active:
                    break
                
                # Ejecutar optimización genética si hay suficientes datos
                if len(self.trade_history) >= 50:
                    await self._optimize_parameters_with_genetic()
                
                # Guardar modelo ML cada 4 horas
                if len(self.trade_history) % 20 == 0:  # Cada ~20 trades
                    try:
                        import os
                        os.makedirs("data", exist_ok=True)
                        self.ml_system.save_model("data/ml_model.json")
                        self.genetic_optimizer.save_evolution_state("data/genetic_state.json")
                        logger.info("🤖 Modelo ML y estado genético guardados")
                    except Exception as save_error:
                        logger.error(f"Error guardando modelos: {save_error}")
                
            except asyncio.CancelledError:
                logger.info("🤖 Loop de optimización ML cancelado")
                break
            except Exception as e:
                logger.error(f"Error en optimización ML: {e}")
                await asyncio.sleep(3600)  # Esperar 1 hora en caso de error
        
        logger.info("🤖 Loop de optimización ML finalizado")
    
    async def get_optimized_status(self) -> Dict:
        """Obtener estado optimizado del motor"""
        try:
            # Estado básico
            basic_status = await self.get_status()
            
            # Métricas de riesgo
            risk_metrics = self.risk_manager.get_risk_metrics()
            
            # Sesión actual
            current_session = self._get_current_session()
            
            # Performance reciente
            recent_trades = self.trade_history[-10:] if len(self.trade_history) >= 10 else self.trade_history
            
            win_rate = 0
            avg_profit = 0
            if recent_trades:
                wins = sum(1 for trade in recent_trades if trade.get('profit', 0) > 0)
                win_rate = wins / len(recent_trades) * 100
                avg_profit = sum(trade.get('profit', 0) for trade in recent_trades) / len(recent_trades)
            
            # Estadísticas multi-estrategia
            strategy_stats = self.strategy_manager.get_strategy_statistics()
            
            # Estadísticas multi-pair
            multi_pair_status = self.multi_pair_manager.get_multi_pair_status()
            
            # Estadísticas ML
            ml_stats = self.get_ml_statistics()
            
            return {
                **basic_status,
                'optimization_level': 'MULTI-STRATEGY + MULTI-PAIR + ML ADAPTIVE PREMIUM',
                'current_session': current_session,
                'analysis_interval': self.analysis_interval,
                'min_confidence': self.min_confidence,
                'recent_win_rate': win_rate,
                'recent_avg_profit': avg_profit,
                'risk_metrics': risk_metrics,
                'total_optimized_trades': len(self.trade_history),
                'multi_strategy_active': len(self.strategy_manager.active_strategies),
                'market_condition': strategy_stats.get('market_condition', 'UNKNOWN'),
                'active_strategies': strategy_stats.get('active_strategies', []),
                'multi_pair_active': len(multi_pair_status.get('active_pairs', [])),
                'active_pairs': multi_pair_status.get('active_pairs', []),
                'correlation_risk': await self._calculate_current_correlation_risk(),
                'ml_learning_active': ml_stats.get('ml_system', {}).get('total_trades_learned', 0) > 0,
                'ml_confidence_threshold': ml_stats.get('adaptive_parameters', {}).get('min_confidence', 75),
                'genetic_generation': ml_stats.get('genetic_optimizer', {}).get('total_generations', 0)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado optimizado: {e}")
            return {}
    
    # Métodos heredados del TradingEngine original
    
    async def get_market_analysis(self) -> Dict:
        """Obtener análisis optimizado del mercado"""
        try:
            df = await self.mt5.get_rates(count=300)
            if df.empty:
                return {}
            
            # Análisis avanzado
            df = self.analyzer.calculate_advanced_indicators(df)
            
            # Generar señales premium
            signals = self.analyzer.generate_premium_signals(df)
            
            # Información adicional
            latest = df.iloc[-1]
            current_session = self._get_current_session()
            
            return {
                'current_price': latest['close'],
                'trend': signals['market_regime']['regime'],
                'trend_emoji': "🟢" if signals['market_regime']['trend_direction'] == 1 else "🔴" if signals['market_regime']['trend_direction'] == -1 else "🟡",
                'signal': signals['signal'],
                'signal_emoji': "📈" if signals['signal'] == 'BUY' else "📉" if signals['signal'] == 'SELL' else "⏸️",
                'confidence': signals['confidence'],
                'rsi': latest.get('rsi', 50),
                'rsi_status': "Sobreventa" if latest.get('rsi', 50) < 30 else "Sobrecompra" if latest.get('rsi', 50) > 70 else "Neutral",
                'macd_signal': "Alcista" if latest.get('macd', 0) > latest.get('macd_signal', 0) else "Bajista",
                'bollinger_position': "Sobre banda superior" if latest['close'] > latest.get('bb_upper', latest['close']) else "Bajo banda inferior" if latest['close'] < latest.get('bb_lower', latest['close']) else "Entre bandas",
                'sma20': latest.get('sma_21', latest['close']),
                'sma50': latest.get('sma_50', latest['close']),
                'recommendation': f"{signals['signal']} - Confianza {signals['confidence']:.0f}%",
                'reasons': signals['reasons'],
                'market_regime': signals['market_regime']['regime'],
                'regime_strength': signals['market_regime']['strength'],
                'current_session': current_session,
                'atr': latest.get('atr', 0),
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo análisis optimizado: {e}")
            return {}
    
    async def get_open_positions(self) -> List[Dict]:
        """Obtener posiciones abiertas"""
        try:
            return await self.mt5.get_positions()
        except Exception as e:
            logger.error(f"Error obteniendo posiciones: {e}")
            return []
    
    async def get_settings(self) -> Dict:
        """Obtener configuración optimizada"""
        return {
            'risk_percentage': self.risk_manager.base_risk_percentage,
            'trade_amount': 'DYNAMIC',  # Calculado dinámicamente
            'stop_loss_pips': 'DYNAMIC',  # Basado en ATR
            'take_profit_pips': 'DYNAMIC',  # Basado en régimen de mercado
            'max_daily_loss': self.risk_manager.max_daily_loss,
            'timeframe': '15M',
            'min_confidence': self.min_confidence,
            'auto_trading': self.trading_active,
            'notifications': True,
            'optimization_level': 'PREMIUM',
            'max_positions': self.risk_manager.max_positions,
            'analysis_interval': f"{self.analysis_interval}s (adaptive)",
            'trailing_stops': 'ENABLED',
            'session_awareness': 'ENABLED'
        }
    
    async def get_trade_history(self) -> List[Dict]:
        """Obtener historial optimizado"""
        try:
            # Combinar historial interno con MT5
            mt5_history = await self.mt5.get_history_deals(days=7)
            
            # Enriquecer con datos de optimización
            enriched_history = []
            for deal in mt5_history[-10:]:  # Últimos 10
                # Buscar trade correspondiente en historial interno
                matching_trade = None
                for trade in self.trade_history:
                    if (abs((trade['timestamp'] - deal['time']).total_seconds()) < 60 and
                        trade['signal'].upper() == deal['type'].upper()):
                        matching_trade = trade
                        break
                
                enriched_deal = {
                    **deal,
                    'confidence': matching_trade['confidence'] if matching_trade else 'N/A',
                    'market_regime': matching_trade['market_regime']['regime'] if matching_trade else 'N/A',
                    'session': matching_trade['session'] if matching_trade else 'N/A'
                }
                enriched_history.append(enriched_deal)
            
            return enriched_history
            
        except Exception as e:
            logger.error(f"Error obteniendo historial optimizado: {e}")
            return []
    
    async def close_all_positions(self) -> Dict:
        """Cerrar todas las posiciones"""
        try:
            return await self.mt5.close_all_positions()
        except Exception as e:
            logger.error(f"Error cerrando posiciones: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_status(self) -> Dict:
        """Obtener estado del motor de trading optimizado"""
        logger.info("🔍 [DEBUG] get_status called in OptimizedTradingEngine")
        try:
            logger.info("🔍 [DEBUG] Getting account info...")
            account_info = await self.mt5.get_account_info()
            logger.info(f"🔍 [DEBUG] Account info: {account_info}")
            
            logger.info("🔍 [DEBUG] Getting positions...")
            positions = await self.mt5.get_positions()
            logger.info(f"🔍 [DEBUG] Positions count: {len(positions) if positions else 0}")
            
            return {
                'trading_active': self.trading_active,
                'last_analysis': self.last_analysis_time.strftime('%H:%M:%S') if self.last_analysis_time else 'Nunca',
                'total_trades_today': len([t for t in self.trade_history if t['timestamp'].date() == datetime.now().date()]),
                'account_balance': account_info.get('balance', 0),
                'account_equity': account_info.get('equity', 0),
                'open_positions': len(positions),
                'min_confidence': self.min_confidence,
                'max_daily_trades': self.max_daily_trades,
                'analysis_interval': f"{self.analysis_interval}s",
                'capabilities': ['Multi-Timeframe', 'Machine Learning', 'Risk Management'],
                'performance_metrics': self.performance_metrics,
                'current_session': self._get_current_session()
            }
        except Exception as e:
            logger.error(f"Error obteniendo estado: {e}")
            return {
                'trading_active': self.trading_active,
                'error': str(e),
                'last_analysis': 'Error',
                'total_trades_today': 0,
                'account_balance': 0,
                'account_equity': 0,
                'open_positions': 0
            }
    
    async def get_balance(self) -> Dict:
        """Obtener información de balance de la cuenta"""
        logger.info("🔍 [DEBUG] get_balance called in OptimizedTradingEngine")
        try:
            logger.info("🔍 [DEBUG] Getting account info for balance...")
            account_info = await self.mt5.get_account_info()
            logger.info(f"🔍 [DEBUG] Account info for balance: {account_info}")
            
            if not account_info:
                logger.warning("🔍 [DEBUG] No account info available, returning defaults")
                return {
                    'balance': 0,
                    'equity': 0,
                    'floating_pl': 0,
                    'free_margin': 0,
                    'margin': 0,
                    'margin_level': 0,
                    'risk_per_trade': 2.0,
                    'max_daily_loss': 0
                }
            
            balance = account_info.get('balance', 0)
            equity = account_info.get('equity', 0)
            margin = account_info.get('margin', 0)
            free_margin = account_info.get('free_margin', 0)
            
            result = {
                'balance': balance,
                'equity': equity,
                'floating_pl': equity - balance,
                'free_margin': free_margin,
                'margin': margin,
                'margin_level': (equity / margin * 100) if margin > 0 else 0,
                'risk_per_trade': 2.0,  # 2% por trade
                'max_daily_loss': balance * 0.05  # 5% pérdida máxima diaria
            }
            
            logger.info(f"🔍 [DEBUG] get_balance returning: {result}")
            return result
            
        except Exception as e:
            logger.error(f"🔍 [DEBUG] Error in get_balance: {e}")
            return {
                'balance': 0,
                'equity': 0,
                'floating_pl': 0,
                'free_margin': 0,
                'margin': 0,
                'margin_level': 0,
                'risk_per_trade': 2.0,
                'max_daily_loss': 0
            }

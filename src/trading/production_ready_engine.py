"""
Motor de Trading Listo para Producción
Integra backtesting riguroso, estrategias probadas, gestión de capital avanzada y paper trading
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import asyncio
import json
from pathlib import Path

# Importar componentes profesionales
try:
    # Importaciones relativas (cuando se usa como módulo)
    from .advanced_capital_management import AdvancedCapitalManager
    from .paper_trading_engine import PaperTradingEngine
    from ..backtesting.professional_backtester import ProfessionalBacktester
    from ..strategies.proven_strategies import ProvenForexStrategies
    from .mt5_connector import MT5Connector
    from .risk_manager import AdvancedRiskManager
except ImportError:
    # Importaciones absolutas (cuando se ejecuta directamente)
    from trading.advanced_capital_management import AdvancedCapitalManager
    from trading.paper_trading_engine import PaperTradingEngine
    from backtesting.professional_backtester import ProfessionalBacktester
    from strategies.proven_strategies import ProvenForexStrategies
    from trading.mt5_connector import MT5Connector
    from trading.risk_manager import AdvancedRiskManager

logger = logging.getLogger(__name__)

class ProductionReadyTradingEngine:
    """Motor de trading listo para producción con validación rigurosa"""
    
    def __init__(self, initial_capital: float = 10000, mode: str = 'paper'):
        """
        Inicializar motor de producción
        
        Args:
            initial_capital: Capital inicial
            mode: 'paper', 'backtest', o 'live'
        """
        self.initial_capital = initial_capital
        self.mode = mode
        
        # Componentes principales
        self.capital_manager = AdvancedCapitalManager(initial_capital)
        self.paper_engine = PaperTradingEngine(initial_capital) if mode == 'paper' else None
        self.backtester = ProfessionalBacktester(initial_capital)
        self.strategies = ProvenForexStrategies()
        
        # Configuración de trading
        self.active_strategies = [
            'ema_crossover_filtered',
            'rsi_mean_reversion', 
            'breakout_momentum',
            'london_breakout'
        ]
        
        # Estado del sistema
        self.is_validated = False
        self.validation_results = {}
        self.current_strategy_weights = {}
        
        # Métricas de rendimiento
        self.performance_tracker = {
            'daily_pnl': [],
            'monthly_returns': {},
            'strategy_performance': {},
            'risk_metrics': {}
        }
        
        logger.info(f"🚀 Production Ready Engine inicializado en modo {mode.upper()}")
    
    async def validate_strategies(self, historical_data: pd.DataFrame, 
                                validation_period_months: int = 6) -> Dict:
        """
        Validar estrategias con backtesting riguroso
        
        Args:
            historical_data: Datos históricos para validación
            validation_period_months: Meses de datos para validación out-of-sample
        """
        logger.info("🔍 Iniciando validación rigurosa de estrategias...")
        
        validation_results = {}
        
        try:
            for strategy_name in self.active_strategies:
                logger.info(f"📊 Validando estrategia: {strategy_name}")
                
                # Obtener función de estrategia
                strategy_func = self.strategies.get_strategy(strategy_name)
                if not strategy_func:
                    logger.warning(f"Estrategia {strategy_name} no encontrada")
                    continue
                
                # Crear wrapper para backtesting
                def strategy_wrapper(data: pd.DataFrame, idx: int):
                    return strategy_func(data, idx)
                
                # Ejecutar backtesting
                results = self.backtester.run_backtest(
                    strategy_wrapper,
                    historical_data,
                    out_of_sample_pct=validation_period_months/36  # 6 meses de 3 años = 1/6
                )
                
                # Evaluar resultados
                metrics = results.metrics
                validation = results.period_stats.get('validation', {})
                
                # Criterios de aprobación
                is_approved = (
                    metrics.get('win_rate', 0) >= 50 and
                    metrics.get('profit_factor', 0) >= 1.2 and
                    metrics.get('sharpe_ratio', 0) >= 0.5 and
                    metrics.get('max_drawdown', 100) <= 20 and
                    validation.get('is_valid', False)
                )
                
                validation_results[strategy_name] = {
                    'approved': is_approved,
                    'metrics': metrics,
                    'validation': validation,
                    'recommendation': 'APPROVED' if is_approved else 'REJECTED'
                }
                
                logger.info(f"✅ {strategy_name}: {validation_results[strategy_name]['recommendation']}")
            
            # Calcular pesos de estrategias basados en rendimiento
            self._calculate_strategy_weights(validation_results)
            
            # Determinar si el sistema está validado
            approved_strategies = [name for name, result in validation_results.items() 
                                 if result['approved']]
            
            self.is_validated = len(approved_strategies) >= 2  # Mínimo 2 estrategias aprobadas
            self.validation_results = validation_results
            
            # Generar reporte de validación
            validation_report = self._generate_validation_report(validation_results)
            
            logger.info(f"🎯 Validación completada: {len(approved_strategies)}/{len(self.active_strategies)} estrategias aprobadas")
            
            return {
                'is_validated': self.is_validated,
                'approved_strategies': approved_strategies,
                'validation_results': validation_results,
                'strategy_weights': self.current_strategy_weights,
                'report': validation_report
            }
            
        except Exception as e:
            logger.error(f"Error en validación de estrategias: {e}")
            return {'is_validated': False, 'error': str(e)}
    
    def _calculate_strategy_weights(self, validation_results: Dict):
        """Calcular pesos de estrategias basados en rendimiento"""
        try:
            approved_strategies = {name: result for name, result in validation_results.items() 
                                 if result['approved']}
            
            if not approved_strategies:
                self.current_strategy_weights = {}
                return
            
            # Calcular score compuesto para cada estrategia
            strategy_scores = {}
            for name, result in approved_strategies.items():
                metrics = result['metrics']
                
                # Score basado en múltiples métricas (0-100)
                win_rate_score = min(metrics.get('win_rate', 0), 100)
                profit_factor_score = min(metrics.get('profit_factor', 0) * 25, 100)
                sharpe_score = min(metrics.get('sharpe_ratio', 0) * 50, 100)
                drawdown_score = max(0, 100 - abs(metrics.get('max_drawdown', 0)) * 5)
                
                composite_score = (win_rate_score * 0.3 + 
                                 profit_factor_score * 0.3 + 
                                 sharpe_score * 0.2 + 
                                 drawdown_score * 0.2)
                
                strategy_scores[name] = composite_score
            
            # Normalizar a pesos (suma = 1.0)
            total_score = sum(strategy_scores.values())
            if total_score > 0:
                self.current_strategy_weights = {
                    name: score / total_score 
                    for name, score in strategy_scores.items()
                }
            else:
                # Pesos iguales si no hay scores válidos
                equal_weight = 1.0 / len(approved_strategies)
                self.current_strategy_weights = {
                    name: equal_weight for name in approved_strategies.keys()
                }
            
            logger.info(f"📊 Pesos de estrategias calculados: {self.current_strategy_weights}")
            
        except Exception as e:
            logger.error(f"Error calculando pesos de estrategias: {e}")
            self.current_strategy_weights = {}
    
    async def start_paper_trading(self, live_data_source=None, duration_hours: int = 24) -> Dict:
        """
        Iniciar paper trading para validación en tiempo real
        
        Args:
            live_data_source: Fuente de datos en tiempo real (MT5Connector)
            duration_hours: Duración de la sesión en horas
        """
        if not self.is_validated:
            return {'success': False, 'error': 'Sistema no validado. Ejecutar validate_strategies() primero.'}
        
        if self.mode != 'paper':
            return {'success': False, 'error': 'Motor no está en modo paper trading'}
        
        logger.info(f"📊 Iniciando paper trading por {duration_hours} horas...")
        
        try:
            start_time = datetime.now()
            end_time = start_time + timedelta(hours=duration_hours)
            
            # Cargar sesión previa si existe
            session_file = "data/paper_trading/current_session.json"
            self.paper_engine.load_session(session_file)
            
            while datetime.now() < end_time:
                # Obtener datos actuales
                if live_data_source:
                    current_data = await live_data_source.get_rates(count=200)
                    if current_data.empty:
                        await asyncio.sleep(60)
                        continue
                    
                    current_price = current_data.iloc[-1]['close']
                    current_time = datetime.now()
                    
                    # Actualizar posiciones existentes
                    await self.paper_engine.update_positions(
                        {'EURUSD': current_price}, current_time
                    )
                    
                    # Generar señales de estrategias aprobadas
                    signals = await self._generate_combined_signals(current_data)
                    
                    # Ejecutar señales con gestión de capital
                    for signal in signals:
                        if signal and signal.get('action') in ['buy', 'sell']:
                            # Calcular tamaño de posición
                            position_sizing = self.capital_manager.calculate_position_size(
                                signal.get('confidence', 50),
                                signal.get('stop_loss_pips', 20),
                                signal.get('strategy', 'unknown'),
                                current_price
                            )
                            
                            # Verificar si se permite el trade
                            can_trade, reason = self.capital_manager.should_allow_new_trade(
                                0,  # Exposición actual (simplificado)
                                signal.get('confidence', 50)
                            )
                            
                            if can_trade and position_sizing['size_lots'] > 0:
                                signal['size_lots'] = position_sizing['size_lots']
                                await self.paper_engine.open_position(signal, current_price, current_time)
                    
                    # Guardar progreso cada hora
                    if datetime.now().minute == 0:
                        self.paper_engine.save_session(session_file)
                        performance = self.paper_engine.get_performance_summary()
                        logger.info(f"📈 Paper Trading - Balance: ${performance['current_balance']:,.2f}, "
                                   f"Return: {performance['total_return_pct']:.2f}%, "
                                   f"Trades: {performance['total_trades']}")
                
                # Esperar 1 minuto antes del siguiente ciclo
                await asyncio.sleep(60)
            
            # Sesión completada
            final_performance = self.paper_engine.get_performance_summary()
            self.paper_engine.save_session(session_file)
            
            logger.info("✅ Sesión de paper trading completada")
            return {
                'success': True,
                'duration_hours': duration_hours,
                'performance': final_performance,
                'session_file': session_file
            }
            
        except Exception as e:
            logger.error(f"Error en paper trading: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _generate_combined_signals(self, data: pd.DataFrame) -> List[Dict]:
        """Generar señales combinadas de múltiples estrategias"""
        signals = []
        
        try:
            current_idx = len(data) - 1
            
            for strategy_name, weight in self.current_strategy_weights.items():
                if weight <= 0:
                    continue
                
                strategy_func = self.strategies.get_strategy(strategy_name)
                if not strategy_func:
                    continue
                
                # Generar señal
                signal = strategy_func(data, current_idx)
                
                if signal and signal.get('action') in ['buy', 'sell']:
                    # Ajustar confianza por peso de estrategia
                    original_confidence = signal.get('confidence', 50)
                    weighted_confidence = original_confidence * weight
                    
                    signal['confidence'] = weighted_confidence
                    signal['strategy'] = strategy_name
                    signal['weight'] = weight
                    
                    # Solo incluir señales con confianza suficiente
                    if weighted_confidence >= 60:  # Umbral mínimo
                        signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generando señales combinadas: {e}")
            return []
    
    def _generate_validation_report(self, validation_results: Dict) -> str:
        """Generar reporte de validación"""
        report_lines = []
        
        report_lines.append("=" * 80)
        report_lines.append("📊 REPORTE DE VALIDACIÓN DE ESTRATEGIAS")
        report_lines.append("=" * 80)
        
        approved_count = sum(1 for result in validation_results.values() if result['approved'])
        total_count = len(validation_results)
        
        report_lines.append(f"\n🎯 RESUMEN GENERAL:")
        report_lines.append(f"Estrategias evaluadas: {total_count}")
        report_lines.append(f"Estrategias aprobadas: {approved_count}")
        report_lines.append(f"Tasa de aprobación: {approved_count/total_count*100:.1f}%")
        report_lines.append(f"Sistema validado: {'✅ SÍ' if self.is_validated else '❌ NO'}")
        
        report_lines.append(f"\n📈 RESULTADOS POR ESTRATEGIA:")
        
        for strategy_name, result in validation_results.items():
            status = "✅ APROBADA" if result['approved'] else "❌ RECHAZADA"
            metrics = result['metrics']
            
            report_lines.append(f"\n{strategy_name.upper()}: {status}")
            report_lines.append(f"  Win Rate: {metrics.get('win_rate', 0):.1f}%")
            report_lines.append(f"  Profit Factor: {metrics.get('profit_factor', 0):.2f}")
            report_lines.append(f"  Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
            report_lines.append(f"  Max Drawdown: {metrics.get('max_drawdown', 0):.1f}%")
            report_lines.append(f"  Total Return: {metrics.get('total_return_pct', 0):.1f}%")
            
            if strategy_name in self.current_strategy_weights:
                weight = self.current_strategy_weights[strategy_name] * 100
                report_lines.append(f"  Peso asignado: {weight:.1f}%")
        
        if self.is_validated:
            report_lines.append(f"\n🚀 RECOMENDACIONES:")
            report_lines.append(f"✅ El sistema está listo para paper trading")
            report_lines.append(f"✅ Proceder con validación en tiempo real")
            report_lines.append(f"⚠️ Monitorear rendimiento durante 30-90 días antes de capital real")
        else:
            report_lines.append(f"\n⚠️ ACCIONES REQUERIDAS:")
            report_lines.append(f"❌ Insuficientes estrategias aprobadas")
            report_lines.append(f"🔧 Optimizar parámetros de estrategias rechazadas")
            report_lines.append(f"📊 Obtener más datos históricos para validación")
            report_lines.append(f"🎯 Desarrollar estrategias adicionales")
        
        return "\n".join(report_lines)
    
    def get_system_status(self) -> Dict:
        """Obtener estado completo del sistema"""
        try:
            # Estado básico
            status = {
                'mode': self.mode,
                'is_validated': self.is_validated,
                'initial_capital': self.initial_capital,
                'validation_timestamp': datetime.now().isoformat()
            }
            
            # Estrategias
            status['strategies'] = {
                'total': len(self.active_strategies),
                'approved': len([name for name, result in self.validation_results.items() 
                               if result.get('approved', False)]),
                'weights': self.current_strategy_weights
            }
            
            # Rendimiento del capital
            if hasattr(self.capital_manager, 'get_performance_metrics'):
                status['capital_performance'] = self.capital_manager.get_performance_metrics()
            
            # Paper trading (si aplica)
            if self.paper_engine:
                status['paper_trading'] = self.paper_engine.get_performance_summary()
            
            # Validación
            if self.validation_results:
                status['validation_summary'] = {
                    name: {
                        'approved': result['approved'],
                        'win_rate': result['metrics'].get('win_rate', 0),
                        'profit_factor': result['metrics'].get('profit_factor', 0),
                        'sharpe_ratio': result['metrics'].get('sharpe_ratio', 0)
                    }
                    for name, result in self.validation_results.items()
                }
            
            return status
            
        except Exception as e:
            logger.error(f"Error obteniendo estado del sistema: {e}")
            return {'error': str(e)}
    
    def save_system_state(self, filepath: str = None):
        """Guardar estado completo del sistema"""
        try:
            if not filepath:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filepath = f"data/system_states/production_engine_{timestamp}.json"
            
            # Crear directorio si no existe
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            system_state = {
                'engine_config': {
                    'initial_capital': self.initial_capital,
                    'mode': self.mode,
                    'active_strategies': self.active_strategies
                },
                'validation_results': self.validation_results,
                'strategy_weights': self.current_strategy_weights,
                'is_validated': self.is_validated,
                'system_status': self.get_system_status(),
                'timestamp': datetime.now().isoformat()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(system_state, f, indent=2, default=str)
            
            # Guardar estado de componentes
            if hasattr(self.capital_manager, 'save_state'):
                capital_file = filepath.replace('.json', '_capital.json')
                self.capital_manager.save_state(capital_file)
            
            if self.paper_engine:
                paper_file = filepath.replace('.json', '_paper.json')
                self.paper_engine.save_session(paper_file)
            
            logger.info(f"💾 Estado del sistema guardado en {filepath}")
            
        except Exception as e:
            logger.error(f"Error guardando estado del sistema: {e}")
    
    async def run_production_validation_cycle(self, historical_data: pd.DataFrame,
                                            paper_trading_hours: int = 48) -> Dict:
        """
        Ejecutar ciclo completo de validación para producción
        
        1. Validar estrategias con backtesting
        2. Paper trading si pasa validación
        3. Generar reporte final
        """
        logger.info("🚀 Iniciando ciclo completo de validación para producción")
        
        try:
            # Fase 1: Validación con backtesting
            logger.info("📊 FASE 1: Validación con backtesting riguroso")
            validation_result = await self.validate_strategies(historical_data)
            
            if not validation_result['is_validated']:
                logger.warning("❌ Sistema no pasó validación de backtesting")
                return {
                    'success': False,
                    'phase': 'backtesting',
                    'result': validation_result,
                    'recommendation': 'OPTIMIZE_STRATEGIES'
                }
            
            logger.info("✅ Fase 1 completada - Backtesting aprobado")
            
            # Fase 2: Paper trading
            logger.info("📈 FASE 2: Validación con paper trading")
            paper_result = await self.start_paper_trading(
                duration_hours=paper_trading_hours
            )
            
            if not paper_result.get('success', False):
                logger.warning("❌ Error en paper trading")
                return {
                    'success': False,
                    'phase': 'paper_trading',
                    'result': paper_result,
                    'recommendation': 'FIX_PAPER_TRADING'
                }
            
            # Evaluar resultados de paper trading
            paper_performance = paper_result.get('performance', {})
            paper_approved = (
                paper_performance.get('win_rate', 0) >= 45 and
                paper_performance.get('total_return_pct', -100) > 0 and
                paper_performance.get('max_drawdown_pct', 100) <= 25
            )
            
            logger.info("✅ Fase 2 completada - Paper trading finalizado")
            
            # Fase 3: Evaluación final
            logger.info("🎯 FASE 3: Evaluación final")
            
            final_recommendation = 'APPROVED_FOR_LIVE' if paper_approved else 'NEEDS_MORE_TESTING'
            
            # Generar reporte final
            final_report = self._generate_final_production_report(
                validation_result, paper_result, final_recommendation
            )
            
            # Guardar estado completo
            self.save_system_state()
            
            logger.info(f"🏁 Ciclo de validación completado: {final_recommendation}")
            
            return {
                'success': True,
                'validation_result': validation_result,
                'paper_trading_result': paper_result,
                'final_recommendation': final_recommendation,
                'report': final_report,
                'ready_for_live': paper_approved
            }
            
        except Exception as e:
            logger.error(f"Error en ciclo de validación: {e}")
            return {
                'success': False,
                'error': str(e),
                'recommendation': 'FIX_ERRORS'
            }
    
    def _generate_final_production_report(self, validation_result: Dict, 
                                        paper_result: Dict, 
                                        recommendation: str) -> str:
        """Generar reporte final para producción"""
        report_lines = []
        
        report_lines.append("=" * 100)
        report_lines.append("🚀 REPORTE FINAL DE VALIDACIÓN PARA PRODUCCIÓN")
        report_lines.append("=" * 100)
        
        # Resumen ejecutivo
        report_lines.append(f"\n📋 RESUMEN EJECUTIVO:")
        report_lines.append(f"Recomendación final: {recommendation}")
        report_lines.append(f"Listo para trading en vivo: {'✅ SÍ' if recommendation == 'APPROVED_FOR_LIVE' else '❌ NO'}")
        report_lines.append(f"Fecha de evaluación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Resultados de backtesting
        report_lines.append(f"\n📊 RESULTADOS DE BACKTESTING:")
        approved_strategies = validation_result.get('approved_strategies', [])
        report_lines.append(f"Estrategias aprobadas: {len(approved_strategies)}")
        
        for strategy in approved_strategies:
            if strategy in validation_result['validation_results']:
                metrics = validation_result['validation_results'][strategy]['metrics']
                report_lines.append(f"  {strategy}: WR={metrics.get('win_rate', 0):.1f}%, "
                                   f"PF={metrics.get('profit_factor', 0):.2f}, "
                                   f"Sharpe={metrics.get('sharpe_ratio', 0):.2f}")
        
        # Resultados de paper trading
        if paper_result.get('success'):
            performance = paper_result.get('performance', {})
            report_lines.append(f"\n📈 RESULTADOS DE PAPER TRADING:")
            report_lines.append(f"Duración: {paper_result.get('duration_hours', 0)} horas")
            report_lines.append(f"Total de trades: {performance.get('total_trades', 0)}")
            report_lines.append(f"Win rate: {performance.get('win_rate', 0):.1f}%")
            report_lines.append(f"Retorno total: {performance.get('total_return_pct', 0):.2f}%")
            report_lines.append(f"Máximo drawdown: {performance.get('max_drawdown_pct', 0):.1f}%")
            report_lines.append(f"Profit factor: {performance.get('profit_factor', 0):.2f}")
        
        # Recomendaciones
        report_lines.append(f"\n🎯 RECOMENDACIONES:")
        
        if recommendation == 'APPROVED_FOR_LIVE':
            report_lines.append("✅ SISTEMA APROBADO PARA TRADING EN VIVO")
            report_lines.append("📋 Pasos siguientes:")
            report_lines.append("   1. Comenzar con capital pequeño (1-5% del capital total)")
            report_lines.append("   2. Monitorear rendimiento diariamente por 30 días")
            report_lines.append("   3. Incrementar capital gradualmente si el rendimiento es consistente")
            report_lines.append("   4. Mantener límites de drawdown estrictos (15% máximo)")
            report_lines.append("   5. Revisar y reoptimizar mensualmente")
        else:
            report_lines.append("⚠️ SISTEMA REQUIERE MÁS DESARROLLO")
            report_lines.append("📋 Acciones requeridas:")
            report_lines.append("   1. Extender período de paper trading (30-90 días)")
            report_lines.append("   2. Optimizar estrategias con bajo rendimiento")
            report_lines.append("   3. Mejorar gestión de riesgo")
            report_lines.append("   4. Considerar estrategias adicionales")
            report_lines.append("   5. Repetir ciclo de validación")
        
        return "\n".join(report_lines)

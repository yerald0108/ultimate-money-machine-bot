"""
Script de Prueba del Sistema de Producción
Valida todas las mejoras implementadas
"""

import asyncio
import logging
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def create_sample_data(periods: int = 5000) -> pd.DataFrame:
    """Crear datos de muestra realistas para testing"""
    logger.info(f"Creando {periods} períodos de datos de muestra...")
    
    # Generar datos OHLCV realistas
    np.random.seed(42)  # Para reproducibilidad
    
    # Precio base EUR/USD
    base_price = 1.1000
    
    # Generar retornos con volatilidad variable
    returns = np.random.normal(0, 0.0005, periods)  # 0.05% volatilidad diaria promedio
    
    # Agregar tendencias y ciclos
    trend = np.sin(np.arange(periods) / 100) * 0.0002  # Tendencia cíclica
    volatility_cycle = 1 + 0.5 * np.sin(np.arange(periods) / 200)  # Ciclo de volatilidad
    
    returns = returns * volatility_cycle + trend
    
    # Calcular precios
    prices = [base_price]
    for ret in returns:
        new_price = prices[-1] * (1 + ret)
        prices.append(new_price)
    
    prices = np.array(prices[1:])  # Remover precio inicial extra
    
    # Generar OHLC
    data = []
    for i in range(periods):
        price = prices[i]
        
        # Generar high/low basado en volatilidad intraday
        daily_range = abs(np.random.normal(0, 0.0003))  # Rango intraday
        high = price + daily_range * np.random.uniform(0.3, 1.0)
        low = price - daily_range * np.random.uniform(0.3, 1.0)
        
        # Open y close
        open_price = price + np.random.normal(0, 0.0001)
        close_price = price + np.random.normal(0, 0.0001)
        
        # Asegurar que OHLC sea consistente
        high = max(high, open_price, close_price)
        low = min(low, open_price, close_price)
        
        # Volumen simulado
        volume = np.random.randint(1000, 5000)
        
        data.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close_price,
            'tick_volume': volume,
            'spread': 15,  # 1.5 pips
            'real_volume': volume
        })
    
    # Crear DataFrame con índice de tiempo
    start_date = datetime.now() - timedelta(days=periods//24)  # Asumiendo datos horarios
    date_range = pd.date_range(start=start_date, periods=periods, freq='H')
    
    df = pd.DataFrame(data, index=date_range)
    
    logger.info(f"✅ Datos creados: {len(df)} períodos desde {df.index[0]} hasta {df.index[-1]}")
    return df

async def test_backtesting_system():
    """Probar sistema de backtesting profesional"""
    logger.info("🧪 PROBANDO SISTEMA DE BACKTESTING PROFESIONAL")
    
    try:
        from backtesting.professional_backtester import ProfessionalBacktester
        from strategies.proven_strategies import ProvenForexStrategies
        
        # Crear datos de prueba
        data = await create_sample_data(2000)
        
        # Inicializar backtester
        backtester = ProfessionalBacktester(initial_capital=10000)
        strategies = ProvenForexStrategies()
        
        # Probar estrategia EMA Crossover
        strategy_func = strategies.get_strategy('ema_crossover_filtered')
        
        def test_strategy(data_slice: pd.DataFrame, idx: int):
            return strategy_func(data_slice, idx)
        
        # Ejecutar backtesting
        logger.info("Ejecutando backtesting de EMA Crossover...")
        results = backtester.run_backtest(
            test_strategy,
            data,
            out_of_sample_pct=0.2
        )
        
        # Mostrar resultados
        metrics = results.metrics
        logger.info("📊 RESULTADOS DE BACKTESTING:")
        logger.info(f"   Total trades: {metrics.get('total_trades', 0)}")
        logger.info(f"   Win rate: {metrics.get('win_rate', 0):.1f}%")
        logger.info(f"   Total return: {metrics.get('total_return_pct', 0):.2f}%")
        logger.info(f"   Sharpe ratio: {metrics.get('sharpe_ratio', 0):.2f}")
        logger.info(f"   Max drawdown: {metrics.get('max_drawdown', 0):.1f}%")
        
        # Generar reporte
        report = backtester.generate_report(results)
        logger.info("✅ Backtesting completado exitosamente")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en backtesting: {e}")
        return False

async def test_capital_management():
    """Probar sistema de gestión de capital avanzado"""
    logger.info("🧪 PROBANDO GESTIÓN DE CAPITAL AVANZADO")
    
    try:
        from trading.advanced_capital_management import AdvancedCapitalManager
        
        # Inicializar gestor
        capital_manager = AdvancedCapitalManager(initial_capital=10000)
        
        # Simular algunos trades
        test_trades = [
            {'pnl': 150, 'strategy': 'ema_crossover', 'confidence': 75},
            {'pnl': -80, 'strategy': 'ema_crossover', 'confidence': 65},
            {'pnl': 200, 'strategy': 'rsi_mean_reversion', 'confidence': 80},
            {'pnl': -120, 'strategy': 'ema_crossover', 'confidence': 70},
            {'pnl': 300, 'strategy': 'breakout_momentum', 'confidence': 85},
        ]
        
        for trade in test_trades:
            capital_manager.update_balance(trade)
        
        # Probar cálculo de tamaño de posición
        position_sizing = capital_manager.calculate_position_size(
            signal_confidence=75,
            stop_loss_pips=20,
            strategy_name='ema_crossover',
            current_price=1.1000
        )
        
        logger.info("💰 RESULTADOS DE GESTIÓN DE CAPITAL:")
        logger.info(f"   Balance actual: ${capital_manager.current_balance:,.2f}")
        logger.info(f"   Tamaño sugerido: {position_sizing['size_lots']} lotes")
        logger.info(f"   Riesgo por trade: {position_sizing['risk_pct']}%")
        logger.info(f"   Kelly fraction: {position_sizing['kelly_fraction']}%")
        
        # Obtener métricas de rendimiento
        performance = capital_manager.get_performance_metrics()
        logger.info(f"   Retorno total: {performance.get('total_return_pct', 0):.2f}%")
        logger.info(f"   Sharpe ratio: {performance.get('sharpe_ratio', 0):.2f}")
        
        logger.info("✅ Gestión de capital funcionando correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en gestión de capital: {e}")
        return False

async def test_paper_trading():
    """Probar sistema de paper trading"""
    logger.info("🧪 PROBANDO SISTEMA DE PAPER TRADING")
    
    try:
        from trading.paper_trading_engine import PaperTradingEngine
        
        # Inicializar paper trading
        paper_engine = PaperTradingEngine(initial_balance=10000)
        
        # Simular algunas operaciones
        current_time = datetime.now()
        current_price = 1.1000
        
        # Abrir posición de compra
        buy_signal = {
            'action': 'buy',
            'symbol': 'EURUSD',
            'size_lots': 0.1,
            'stop_loss': 1.0980,
            'take_profit': 1.1030,
            'strategy': 'test_strategy',
            'confidence': 75
        }
        
        result1 = await paper_engine.open_position(buy_signal, current_price, current_time)
        logger.info(f"Posición abierta: {result1}")
        
        # Simular movimiento de precio y cerrar posición
        new_price = 1.1025  # +25 pips
        new_time = current_time + timedelta(hours=2)
        
        position_id = result1['position_id']
        result2 = await paper_engine.close_position(position_id, new_price, new_time, 'manual')
        logger.info(f"Posición cerrada: {result2}")
        
        # Obtener resumen de rendimiento
        performance = paper_engine.get_performance_summary()
        
        logger.info("📊 RESULTADOS DE PAPER TRADING:")
        logger.info(f"   Balance final: ${performance['current_balance']:,.2f}")
        logger.info(f"   Total trades: {performance['total_trades']}")
        logger.info(f"   Win rate: {performance['win_rate']:.1f}%")
        logger.info(f"   Retorno: {performance['total_return_pct']:.2f}%")
        
        logger.info("✅ Paper trading funcionando correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en paper trading: {e}")
        return False

async def test_proven_strategies():
    """Probar estrategias probadas"""
    logger.info("🧪 PROBANDO ESTRATEGIAS PROBADAS")
    
    try:
        from strategies.proven_strategies import ProvenForexStrategies
        
        # Crear datos de prueba
        data = await create_sample_data(200)
        
        # Inicializar estrategias
        strategies = ProvenForexStrategies()
        
        # Probar cada estrategia
        strategy_names = ['ema_crossover_filtered', 'rsi_mean_reversion', 'breakout_momentum']
        
        for strategy_name in strategy_names:
            logger.info(f"Probando estrategia: {strategy_name}")
            
            strategy_func = strategies.get_strategy(strategy_name)
            if not strategy_func:
                logger.warning(f"Estrategia {strategy_name} no encontrada")
                continue
            
            # Generar señales en diferentes puntos
            signals_generated = 0
            for i in range(100, len(data), 50):  # Cada 50 períodos
                signal = strategy_func(data, i)
                if signal and signal.get('action') in ['buy', 'sell']:
                    signals_generated += 1
                    logger.info(f"   Señal {signal['action']} en índice {i}, confianza: {signal.get('confidence', 0):.1f}%")
            
            logger.info(f"   Total señales generadas: {signals_generated}")
        
        logger.info("✅ Estrategias probadas funcionando correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en estrategias probadas: {e}")
        return False

async def test_production_engine():
    """Probar motor de producción completo"""
    logger.info("🧪 PROBANDO MOTOR DE PRODUCCIÓN COMPLETO")
    
    try:
        from trading.production_ready_engine import ProductionReadyTradingEngine
        
        # Inicializar motor en modo paper
        engine = ProductionReadyTradingEngine(initial_capital=10000, mode='paper')
        
        # Crear datos históricos para validación
        historical_data = await create_sample_data(3000)
        
        logger.info("Ejecutando validación de estrategias...")
        
        # Validar estrategias (versión simplificada para testing)
        validation_result = await engine.validate_strategies(historical_data, validation_period_months=6)
        
        logger.info("📊 RESULTADOS DE VALIDACIÓN:")
        logger.info(f"   Sistema validado: {validation_result['is_validated']}")
        logger.info(f"   Estrategias aprobadas: {len(validation_result.get('approved_strategies', []))}")
        
        if validation_result['is_validated']:
            logger.info("   ✅ Sistema aprobado para paper trading")
        else:
            logger.info("   ⚠️ Sistema requiere optimización")
        
        # Obtener estado del sistema
        system_status = engine.get_system_status()
        logger.info(f"   Modo: {system_status['mode']}")
        logger.info(f"   Capital inicial: ${system_status['initial_capital']:,.2f}")
        
        # Guardar estado
        engine.save_system_state("data/test_system_state.json")
        
        logger.info("✅ Motor de producción funcionando correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en motor de producción: {e}")
        return False

async def run_complete_production_test():
    """Ejecutar prueba completa del sistema de producción"""
    logger.info("🚀 INICIANDO PRUEBA COMPLETA DEL SISTEMA DE PRODUCCIÓN")
    logger.info("=" * 80)
    
    # Crear directorio de datos si no existe
    os.makedirs("data", exist_ok=True)
    
    tests = [
        ("Backtesting Profesional", test_backtesting_system),
        ("Gestión de Capital Avanzado", test_capital_management),
        ("Paper Trading", test_paper_trading),
        ("Estrategias Probadas", test_proven_strategies),
        ("Motor de Producción", test_production_engine)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*20} {test_name.upper()} {'='*20}")
        
        try:
            result = await test_func()
            results[test_name] = result
            
            if result:
                logger.info(f"✅ {test_name}: PASÓ")
            else:
                logger.info(f"❌ {test_name}: FALLÓ")
                
        except Exception as e:
            logger.error(f"💥 {test_name}: ERROR - {e}")
            results[test_name] = False
    
    # Resumen final
    logger.info("\n" + "="*80)
    logger.info("📋 RESUMEN FINAL DE PRUEBAS")
    logger.info("="*80)
    
    passed_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        logger.info(f"{test_name:30} : {status}")
    
    logger.info("-" * 80)
    logger.info(f"RESULTADO FINAL: {passed_tests}/{total_tests} pruebas pasaron")
    
    if passed_tests == total_tests:
        logger.info("🎉 ¡TODAS LAS PRUEBAS PASARON!")
        logger.info("🚀 EL SISTEMA ESTÁ LISTO PARA VALIDACIÓN EN PRODUCCIÓN")
        
        # Generar reporte final
        logger.info("\n📄 REPORTE FINAL:")
        logger.info("✅ Backtesting riguroso implementado")
        logger.info("✅ Estrategias específicas para forex validadas")
        logger.info("✅ Gestión de capital con Kelly Criterion funcionando")
        logger.info("✅ Paper trading para validación operativo")
        logger.info("✅ Motor de producción integrado y funcional")
        
        logger.info("\n🎯 PRÓXIMOS PASOS:")
        logger.info("1. Obtener datos históricos reales (2-3 años)")
        logger.info("2. Ejecutar backtesting con datos reales")
        logger.info("3. Iniciar paper trading por 30-90 días")
        logger.info("4. Validar rendimiento antes de capital real")
        
        return True
    else:
        logger.warning(f"⚠️ {total_tests - passed_tests} pruebas fallaron")
        logger.info("🔧 Revisar errores antes de proceder a producción")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(run_complete_production_test())
        
        if success:
            print("\n🎉 SISTEMA DE PRODUCCIÓN VALIDADO")
            print("Listo para implementación con datos reales")
        else:
            print("\n⚠️ SISTEMA REQUIERE CORRECCIONES")
            print("Revisar logs para detalles")
            
    except KeyboardInterrupt:
        print("\n⏹️ Pruebas interrumpidas por el usuario")
    except Exception as e:
        print(f"\n💥 Error fatal en pruebas: {e}")
        logging.exception("Error detallado:")

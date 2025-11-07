"""
Script de Prueba Simple del Bot de Trading
Verifica funcionalidades básicas sin emojis
"""

import asyncio
import logging
import sys
import os

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configurar logging simple
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def test_imports():
    """Probar que todas las importaciones funcionen"""
    try:
        logger.info("Probando importaciones...")
        
        # Importar componentes principales
        from trading.mt5_connector import MT5Connector
        logger.info("OK: MT5Connector importado")
        
        from analysis.advanced_analyzer import AdvancedMarketAnalyzer
        logger.info("OK: AdvancedMarketAnalyzer importado")
        
        from trading.risk_manager import AdvancedRiskManager
        logger.info("OK: AdvancedRiskManager importado")
        
        from trading.optimized_engine import OptimizedTradingEngine
        logger.info("OK: OptimizedTradingEngine importado")
        
        from ml.real_time_ml_system import RealTimeMLSystem
        logger.info("OK: RealTimeMLSystem importado")
        
        from ml.genetic_optimizer import GeneticOptimizer
        logger.info("OK: GeneticOptimizer importado")
        
        from analysis.correlation_analyzer import CorrelationAnalyzer
        logger.info("OK: CorrelationAnalyzer importado")
        
        from trading.multi_pair_manager import MultiPairManager
        logger.info("OK: MultiPairManager importado")
        
        from strategies.strategy_manager import StrategyManager
        logger.info("OK: StrategyManager importado")
        
        return True
        
    except Exception as e:
        logger.error(f"ERROR en importaciones: {e}")
        return False

async def test_initialization():
    """Probar inicialización de componentes"""
    try:
        logger.info("Probando inicialización...")
        
        # Importar componentes
        from trading.mt5_connector import MT5Connector
        from analysis.advanced_analyzer import AdvancedMarketAnalyzer
        from trading.risk_manager import AdvancedRiskManager
        from trading.optimized_engine import OptimizedTradingEngine
        
        # Inicializar componentes básicos
        mt5_connector = MT5Connector()
        logger.info("OK: MT5Connector inicializado")
        
        analyzer = AdvancedMarketAnalyzer()
        logger.info("OK: AdvancedMarketAnalyzer inicializado")
        
        risk_manager = AdvancedRiskManager()
        logger.info("OK: AdvancedRiskManager inicializado")
        
        # Inicializar motor optimizado
        trading_engine = OptimizedTradingEngine(mt5_connector, analyzer, risk_manager)
        logger.info("OK: OptimizedTradingEngine inicializado")
        
        return trading_engine
        
    except Exception as e:
        logger.error(f"ERROR en inicialización: {e}")
        return None

async def test_ml_system(trading_engine):
    """Probar sistema ML"""
    try:
        logger.info("Probando sistema ML...")
        
        # Verificar que el sistema ML esté inicializado
        ml_system = trading_engine.ml_system
        genetic_optimizer = trading_engine.genetic_optimizer
        
        logger.info("OK: Sistema ML inicializado")
        logger.info("OK: Optimizador genético inicializado")
        
        # Probar predicción con datos simulados
        import pandas as pd
        import numpy as np
        
        df_test = pd.DataFrame({
            'close': [1.1000, 1.1010, 1.1005, 1.1015, 1.1020],
            'rsi': [30, 35, 40, 45, 50],
            'macd': [0.0001, 0.0002, 0.0001, 0.0003, 0.0002],
            'bb_position': [0.2, 0.3, 0.4, 0.5, 0.6],
            'ema_alignment': [0.1, 0.2, 0.3, 0.4, 0.5],
            'atr': [0.001, 0.001, 0.001, 0.001, 0.001],
            'adx': [25, 26, 27, 28, 29],
            'momentum': [0.001, 0.002, 0.001, 0.003, 0.002],
            'volume_ratio': [1.0, 1.1, 1.2, 1.3, 1.4]
        })
        
        trade_info = {'confidence': 75}
        ml_signal, ml_confidence, ml_reason = await trading_engine._get_ml_prediction(df_test, trade_info)
        
        logger.info(f"OK: Predicción ML - {ml_signal} (confianza: {ml_confidence:.1f}%)")
        
        return True
        
    except Exception as e:
        logger.error(f"ERROR en sistema ML: {e}")
        return False

async def test_multi_pair():
    """Probar sistema multi-pair"""
    try:
        logger.info("Probando sistema multi-pair...")
        
        from analysis.correlation_analyzer import CorrelationAnalyzer
        from trading.mt5_connector import MT5Connector
        
        mt5_connector = MT5Connector()
        correlation_analyzer = CorrelationAnalyzer(mt5_connector)
        
        # Probar selección de pares
        pairs = await correlation_analyzer.get_optimal_pairs_for_session('london', max_pairs=3)
        logger.info(f"OK: Pares para sesión london: {pairs}")
        
        # Probar correlaciones
        test_pairs = ['EURUSD', 'GBPUSD', 'USDJPY']
        diversification = correlation_analyzer.get_diversification_score(test_pairs)
        logger.info(f"OK: Score de diversificación: {diversification:.2f}")
        
        return True
        
    except Exception as e:
        logger.error(f"ERROR en sistema multi-pair: {e}")
        return False

async def test_strategies():
    """Probar sistema de estrategias"""
    try:
        logger.info("Probando sistema de estrategias...")
        
        from strategies.strategy_manager import StrategyManager
        from trading.mt5_connector import MT5Connector
        from analysis.advanced_analyzer import AdvancedMarketAnalyzer
        from trading.risk_manager import AdvancedRiskManager
        
        mt5_connector = MT5Connector()
        analyzer = AdvancedMarketAnalyzer()
        risk_manager = AdvancedRiskManager()
        
        strategy_manager = StrategyManager(mt5_connector, analyzer, risk_manager)
        
        # Probar detección de condición de mercado
        market_condition = strategy_manager.detect_market_condition({})
        logger.info(f"OK: Condición de mercado: {market_condition}")
        
        # Probar estadísticas
        stats = strategy_manager.get_strategy_statistics()
        logger.info(f"OK: Estadísticas de estrategias obtenidas")
        
        return True
        
    except Exception as e:
        logger.error(f"ERROR en sistema de estrategias: {e}")
        return False

async def run_tests():
    """Ejecutar todas las pruebas"""
    logger.info("=== INICIANDO PRUEBAS DEL BOT ===")
    
    # Test 1: Importaciones
    imports_ok = await test_imports()
    if not imports_ok:
        logger.error("FALLO: No se pudieron importar los módulos")
        return False
    
    # Test 2: Inicialización
    trading_engine = await test_initialization()
    if not trading_engine:
        logger.error("FALLO: No se pudo inicializar el motor")
        return False
    
    # Test 3: Sistema ML
    ml_ok = await test_ml_system(trading_engine)
    
    # Test 4: Sistema Multi-Pair
    multi_pair_ok = await test_multi_pair()
    
    # Test 5: Sistema de Estrategias
    strategies_ok = await test_strategies()
    
    # Resumen
    logger.info("=== RESUMEN DE PRUEBAS ===")
    logger.info(f"Importaciones: {'OK' if imports_ok else 'FALLO'}")
    logger.info(f"Inicialización: {'OK' if trading_engine else 'FALLO'}")
    logger.info(f"Sistema ML: {'OK' if ml_ok else 'FALLO'}")
    logger.info(f"Multi-Pair: {'OK' if multi_pair_ok else 'FALLO'}")
    logger.info(f"Estrategias: {'OK' if strategies_ok else 'FALLO'}")
    
    all_ok = imports_ok and trading_engine and ml_ok and multi_pair_ok and strategies_ok
    
    if all_ok:
        logger.info("RESULTADO: TODAS LAS PRUEBAS PASARON!")
        logger.info("El bot está listo para usar")
        return True
    else:
        logger.warning("RESULTADO: Algunas pruebas fallaron")
        logger.info("Revisar errores antes de usar el bot")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(run_tests())
        
        if success:
            print("\nBOT LISTO PARA USAR")
            print("Para iniciar el bot: python main.py")
        else:
            print("\nREVISAR ERRORES")
            
    except KeyboardInterrupt:
        print("\nPruebas interrumpidas")
    except Exception as e:
        print(f"\nError en pruebas: {e}")

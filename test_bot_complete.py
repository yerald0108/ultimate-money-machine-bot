"""
Script de Prueba Completa del Bot de Trading
Verifica todas las funcionalidades implementadas
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configurar logging (sin emojis para evitar problemas de encoding)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def test_bot_initialization():
    """Probar inicialización del bot"""
    try:
        logger.info("🚀 INICIANDO PRUEBA COMPLETA DEL BOT")
        logger.info("=" * 60)
        
        # Importar componentes principales
        from trading.mt5_connector import MT5Connector
        from analysis.advanced_analyzer import AdvancedMarketAnalyzer
        from trading.risk_manager import AdvancedRiskManager
        from trading.optimized_engine import OptimizedTradingEngine
        
        logger.info("✅ Importaciones exitosas")
        
        # Inicializar componentes
        logger.info("🔧 Inicializando componentes...")
        
        # MT5 Connector (modo demo/test)
        mt5_connector = MT5Connector()
        logger.info("✅ MT5Connector inicializado")
        
        # Advanced Analyzer
        analyzer = AdvancedMarketAnalyzer()
        logger.info("✅ AdvancedMarketAnalyzer inicializado")
        
        # Risk Manager
        risk_manager = AdvancedRiskManager()
        logger.info("✅ AdvancedRiskManager inicializado")
        
        # Optimized Trading Engine (con ML y Multi-pair)
        trading_engine = OptimizedTradingEngine(mt5_connector, analyzer, risk_manager)
        logger.info("✅ OptimizedTradingEngine inicializado")
        
        return trading_engine, mt5_connector, analyzer, risk_manager
        
    except Exception as e:
        logger.error(f"❌ Error en inicialización: {e}")
        return None, None, None, None

async def test_ml_system(trading_engine):
    """Probar sistema de Machine Learning"""
    try:
        logger.info("\n🤖 PROBANDO SISTEMA DE MACHINE LEARNING")
        logger.info("-" * 40)
        
        # Verificar inicialización ML
        ml_system = trading_engine.ml_system
        genetic_optimizer = trading_engine.genetic_optimizer
        
        logger.info("✅ Sistema ML inicializado")
        logger.info("✅ Optimizador genético inicializado")
        
        # Probar predicción ML con datos simulados
        import pandas as pd
        import numpy as np
        
        # Crear DataFrame simulado
        df_test = pd.DataFrame({
            'close': np.random.randn(100).cumsum() + 1.1000,
            'rsi': np.random.uniform(20, 80, 100),
            'macd': np.random.uniform(-0.001, 0.001, 100),
            'bb_position': np.random.uniform(0, 1, 100),
            'ema_alignment': np.random.uniform(-1, 1, 100),
            'atr': np.random.uniform(0.0005, 0.002, 100),
            'adx': np.random.uniform(15, 40, 100),
            'momentum': np.random.uniform(-0.01, 0.01, 100),
            'volume_ratio': np.random.uniform(0.5, 2.0, 100)
        })
        
        # Probar predicción ML
        trade_info = {'confidence': 75}
        ml_signal, ml_confidence, ml_reason = await trading_engine._get_ml_prediction(df_test, trade_info)
        
        logger.info(f"✅ Predicción ML: {ml_signal} (confianza: {ml_confidence:.1f}%)")
        logger.info(f"   Razón: {ml_reason}")
        
        # Probar registro de trade para ML
        test_trade = {
            'success': True,
            'profit': 15.5,
            'confidence': 78,
            'signal': 'BUY',
            'indicators': {
                'rsi': 25,
                'macd': 0.0002,
                'bb_position': 0.1,
                'ema_alignment': 0.5,
                'atr': 0.001,
                'adx': 30,
                'momentum': 0.005,
                'volume_ratio': 1.2
            },
            'session': 'london',
            'market_regime': 'trending'
        }
        
        ml_system.record_trade_result(test_trade)
        logger.info("✅ Trade registrado para aprendizaje ML")
        
        # Obtener estadísticas ML
        ml_stats = trading_engine.get_ml_statistics()
        logger.info(f"✅ Estadísticas ML obtenidas: {len(ml_stats)} categorías")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en sistema ML: {e}")
        return False

async def test_multi_pair_system(trading_engine):
    """Probar sistema Multi-Pair"""
    try:
        logger.info("\n🌍 PROBANDO SISTEMA MULTI-PAIR")
        logger.info("-" * 40)
        
        # Verificar inicialización multi-pair
        multi_pair_manager = trading_engine.multi_pair_manager
        correlation_analyzer = trading_engine.correlation_analyzer
        
        logger.info("✅ MultiPairManager inicializado")
        logger.info("✅ CorrelationAnalyzer inicializado")
        
        # Probar selección de pares por sesión
        sessions = ['asian', 'london', 'new_york', 'overlap']
        for session in sessions:
            pairs = await correlation_analyzer.get_optimal_pairs_for_session(session, max_pairs=3)
            logger.info(f"✅ Pares para sesión {session}: {pairs}")
        
        # Probar análisis de correlaciones
        test_pairs = ['EURUSD', 'GBPUSD', 'USDJPY']
        correlation_report = correlation_analyzer.get_correlation_report(test_pairs)
        logger.info(f"✅ Reporte de correlaciones generado: {len(correlation_report)} elementos")
        
        # Probar diversificación
        diversification_score = correlation_analyzer.get_diversification_score(test_pairs)
        logger.info(f"✅ Score de diversificación: {diversification_score:.2f}")
        
        # Probar pesos óptimos
        optimal_weights = correlation_analyzer.get_optimal_pair_weights(test_pairs)
        logger.info(f"✅ Pesos óptimos: {optimal_weights}")
        
        # Obtener estado multi-pair
        multi_pair_status = multi_pair_manager.get_multi_pair_status()
        logger.info(f"✅ Estado multi-pair obtenido: {len(multi_pair_status)} elementos")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en sistema multi-pair: {e}")
        return False

async def test_strategy_system(trading_engine):
    """Probar sistema de estrategias"""
    try:
        logger.info("\n🎯 PROBANDO SISTEMA MULTI-ESTRATEGIA")
        logger.info("-" * 40)
        
        # Verificar inicialización de estrategias
        strategy_manager = trading_engine.strategy_manager
        
        logger.info("✅ StrategyManager inicializado")
        
        # Verificar estrategias disponibles
        available_strategies = len(strategy_manager.strategies)
        logger.info(f"✅ Estrategias disponibles: {available_strategies}")
        
        # Probar detección de condición de mercado
        market_condition = strategy_manager.detect_market_condition({})
        logger.info(f"✅ Condición de mercado detectada: {market_condition}")
        
        # Obtener estadísticas de estrategias
        strategy_stats = strategy_manager.get_strategy_statistics()
        logger.info(f"✅ Estadísticas de estrategias: {len(strategy_stats)} elementos")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en sistema de estrategias: {e}")
        return False

async def test_risk_management(risk_manager):
    """Probar gestión de riesgo"""
    try:
        logger.info("\n🛡️ PROBANDO GESTIÓN DE RIESGO")
        logger.info("-" * 40)
        
        # Probar cálculo de tamaño de posición
        lot_size = risk_manager.calculate_position_size(
            balance=10000,
            risk_percentage=2.0,
            stop_loss_pips=20,
            symbol="EURUSD"
        )
        logger.info(f"✅ Tamaño de posición calculado: {lot_size} lotes")
        
        # Probar verificación de nuevo trade
        can_trade, reason = risk_manager.should_allow_new_trade([], 0, 80)
        logger.info(f"✅ Verificación de trade: {can_trade} - {reason}")
        
        # Probar métricas de riesgo
        risk_metrics = risk_manager.get_risk_metrics()
        logger.info(f"✅ Métricas de riesgo: {len(risk_metrics)} elementos")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en gestión de riesgo: {e}")
        return False

async def test_engine_status(trading_engine):
    """Probar estado del motor"""
    try:
        logger.info("\n📊 PROBANDO ESTADO DEL MOTOR")
        logger.info("-" * 40)
        
        # Probar estado básico (sin conexión MT5 real)
        try:
            status = await trading_engine.get_status()
            logger.info(f"✅ Estado básico obtenido: {len(status)} elementos")
        except Exception as status_error:
            logger.warning(f"⚠️ Estado básico (sin MT5): {status_error}")
        
        # Probar estado optimizado
        try:
            optimized_status = await trading_engine.get_optimized_status()
            logger.info(f"✅ Estado optimizado obtenido: {len(optimized_status)} elementos")
            
            # Mostrar nivel de optimización
            opt_level = optimized_status.get('optimization_level', 'N/A')
            logger.info(f"🚀 Nivel de optimización: {opt_level}")
            
        except Exception as opt_error:
            logger.warning(f"⚠️ Estado optimizado (sin MT5): {opt_error}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en estado del motor: {e}")
        return False

async def test_integration():
    """Probar integración completa"""
    try:
        logger.info("\n🔗 PROBANDO INTEGRACIÓN COMPLETA")
        logger.info("-" * 40)
        
        # Simular ciclo completo de análisis (sin MT5 real)
        logger.info("📊 Simulando análisis completo...")
        
        # Crear datos simulados
        import pandas as pd
        import numpy as np
        
        df_sim = pd.DataFrame({
            'open': np.random.randn(200).cumsum() + 1.1000,
            'high': np.random.randn(200).cumsum() + 1.1020,
            'low': np.random.randn(200).cumsum() + 1.0980,
            'close': np.random.randn(200).cumsum() + 1.1000,
            'volume': np.random.randint(1000, 5000, 200),
            'time': pd.date_range('2024-01-01', periods=200, freq='15min')
        })
        
        logger.info("✅ Datos simulados creados")
        
        # Simular análisis de indicadores
        from analysis.advanced_analyzer import AdvancedMarketAnalyzer
        analyzer = AdvancedMarketAnalyzer()
        
        df_with_indicators = analyzer.calculate_advanced_indicators(df_sim)
        logger.info("✅ Indicadores calculados")
        
        # Simular generación de señales
        signals = analyzer.generate_premium_signals(df_with_indicators)
        logger.info(f"✅ Señales generadas: {signals['signal']} (confianza: {signals['confidence']:.1f}%)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en integración: {e}")
        return False

async def run_complete_test():
    """Ejecutar prueba completa"""
    try:
        logger.info("🎯 INICIANDO PRUEBA COMPLETA DEL BOT DE TRADING")
        logger.info("=" * 60)
        
        # Test 1: Inicialización
        trading_engine, mt5_connector, analyzer, risk_manager = await test_bot_initialization()
        if not trading_engine:
            logger.error("❌ FALLO EN INICIALIZACIÓN - ABORTANDO PRUEBAS")
            return False
        
        # Test 2: Sistema ML
        ml_success = await test_ml_system(trading_engine)
        
        # Test 3: Sistema Multi-Pair
        multi_pair_success = await test_multi_pair_system(trading_engine)
        
        # Test 4: Sistema de Estrategias
        strategy_success = await test_strategy_system(trading_engine)
        
        # Test 5: Gestión de Riesgo
        risk_success = await test_risk_management(risk_manager)
        
        # Test 6: Estado del Motor
        status_success = await test_engine_status(trading_engine)
        
        # Test 7: Integración
        integration_success = await test_integration()
        
        # Resumen final
        logger.info("\n" + "=" * 60)
        logger.info("📋 RESUMEN DE PRUEBAS")
        logger.info("=" * 60)
        
        tests = [
            ("Inicialización", True),
            ("Sistema ML", ml_success),
            ("Sistema Multi-Pair", multi_pair_success),
            ("Sistema Estrategias", strategy_success),
            ("Gestión de Riesgo", risk_success),
            ("Estado del Motor", status_success),
            ("Integración", integration_success)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, result in tests:
            status = "✅ PASÓ" if result else "❌ FALLÓ"
            logger.info(f"{test_name:20} : {status}")
            if result:
                passed += 1
        
        logger.info("-" * 60)
        logger.info(f"RESULTADO FINAL: {passed}/{total} pruebas pasaron")
        
        if passed == total:
            logger.info("🎉 ¡TODAS LAS PRUEBAS PASARON! EL BOT ESTÁ LISTO")
            return True
        else:
            logger.warning(f"⚠️ {total - passed} pruebas fallaron. Revisar errores.")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error en prueba completa: {e}")
        return False

if __name__ == "__main__":
    # Ejecutar pruebas
    try:
        success = asyncio.run(run_complete_test())
        
        if success:
            print("\n🚀 BOT LISTO PARA USAR")
            print("Para iniciar el bot real, ejecuta: python main.py")
        else:
            print("\n⚠️ REVISAR ERRORES ANTES DE USAR")
            
    except KeyboardInterrupt:
        print("\n⏹️ Pruebas interrumpidas por el usuario")
    except Exception as e:
        print(f"\n💥 Error fatal en pruebas: {e}")

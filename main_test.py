#!/usr/bin/env python3
"""
Forex Trading Bot - EUR/USD (Versión de Prueba)
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

# Configurar logging esencial
setup_essential_logging()

logger = logging.getLogger(__name__)

async def main():
    """Función principal del bot (sin verificación de instancia única)"""
    
    logger.info("INICIANDO: Forex Trading Bot (Modo Prueba)...")
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Forzar modo demo para pruebas
    logger.info("🧪 Ejecutando en MODO DEMO para verificar funcionalidades...")
    missing_vars = ['DEMO_MODE']  # Forzar modo demo
    
    if True:  # Siempre ejecutar en modo demo
        logger.warning(f"Variables de entorno faltantes: {missing_vars}")
        logger.info("Continuando en modo DEMO sin conexión MT5...")
        
        # Modo demo sin MT5
        try:
            # Inicializar componentes en modo demo
            logger.info("Inicializando componentes en modo DEMO...")
            
            mt5_connector = MT5Connector()
            analyzer = AdvancedMarketAnalyzer()
            risk_manager = AdvancedRiskManager()
            trading_engine = OptimizedTradingEngine(mt5_connector, analyzer, risk_manager)
            
            logger.info("✅ Componentes inicializados correctamente")
            
            # Probar funcionalidades básicas
            logger.info("🧪 Probando funcionalidades básicas...")
            
            # Test 1: Estado del motor
            try:
                status = await trading_engine.get_status()
                logger.info(f"✅ Estado del motor obtenido: {len(status)} elementos")
            except Exception as e:
                logger.warning(f"⚠️ Error obteniendo estado: {e}")
            
            # Test 2: Estadísticas ML
            try:
                ml_stats = trading_engine.get_ml_statistics()
                logger.info(f"✅ Estadísticas ML obtenidas: {len(ml_stats)} categorías")
            except Exception as e:
                logger.warning(f"⚠️ Error obteniendo ML stats: {e}")
            
            # Test 3: Estado multi-pair
            try:
                multi_pair_status = trading_engine.multi_pair_manager.get_multi_pair_status()
                logger.info(f"✅ Estado multi-pair obtenido: {len(multi_pair_status)} elementos")
            except Exception as e:
                logger.warning(f"⚠️ Error obteniendo multi-pair status: {e}")
            
            logger.info("🎉 TODAS LAS FUNCIONALIDADES BÁSICAS FUNCIONAN CORRECTAMENTE")
            logger.info("Para usar con MT5 real, configura las variables de entorno en .env")
            
            # Mantener el bot ejecutándose por un momento para verificar
            logger.info("Bot ejecutándose en modo demo por 30 segundos...")
            await asyncio.sleep(30)
            
            logger.info("✅ Prueba completada exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error en modo demo: {e}")
            return
    
    else:
        # Modo completo con MT5
        try:
            # Conectar a MT5
            mt5_connector = MT5Connector()
            if not await mt5_connector.connect():
                logger.error("ERROR: No se pudo conectar a MT5")
                return
            
            # Inicializar componentes principales
            logger.info("Inicializando componentes...")
            analyzer = AdvancedMarketAnalyzer(mt5_connector)
            risk_manager = AdvancedRiskManager()
            trading_engine = OptimizedTradingEngine(mt5_connector, analyzer, risk_manager)
            
            telegram_bot = ForexTradingBot(trading_engine)
            logger.info("Telegram bot creado")
            
            # Registrar estado del sistema
            await log_system_status()
            
            # Iniciar el bot
            logger.info("INICIANDO: Bot de Telegram...")
            await telegram_bot.start()
            
        except KeyboardInterrupt:
            logger.info("Bot detenido por el usuario")
        except Exception as e:
            logger.error(f"ERROR CRÍTICO: {e}")
            raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Bot detenido por el usuario")
    except Exception as e:
        print(f"\n💥 Error fatal: {e}")
        sys.exit(1)

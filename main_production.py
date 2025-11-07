"""
Versión de producción del Ultimate Money Machine Bot
Detecta automáticamente el entorno y usa MT5 real o simulado
"""
import os
import sys
import asyncio
import logging
from datetime import datetime

# Detectar entorno
IS_PRODUCTION = (
    os.getenv('RAILWAY_ENVIRONMENT') or 
    os.getenv('RENDER') or 
    os.getenv('DYNO') or 
    os.getenv('PRODUCTION') == 'true'
)

def setup_logging():
    """Configurar logging según el entorno"""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Reducir logs de librerías externas en producción
    if IS_PRODUCTION:
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('telegram').setLevel(logging.WARNING)
        logging.getLogger('httpx').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    
    if IS_PRODUCTION:
        logger.info("🚀 INICIANDO EN MODO PRODUCCIÓN")
        logger.info("🎭 Usando MT5 Mock Connector (Demo)")
    else:
        logger.info("🏠 INICIANDO EN MODO LOCAL")
        logger.info("🔌 Usando MT5 Real Connector")
    
    return logger

async def create_trading_engine():
    """Crear motor de trading según el entorno"""
    
    if IS_PRODUCTION:
        # Usar MT5 Mock en producción
        from src.trading.mt5_connector_mock import MT5ConnectorMock
        mt5_connector = MT5ConnectorMock()
        
        # Conectar al mock
        await mt5_connector.connect()
        
    else:
        # Usar MT5 real en local
        try:
            from src.trading.mt5_connector import MT5Connector
            mt5_connector = MT5Connector()
            
            # Intentar conectar a MT5 real
            login = os.getenv('MT5_LOGIN')
            password = os.getenv('MT5_PASSWORD')
            server = os.getenv('MT5_SERVER', 'MetaQuotes-Demo')
            
            if login and password:
                success = await mt5_connector.connect(int(login), password, server)
                if not success:
                    raise Exception("No se pudo conectar a MT5")
            else:
                raise Exception("Credenciales MT5 no configuradas")
                
        except Exception as e:
            logging.error(f"❌ Error con MT5 real: {e}")
            logging.info("🎭 Cambiando a MT5 Mock")
            from src.trading.mt5_connector_mock import MT5ConnectorMock
            mt5_connector = MT5ConnectorMock()
            await mt5_connector.connect()
    
    # Crear analizador y gestor de riesgo
    from src.analysis.advanced_analyzer import AdvancedMarketAnalyzer
    from src.trading.risk_manager import AdvancedRiskManager
    
    analyzer = AdvancedMarketAnalyzer()
    risk_manager = AdvancedRiskManager()
    
    # Crear motor de trading optimizado
    from src.trading.optimized_engine import OptimizedTradingEngine
    trading_engine = OptimizedTradingEngine(mt5_connector, analyzer, risk_manager)
    
    return trading_engine

async def main():
    """Función principal"""
    logger = setup_logging()
    
    try:
        # Validar configuración básica
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN no configurado")
        
        logger.info("✅ Configuración validada")
        
        # Crear motor de trading
        logger.info("🔧 Creando motor de trading...")
        trading_engine = await create_trading_engine()
        
        # Crear bot de Telegram
        logger.info("🤖 Iniciando bot de Telegram...")
        from src.bot.telegram_bot import ForexTradingBot
        
        telegram_bot = ForexTradingBot(trading_engine)
        
        # Crear Ultimate Machine
        logger.info("💰 Creando Ultimate Money Machine...")
        from ultimate_machine import UltimateMachine
        
        ultimate_machine = UltimateMachine(trading_engine, telegram_bot)
        
        # Iniciar bot
        logger.info("🚀 Iniciando sistema completo...")
        
        # Crear tareas asíncronas
        tasks = [
            telegram_bot.start(),
            ultimate_machine.run()
        ]
        
        # Ejecutar todo concurrentemente
        await asyncio.gather(*tasks)
        
    except KeyboardInterrupt:
        logger.info("🛑 Deteniendo bot...")
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

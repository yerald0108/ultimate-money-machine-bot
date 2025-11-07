"""
Script de inicio para producción
Maneja la configuración y inicio del bot en entornos de despliegue
"""
import os
import sys
import logging
import asyncio
from datetime import datetime

def setup_production_logging():
    """Configurar logging para producción"""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reducir logs de librerías externas
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"🚀 Iniciando bot en modo PRODUCCIÓN")
    logger.info(f"📊 Log level: {log_level}")
    logger.info(f"🕐 Timestamp: {datetime.now()}")
    
    return logger

def validate_environment():
    """Validar variables de entorno obligatorias"""
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'MT5_LOGIN',
        'MT5_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"❌ Variables de entorno faltantes: {', '.join(missing_vars)}")
    
    return True

async def start_bot_production():
    """Iniciar bot en modo producción"""
    logger = setup_production_logging()
    
    try:
        # Validar configuración
        validate_environment()
        logger.info("✅ Variables de entorno validadas")
        
        # Importar y ejecutar main
        from main import main
        logger.info("🤖 Iniciando Ultimate Money Machine Bot...")
        
        await main()
        
    except Exception as e:
        logger.error(f"❌ Error crítico en producción: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Detectar si estamos en un entorno de despliegue
    if os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RENDER') or os.getenv('DYNO'):
        print("🚀 Detectado entorno de producción")
        asyncio.run(start_bot_production())
    else:
        print("⚠️ Ejecutando en entorno local - usar main.py directamente")
        from main import main
        asyncio.run(main())

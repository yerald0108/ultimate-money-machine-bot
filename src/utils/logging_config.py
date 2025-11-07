"""
Configuración de logging esencial para el bot
Solo muestra información crítica y de estado
"""

import logging

def setup_essential_logging():
    """Configurar logging solo para información esencial"""
    import sys
    
    # Configurar encoding para Windows
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
    
    # Configurar formato simple
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[
            logging.FileHandler('logs/bot.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # Silenciar logs innecesarios
    loggers_to_silence = [
        'httpx',
        'telegram',
        'telegram.ext',
        'telegram._bot',
        'urllib3',
        'asyncio',
        'concurrent.futures'
    ]
    
    for logger_name in loggers_to_silence:
        logging.getLogger(logger_name).setLevel(logging.ERROR)
    
    # Configurar niveles específicos para componentes del bot
    logging.getLogger('src.trading.mt5_connector').setLevel(logging.INFO)
    logging.getLogger('src.trading.optimized_engine').setLevel(logging.INFO)
    logging.getLogger('src.analysis.advanced_analyzer').setLevel(logging.WARNING)
    logging.getLogger('src.ml.adaptive_learning').setLevel(logging.INFO)

def log_bot_activity(message: str, level: str = 'info'):
    """Log actividad esencial del bot"""
    logger = logging.getLogger('BOT_ACTIVITY')
    
    if level == 'info':
        logger.info(message)
    elif level == 'warning':
        logger.warning(message)
    elif level == 'error':
        logger.error(message)
    elif level == 'success':
        logger.info(f"✅ {message}")
    elif level == 'trade':
        logger.info(f"🎯 {message}")
    elif level == 'analysis':
        logger.info(f"📊 {message}")

def log_trade_event(action: str, details: str):
    """Log eventos de trading importantes"""
    logger = logging.getLogger('TRADING')
    logger.info(f"🎯 {action}: {details}")

def log_system_status(component: str, status: str, details: str = ""):
    """Log estado del sistema"""
    logger = logging.getLogger('SYSTEM')
    status_emoji = "OK" if status == "OK" else "ERROR" if status == "ERROR" else "WARNING"
    message = f"{status_emoji} {component}: {details}" if details else f"{status_emoji} {component}"
    logger.info(message)

"""
Configuración para producción del bot de trading
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class ProductionConfig:
    """Configuración para entorno de producción"""
    
    # Telegram Bot Token (OBLIGATORIO)
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # MetaTrader 5 Credentials (OBLIGATORIOS)
    MT5_LOGIN = os.getenv('MT5_LOGIN')
    MT5_PASSWORD = os.getenv('MT5_PASSWORD')
    MT5_SERVER = os.getenv('MT5_SERVER', 'MetaQuotes-Demo')
    
    # Trading Configuration
    TRADING_ENABLED = os.getenv('TRADING_ENABLED', 'true').lower() == 'true'
    MAX_RISK_PERCENTAGE = float(os.getenv('MAX_RISK_PERCENTAGE', '0.05'))
    MAX_SIMULTANEOUS_POSITIONS = int(os.getenv('MAX_SIMULTANEOUS_POSITIONS', '5'))
    MIN_CONFIDENCE = float(os.getenv('MIN_CONFIDENCE', '75'))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Webhook Configuration (para Railway/Heroku)
    WEBHOOK_URL = os.getenv('WEBHOOK_URL')
    PORT = int(os.getenv('PORT', '8080'))
    
    @classmethod
    def validate_config(cls):
        """Validar configuración obligatoria"""
        required_vars = [
            'TELEGRAM_BOT_TOKEN',
            'MT5_LOGIN',
            'MT5_PASSWORD'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Variables de entorno faltantes: {', '.join(missing_vars)}")
        
        return True

# Validar configuración al importar
try:
    ProductionConfig.validate_config()
    print("✅ Configuración de producción validada correctamente")
except ValueError as e:
    print(f"❌ Error en configuración: {e}")

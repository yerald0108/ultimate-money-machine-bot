#!/usr/bin/env python3
"""
Script de configuración inicial para el Forex Trading Bot
"""

import os
import sys
from pathlib import Path

def create_directories():
    """Crear directorios necesarios"""
    directories = ['logs', 'data']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Directorio '{directory}' creado/verificado")

def check_env_file():
    """Verificar archivo .env"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("❌ Archivo .env no encontrado")
        return False
    
    # Verificar variables requeridas
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'MT5_LOGIN',
        'MT5_PASSWORD', 
        'MT5_SERVER'
    ]
    
    with open(env_file, 'r') as f:
        content = f.read()
    
    missing_vars = []
    for var in required_vars:
        if f"{var}=YOUR_" in content or f"{var}=" not in content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variables de entorno faltantes: {', '.join(missing_vars)}")
        print("📝 Por favor, edita el archivo .env con tus credenciales reales")
        return False
    
    print("✅ Archivo .env configurado correctamente")
    return True

def check_mt5_installation():
    """Verificar instalación de MT5"""
    try:
        import MetaTrader5 as mt5
        print("✅ MetaTrader5 library instalada")
        return True
    except ImportError:
        print("❌ MetaTrader5 library no instalada")
        print("📦 Ejecuta: pip install MetaTrader5")
        return False

def check_telegram_bot():
    """Verificar configuración del bot de Telegram"""
    try:
        from telegram.ext import Application
        print("✅ python-telegram-bot instalado")
        return True
    except ImportError:
        print("❌ python-telegram-bot no instalado")
        print("📦 Ejecuta: pip install python-telegram-bot")
        return False

def main():
    """Función principal de configuración"""
    print("🤖 Configuración inicial del Forex Trading Bot")
    print("=" * 50)
    
    # Crear directorios
    create_directories()
    print()
    
    # Verificar dependencias
    print("📦 Verificando dependencias...")
    mt5_ok = check_mt5_installation()
    telegram_ok = check_telegram_bot()
    print()
    
    # Verificar configuración
    print("⚙️ Verificando configuración...")
    env_ok = check_env_file()
    print()
    
    # Resumen
    print("📋 Resumen de configuración:")
    print(f"   Directorios: ✅")
    print(f"   MT5 Library: {'✅' if mt5_ok else '❌'}")
    print(f"   Telegram Bot: {'✅' if telegram_ok else '❌'}")
    print(f"   Configuración .env: {'✅' if env_ok else '❌'}")
    print()
    
    if all([mt5_ok, telegram_ok, env_ok]):
        print("🎉 ¡Configuración completa! Puedes ejecutar el bot con:")
        print("   python main.py")
    else:
        print("⚠️ Configuración incompleta. Revisa los elementos marcados con ❌")
        print()
        print("📖 Pasos siguientes:")
        if not mt5_ok:
            print("   1. Instala MetaTrader5: pip install MetaTrader5")
        if not telegram_ok:
            print("   2. Instala telegram bot: pip install python-telegram-bot")
        if not env_ok:
            print("   3. Configura el archivo .env con tus credenciales")
        print("   4. Ejecuta nuevamente: python setup.py")

if __name__ == "__main__":
    main()

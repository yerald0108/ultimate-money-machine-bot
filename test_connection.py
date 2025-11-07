#!/usr/bin/env python3
"""
Script de prueba para verificar conexiones
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

async def test_mt5_connection():
    """Probar conexión a MT5"""
    print("🔄 Probando conexión a MT5...")
    
    try:
        from src.trading.mt5_connector import MT5Connector
        
        mt5 = MT5Connector()
        connected = await mt5.connect()
        
        if connected:
            print("✅ Conexión a MT5 exitosa")
            
            # Probar obtener información de cuenta
            account_info = await mt5.get_account_info()
            if account_info:
                print(f"   📊 Balance: ${account_info['balance']:.2f}")
                print(f"   🏦 Servidor: {account_info['server']}")
                print(f"   👤 Cuenta: {account_info['name']}")
            
            # Probar obtener datos del mercado
            symbol_info = await mt5.get_symbol_info()
            if symbol_info:
                print(f"   💱 EUR/USD: {symbol_info['bid']:.5f} / {symbol_info['ask']:.5f}")
                print(f"   📊 Spread: {symbol_info['spread']:.5f}")
            
            await mt5.disconnect()
            return True
        else:
            print("❌ Error conectando a MT5")
            return False
            
    except Exception as e:
        print(f"❌ Error en conexión MT5: {e}")
        return False

async def test_telegram_bot():
    """Probar configuración del bot de Telegram"""
    print("🔄 Probando configuración de Telegram...")
    
    try:
        from telegram.ext import Application
        
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token or token.startswith('YOUR_'):
            print("❌ Token de Telegram no configurado")
            return False
        
        # Crear aplicación de prueba
        app = Application.builder().token(token).build()
        
        # Probar obtener información del bot
        await app.initialize()
        bot_info = await app.bot.get_me()
        
        print(f"✅ Bot de Telegram configurado: @{bot_info.username}")
        print(f"   🤖 Nombre: {bot_info.first_name}")
        print(f"   🆔 ID: {bot_info.id}")
        
        await app.shutdown()
        return True
        
    except Exception as e:
        print(f"❌ Error en configuración de Telegram: {e}")
        return False

async def test_market_analysis():
    """Probar análisis de mercado"""
    print("🔄 Probando análisis de mercado...")
    
    try:
        from src.analysis.market_analyzer import MarketAnalyzer
        import pandas as pd
        import numpy as np
        
        analyzer = MarketAnalyzer()
        
        # Crear datos de prueba
        dates = pd.date_range(start='2024-01-01', periods=100, freq='15T')
        test_data = pd.DataFrame({
            'open': np.random.uniform(1.0800, 1.0900, 100),
            'high': np.random.uniform(1.0810, 1.0910, 100),
            'low': np.random.uniform(1.0790, 1.0890, 100),
            'close': np.random.uniform(1.0800, 1.0900, 100),
            'tick_volume': np.random.randint(100, 1000, 100)
        }, index=dates)
        
        # Probar cálculo de indicadores
        df_with_indicators = analyzer.calculate_technical_indicators(test_data)
        
        if not df_with_indicators.empty and 'rsi' in df_with_indicators.columns:
            print("✅ Análisis técnico funcionando")
            print(f"   📊 Indicadores calculados: RSI, MACD, Bollinger Bands")
            
            # Probar generación de señales
            signals = analyzer.generate_signals(df_with_indicators)
            print(f"   🎯 Señal generada: {signals['signal']}")
            print(f"   📈 Confianza: {signals['confidence']}%")
            
            return True
        else:
            print("❌ Error calculando indicadores técnicos")
            return False
            
    except Exception as e:
        print(f"❌ Error en análisis de mercado: {e}")
        return False

async def main():
    """Función principal de pruebas"""
    print("🧪 PRUEBAS DEL FOREX TRADING BOT")
    print("=" * 40)
    print()
    
    # Verificar variables de entorno
    required_vars = ['TELEGRAM_BOT_TOKEN', 'MT5_LOGIN', 'MT5_PASSWORD', 'MT5_SERVER']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith('YOUR_'):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Variables de entorno faltantes:")
        for var in missing_vars:
            print(f"   - {var}")
        print()
        print("📝 Configura el archivo .env antes de continuar")
        return
    
    # Ejecutar pruebas
    tests = [
        ("Análisis de Mercado", test_market_analysis),
        ("Telegram Bot", test_telegram_bot),
        ("Conexión MT5", test_mt5_connection),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"🧪 {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error en prueba {test_name}: {e}")
            results.append((test_name, False))
        print()
    
    # Resumen de resultados
    print("📋 RESUMEN DE PRUEBAS")
    print("-" * 30)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if not result:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 ¡Todas las pruebas pasaron! El bot está listo para usar.")
        print("🚀 Ejecuta: python main.py")
    else:
        print("⚠️ Algunas pruebas fallaron. Revisa la configuración.")

if __name__ == "__main__":
    asyncio.run(main())

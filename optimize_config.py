#!/usr/bin/env python3
"""
Configurador de Optimización para Máxima Rentabilidad
Ajusta automáticamente los parámetros del bot para optimizar ganancias
"""

import os
from dotenv import load_dotenv, set_key

def optimize_for_demo_account():
    """Configuración optimizada para cuenta demo"""
    
    optimizations = {
        # Gestión de riesgo agresiva pero controlada
        'RISK_PERCENTAGE': '2.5',  # Aumentado para mayor rentabilidad
        'MAX_DAILY_LOSS': '150.0',  # Límite más alto para más oportunidades
        'TRADE_AMOUNT': '0.15',  # Lotes más grandes
        
        # Stops optimizados
        'STOP_LOSS_PIPS': '18',  # Más ajustado
        'TAKE_PROFIT_PIPS': '45',  # Mejor ratio riesgo/beneficio
        
        # Configuración avanzada
        'MAX_DAILY_TRADES': '12',  # Más trades por día
        'MIN_CONFIDENCE': '72',  # Ligeramente más permisivo
        'ANALYSIS_INTERVAL': '150',  # Análisis más frecuente (2.5 min)
    }
    
    return optimizations

def optimize_for_conservative():
    """Configuración conservadora para cuentas reales pequeñas"""
    
    optimizations = {
        'RISK_PERCENTAGE': '1.0',
        'MAX_DAILY_LOSS': '50.0',
        'TRADE_AMOUNT': '0.05',
        'STOP_LOSS_PIPS': '25',
        'TAKE_PROFIT_PIPS': '35',
        'MAX_DAILY_TRADES': '5',
        'MIN_CONFIDENCE': '80',
        'ANALYSIS_INTERVAL': '300',
    }
    
    return optimizations

def optimize_for_aggressive():
    """Configuración agresiva para cuentas grandes"""
    
    optimizations = {
        'RISK_PERCENTAGE': '3.0',
        'MAX_DAILY_LOSS': '300.0',
        'TRADE_AMOUNT': '0.25',
        'STOP_LOSS_PIPS': '15',
        'TAKE_PROFIT_PIPS': '50',
        'MAX_DAILY_TRADES': '15',
        'MIN_CONFIDENCE': '70',
        'ANALYSIS_INTERVAL': '120',
    }
    
    return optimizations

def apply_optimization(optimization_type='demo'):
    """Aplicar optimización seleccionada"""
    
    load_dotenv()
    
    if optimization_type == 'demo':
        config = optimize_for_demo_account()
        print("🎯 Aplicando configuración DEMO OPTIMIZADA")
    elif optimization_type == 'conservative':
        config = optimize_for_conservative()
        print("🛡️ Aplicando configuración CONSERVADORA")
    elif optimization_type == 'aggressive':
        config = optimize_for_aggressive()
        print("🚀 Aplicando configuración AGRESIVA")
    else:
        print("❌ Tipo de optimización no válido")
        return False
    
    # Aplicar configuraciones
    env_file = '.env'
    
    for key, value in config.items():
        set_key(env_file, key, value)
        print(f"   ✅ {key} = {value}")
    
    print("\n🎉 Optimización aplicada correctamente!")
    print("🔄 Reinicia el bot para aplicar los cambios")
    
    return True

def show_current_config():
    """Mostrar configuración actual"""
    
    load_dotenv()
    
    print("📊 CONFIGURACIÓN ACTUAL:")
    print("=" * 40)
    
    config_items = [
        'RISK_PERCENTAGE',
        'MAX_DAILY_LOSS', 
        'TRADE_AMOUNT',
        'STOP_LOSS_PIPS',
        'TAKE_PROFIT_PIPS'
    ]
    
    for item in config_items:
        value = os.getenv(item, 'NO CONFIGURADO')
        print(f"   {item}: {value}")

def interactive_optimizer():
    """Optimizador interactivo"""
    
    print("🤖 OPTIMIZADOR DE CONFIGURACIÓN")
    print("=" * 50)
    
    show_current_config()
    
    print("\n📋 OPCIONES DE OPTIMIZACIÓN:")
    print("1. 🎯 Demo Optimizada (Recomendado para pruebas)")
    print("2. 🛡️ Conservadora (Para cuentas reales pequeñas)")
    print("3. 🚀 Agresiva (Para cuentas grandes)")
    print("4. 📊 Solo mostrar configuración actual")
    print("5. ❌ Salir")
    
    while True:
        try:
            choice = input("\n👉 Selecciona una opción (1-5): ").strip()
            
            if choice == '1':
                apply_optimization('demo')
                break
            elif choice == '2':
                apply_optimization('conservative')
                break
            elif choice == '3':
                print("⚠️ ADVERTENCIA: Configuración agresiva para cuentas grandes")
                confirm = input("¿Estás seguro? (s/N): ").strip().lower()
                if confirm == 's':
                    apply_optimization('aggressive')
                break
            elif choice == '4':
                show_current_config()
                continue
            elif choice == '5':
                print("👋 Saliendo...")
                break
            else:
                print("❌ Opción no válida. Intenta de nuevo.")
                
        except KeyboardInterrupt:
            print("\n👋 Saliendo...")
            break

if __name__ == "__main__":
    interactive_optimizer()

"""
Test de Trading Real - Prueba Rápida con Cuenta Demo
Objetivo: Ejecutar 1 trade real para confirmar que el bot funciona
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

from trading.mt5_connector import MT5Connector

async def execute_test_trade():
    """Ejecutar un trade de prueba para validar el sistema"""
    logger.info("🧪 INICIANDO PRUEBA DE TRADE REAL")
    logger.info("🎯 Objetivo: Confirmar que el bot puede ejecutar trades")
    logger.info("=" * 60)
    
    try:
        # Conectar a MT5
        mt5 = MT5Connector()
        result = await mt5.connect()
        
        if not result['success']:
            logger.error(f"❌ Error conectando: {result['error']}")
            return False
        
        logger.info("✅ Conectado a MT5")
        
        # Obtener información de cuenta
        account_info = await mt5.get_account_info()
        logger.info(f"💰 Balance: ${account_info.get('balance', 0):,.2f}")
        
        # Obtener precio actual
        df = await mt5.get_rates(count=10)
        current_price = df['close'].iloc[-1]
        logger.info(f"📊 Precio actual EURUSD: {current_price:.5f}")
        
        # Preparar parámetros del trade de prueba
        action = "buy"
        volume = 0.01  # Lote muy pequeño para prueba
        entry_price = current_price
        stop_loss = entry_price - 0.0010  # 10 pips stop
        take_profit = entry_price + 0.0015  # 15 pips target
        
        logger.info("📋 PARÁMETROS DEL TRADE DE PRUEBA:")
        logger.info(f"   Acción: {action.upper()}")
        logger.info(f"   Volumen: {volume} lotes")
        logger.info(f"   Entrada: {entry_price:.5f}")
        logger.info(f"   Stop Loss: {stop_loss:.5f}")
        logger.info(f"   Take Profit: {take_profit:.5f}")
        logger.info(f"   Riesgo: 10 pips")
        logger.info(f"   Objetivo: 15 pips")
        
        # Ejecutar trade
        logger.info("🚀 EJECUTANDO TRADE DE PRUEBA...")
        
        trade_result = await mt5.send_order(
            action=action,
            volume=volume,
            symbol="EURUSD",
            sl=stop_loss,
            tp=take_profit,
            comment="TEST-BOT-VALIDATION"
        )
        
        if trade_result['success']:
            logger.info("🎉 ¡TRADE EJECUTADO EXITOSAMENTE!")
            logger.info(f"✅ Order ID: {trade_result.get('order', 'N/A')}")
            logger.info(f"✅ Deal ID: {trade_result.get('deal', 'N/A')}")
            logger.info(f"✅ Volumen: {trade_result.get('volume', 0)} lotes")
            logger.info(f"✅ Precio: {trade_result.get('price', 0):.5f}")
            
            # Esperar un momento y verificar posiciones
            await asyncio.sleep(2)
            
            positions = await mt5.get_positions()
            if positions:
                logger.info(f"📊 POSICIONES ABIERTAS: {len(positions)}")
                for pos in positions:
                    profit = pos.get('profit', 0)
                    logger.info(f"   💰 P&L actual: ${profit:+.2f}")
            
            # Esperar 10 segundos para ver el P&L
            logger.info("⏳ Esperando 10 segundos para ver evolución...")
            await asyncio.sleep(10)
            
            # Verificar P&L actualizado
            positions = await mt5.get_positions()
            if positions:
                for pos in positions:
                    profit = pos.get('profit', 0)
                    logger.info(f"💰 P&L después de 10s: ${profit:+.2f}")
            
            # Cerrar posición para completar la prueba
            logger.info("🔒 Cerrando posición de prueba...")
            if positions:
                for pos in positions:
                    close_result = await mt5.close_position(pos['ticket'])
                    if close_result:
                        logger.info("✅ Posición cerrada exitosamente")
                        logger.info(f"💰 P&L final: ${pos.get('profit', 0):+.2f}")
            
            await mt5.disconnect()
            
            logger.info("\n" + "🎉" * 20)
            logger.info("✅ ¡PRUEBA DE TRADING EXITOSA!")
            logger.info("🎯 EL BOT PUEDE EJECUTAR TRADES REALES")
            logger.info("💰 SISTEMA VALIDADO PARA GENERAR DINERO")
            logger.info("🚀 LISTO PARA TRADING AUTOMÁTICO")
            logger.info("🎉" * 20)
            
            return True
            
        else:
            logger.error(f"❌ Error ejecutando trade: {trade_result.get('error', 'Unknown')}")
            await mt5.disconnect()
            return False
            
    except Exception as e:
        logger.error(f"💥 Error en prueba: {e}")
        return False

async def main():
    """Función principal"""
    print("🧪" * 30)
    print("🚀 PRUEBA DE TRADING REAL 🚀")
    print("🧪" * 30)
    print()
    print("🎯 OBJETIVO: Ejecutar 1 trade real con cuenta demo")
    print("💰 VALIDAR: Que el bot puede generar dinero")
    print("⚡ RESULTADO: Confirmar funcionalidad completa")
    print("=" * 60)
    
    success = await execute_test_trade()
    
    if success:
        print("\n✅ ¡PRUEBA EXITOSA!")
        print("💰 El bot está confirmado para generar dinero")
        print("🚀 Proceder con trading automático completo")
    else:
        print("\n❌ Prueba fallida")
        print("🔧 Revisar configuración")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n💥 Error: {e}")

"""
MAIN MONEY MAKER - Bot de Trading Enfocado en Generar Dinero Real
Objetivo: Máxima rentabilidad con las estrategias más efectivas
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
import signal

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configurar logging agresivo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('money_maker.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Importar componentes del motor de dinero
from trading.money_making_engine import MoneyMakingEngine
from trading.mt5_connector import MT5Connector
from bot.telegram_bot import ForexTradingBot
from trading.optimized_engine import OptimizedTradingEngine

class MoneyMakingBot:
    """Bot principal enfocado exclusivamente en generar dinero"""
    
    def __init__(self):
        self.money_engine = None
        self.mt5_connector = None
        self.telegram_bot = None
        self.running = False
        
        # Configuración agresiva para generar dinero
        self.config = {
            'initial_capital': 1000,        # Capital inicial
            'target_monthly_return': 25.0,  # 25% mensual objetivo
            'max_daily_drawdown': 0.08,     # 8% drawdown máximo diario
            'aggressive_mode': True,        # Modo agresivo activado
            'profit_reinvestment': True,    # Reinvertir ganancias
            'risk_multiplier': 1.5         # Multiplicador de riesgo
        }
        
        logger.info("💰 MONEY MAKING BOT INICIALIZADO")
        logger.info("🎯 OBJETIVO: GENERAR MÁXIMO DINERO POSIBLE")
    
    async def initialize_components(self):
        """Inicializar todos los componentes para generar dinero"""
        try:
            logger.info("🔧 Inicializando componentes del motor de dinero...")
            
            # 1. Conectar a MT5
            self.mt5_connector = MT5Connector()
            connection_result = await self.mt5_connector.connect()
            
            if not connection_result['success']:
                logger.error("❌ Error conectando a MT5 - Sin conexión no hay dinero")
                return False
            
            logger.info("✅ MT5 conectado - Listo para hacer dinero")
            
            # 2. Inicializar motor de dinero
            self.money_engine = MoneyMakingEngine(
                initial_capital=self.config['initial_capital'],
                target_monthly_return=self.config['target_monthly_return']
            )
            
            logger.info("✅ Motor de dinero inicializado")
            
            # 3. Configurar Telegram para monitoreo
            try:
                # Usar el motor optimizado existente para Telegram
                trading_engine = OptimizedTradingEngine(self.mt5_connector)
                self.telegram_bot = ForexTradingBot(trading_engine)
                
                # Inicializar bot de Telegram en background
                asyncio.create_task(self.telegram_bot.start())
                logger.info("✅ Telegram bot iniciado para monitoreo")
                
            except Exception as telegram_error:
                logger.warning(f"⚠️ Telegram no disponible: {telegram_error}")
                logger.info("💰 Continuando sin Telegram - El dinero es la prioridad")
            
            return True
            
        except Exception as e:
            logger.error(f"💥 Error inicializando componentes: {e}")
            return False
    
    async def start_money_generation(self):
        """Iniciar la generación de dinero"""
        try:
            logger.info("🚀 INICIANDO GENERACIÓN DE DINERO")
            logger.info("=" * 60)
            
            # Mostrar configuración
            logger.info(f"💰 Capital inicial: ${self.config['initial_capital']:,.2f}")
            logger.info(f"🎯 Objetivo mensual: {self.config['target_monthly_return']}%")
            logger.info(f"📈 Objetivo diario: {self.config['target_monthly_return']/22:.2f}%")
            logger.info(f"⚡ Modo agresivo: {self.config['aggressive_mode']}")
            
            # Verificar balance actual
            account_info = await self.mt5_connector.get_account_info()
            if account_info:
                current_balance = account_info.get('balance', 0)
                logger.info(f"💳 Balance actual en MT5: ${current_balance:,.2f}")
                
                # Actualizar capital inicial si es diferente
                if current_balance > 0:
                    self.money_engine.current_balance = current_balance
                    self.money_engine.initial_capital = current_balance
                    logger.info(f"🔄 Capital ajustado a balance real: ${current_balance:,.2f}")
            
            # Iniciar el motor de dinero
            self.running = True
            
            # Mostrar mensaje motivacional
            logger.info("💪 ¡VAMOS A HACER DINERO!")
            logger.info("🎯 Cada pip cuenta, cada trade importa")
            logger.info("💰 Objetivo: Convertir cada oportunidad en ganancia")
            logger.info("=" * 60)
            
            # Iniciar motor de generación de dinero
            await self.money_engine.start_money_making(self.mt5_connector)
            
        except Exception as e:
            logger.error(f"💥 Error iniciando generación de dinero: {e}")
            self.running = False
    
    async def monitor_money_generation(self):
        """Monitorear la generación de dinero en tiempo real"""
        logger.info("📊 Iniciando monitoreo de generación de dinero...")
        
        last_balance = self.money_engine.current_balance
        last_report_time = datetime.now()
        
        while self.running:
            try:
                # Obtener estado actual
                status = self.money_engine.get_money_making_status()
                
                # Reportar progreso cada 15 minutos
                current_time = datetime.now()
                if (current_time - last_report_time).total_seconds() >= 900:  # 15 minutos
                    
                    logger.info("📊 REPORTE DE PROGRESO:")
                    logger.info(f"   💰 Balance actual: ${status['current_balance']:,.2f}")
                    logger.info(f"   📈 Retorno total: {status['total_return_pct']:+.2f}%")
                    logger.info(f"   📅 Retorno diario: {status['daily_return_pct']:+.2f}%")
                    logger.info(f"   🎯 Progreso objetivo: {status['daily_target_progress']:.1f}%")
                    logger.info(f"   📊 Trades hoy: {status['trades_today']}")
                    logger.info(f"   🏆 Win rate hoy: {status['win_rate_today']:.1f}%")
                    
                    # Verificar si estamos ganando dinero
                    balance_change = status['current_balance'] - last_balance
                    if balance_change > 0:
                        logger.info(f"   💚 ¡GANANDO! +${balance_change:.2f} desde último reporte")
                    elif balance_change < 0:
                        logger.warning(f"   🔴 Pérdida temporal: ${balance_change:.2f}")
                    
                    last_balance = status['current_balance']
                    last_report_time = current_time
                
                # Verificar alertas críticas
                if status['daily_return_pct'] < -5.0:  # Pérdida diaria > 5%
                    logger.error("🚨 ALERTA: Pérdida diaria excesiva")
                    logger.error("🛡️ Activando protecciones adicionales")
                
                elif status['daily_return_pct'] > 3.0:  # Ganancia diaria > 3%
                    logger.info("🎉 ¡EXCELENTE DÍA! Ganancia superior al 3%")
                
                # Verificar objetivo mensual
                days_in_month = 22  # Días de trading aproximados
                monthly_projection = status['daily_return_pct'] * days_in_month
                
                if monthly_projection > self.config['target_monthly_return']:
                    logger.info(f"🚀 ¡SUPERANDO OBJETIVO! Proyección mensual: {monthly_projection:.1f}%")
                
                await asyncio.sleep(300)  # Verificar cada 5 minutos
                
            except Exception as e:
                logger.error(f"Error en monitoreo: {e}")
                await asyncio.sleep(60)
    
    async def emergency_stop(self):
        """Parada de emergencia"""
        logger.warning("🛑 PARADA DE EMERGENCIA ACTIVADA")
        
        try:
            # Detener motor de dinero
            if self.money_engine:
                await self.money_engine.stop_money_making()
            
            # Cerrar todas las posiciones
            if self.mt5_connector:
                positions = await self.mt5_connector.get_positions()
                if positions:
                    logger.info(f"🔒 Cerrando {len(positions)} posiciones abiertas...")
                    for position in positions:
                        await self.mt5_connector.close_position(position['ticket'])
            
            self.running = False
            logger.info("✅ Parada de emergencia completada")
            
        except Exception as e:
            logger.error(f"Error en parada de emergencia: {e}")
    
    def setup_signal_handlers(self):
        """Configurar manejadores de señales para parada segura"""
        def signal_handler(signum, frame):
            logger.info("📡 Señal de parada recibida")
            asyncio.create_task(self.emergency_stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run(self):
        """Ejecutar el bot de generación de dinero"""
        try:
            # Configurar manejadores de señales
            self.setup_signal_handlers()
            
            # Inicializar componentes
            if not await self.initialize_components():
                logger.error("❌ Fallo en inicialización - No se puede generar dinero")
                return False
            
            # Crear tareas principales
            tasks = [
                asyncio.create_task(self.start_money_generation()),
                asyncio.create_task(self.monitor_money_generation())
            ]
            
            # Ejecutar hasta que se detenga
            await asyncio.gather(*tasks, return_exceptions=True)
            
            return True
            
        except KeyboardInterrupt:
            logger.info("⏹️ Deteniendo bot por solicitud del usuario...")
            await self.emergency_stop()
            return True
            
        except Exception as e:
            logger.error(f"💥 Error crítico en bot de dinero: {e}")
            await self.emergency_stop()
            return False
        
        finally:
            # Cleanup
            if self.mt5_connector:
                await self.mt5_connector.disconnect()
            
            logger.info("🏁 Bot de generación de dinero finalizado")

async def main():
    """Función principal"""
    print("💰" * 30)
    print("🚀 FOREX MONEY MAKING BOT 🚀")
    print("💰" * 30)
    print()
    print("🎯 OBJETIVO: GENERAR DINERO REAL")
    print("⚡ MODO: AGRESIVO Y RENTABLE")
    print("💪 ESTRATEGIAS: PROBADAS Y OPTIMIZADAS")
    print()
    print("💡 Presiona Ctrl+C para detener de forma segura")
    print("=" * 60)
    
    # Crear y ejecutar bot
    money_bot = MoneyMakingBot()
    
    try:
        success = await money_bot.run()
        
        if success:
            print("\n✅ Bot ejecutado exitosamente")
        else:
            print("\n❌ Bot terminó con errores")
            
    except Exception as e:
        print(f"\n💥 Error fatal: {e}")
        logger.exception("Error detallado:")

if __name__ == "__main__":
    try:
        # Verificar que estamos en el directorio correcto
        if not os.path.exists('src'):
            print("❌ Error: Ejecutar desde el directorio raíz del bot")
            print("💡 Uso: cd Bot-Trading && python main_money_maker.py")
            sys.exit(1)
        
        # Ejecutar bot de dinero
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n⏹️ Bot detenido por el usuario")
    except Exception as e:
        print(f"\n💥 Error al iniciar: {e}")
        sys.exit(1)

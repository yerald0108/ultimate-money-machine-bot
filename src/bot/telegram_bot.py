"""
Bot de Telegram Refactorizado para trading de Forex
Interfaz principal con navegación por botones - Código limpio y modular
"""

import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from .handlers.menu_handlers import MenuHandlers
from .handlers.trading_handlers import TradingHandlers
from .handlers.optimization_handlers import OptimizationHandlers
from .handlers.monitoring_handlers import MonitoringHandlers
from .handlers.backtesting_handlers import BacktestingHandlers
from .handlers.dashboard_handlers import DashboardHandlers

logger = logging.getLogger(__name__)

class ForexTradingBot:
    def __init__(self, trading_engine):
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔍 [DEBUG] ForexTradingBot.__init__ called with trading_engine: {type(trading_engine)}")
        logger.info(f"🔍 [DEBUG] Trading engine has get_status: {hasattr(trading_engine, 'get_status')}")
        
        self.trading_engine = trading_engine
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.app = None
        
        # Inicializar handlers
        logger.info("🔍 [DEBUG] Inicializando handlers...")
        self.menu_handler = MenuHandlers(trading_engine)
        self.trading_handler = TradingHandlers(trading_engine)
        logger.info(f"🔍 [DEBUG] TradingHandlers creado con engine: {type(self.trading_handler.trading_engine)}")
        self.optimization_handler = OptimizationHandlers(trading_engine)
        self.monitoring_handler = MonitoringHandlers(trading_engine)
        self.backtesting_handler = BacktestingHandlers(trading_engine)
        self.dashboard_handler = DashboardHandlers(trading_engine)
        
    async def start(self):
        """Iniciar el bot de Telegram"""
        self.app = Application.builder().token(self.token).build()
        
        # Handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("start_trading", self.start_trading_command))
        self.app.add_handler(CommandHandler("stop_trading", self.stop_trading_command))
        self.app.add_handler(CommandHandler("trading_status", self.trading_status_command))
        self.app.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Error handler para timeouts
        self.app.add_error_handler(self.error_handler)
        
        # Iniciar polling
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        
        # Mantener el bot corriendo
        try:
            import signal
            import asyncio
            
            # Crear evento para mantener el bot corriendo
            stop_event = asyncio.Event()
            
            def signal_handler():
                stop_event.set()
            
            # Configurar manejadores de señales
            for sig in (signal.SIGTERM, signal.SIGINT):
                signal.signal(sig, lambda s, f: signal_handler())
            
            # Esperar hasta que se reciba una señal de parada
            await stop_event.wait()
            
        except Exception as e:
            logger.error(f"Error en el bucle principal: {e}")
        finally:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        await self.menu_handler.show_welcome_message(update)
    
    async def start_trading_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start_trading - Iniciar trading automático"""
        try:
            if hasattr(self, 'ultimate_machine') and self.ultimate_machine:
                if not self.ultimate_machine.running:
                    # Iniciar trading automático
                    import asyncio
                    asyncio.create_task(self.ultimate_machine.start_integrated_trading())
                    
                    message = """🚀 **TRADING AUTOMÁTICO INICIADO**

✅ **Estado**: Activo
🎯 **Configuración**: Optimizada para rentabilidad
📊 **Análisis**: Cada 15 segundos
💰 **Riesgo**: 2-5% por trade
🏆 **Posiciones máx**: 5 simultáneas
📈 **Confianza mín**: 75%

💡 **Comandos disponibles**:
/stop_trading - Detener trading
/trading_status - Ver estado actual"""
                    
                    await update.message.reply_text(message, parse_mode='Markdown')
                    logger.info("🚀 Trading automático iniciado por comando de Telegram")
                else:
                    await update.message.reply_text("⚠️ El trading automático ya está activo")
            else:
                await update.message.reply_text("❌ Ultimate Machine no disponible")
                
        except Exception as e:
            logger.error(f"Error iniciando trading: {e}")
            await update.message.reply_text(f"❌ Error iniciando trading: {str(e)}")
    
    async def stop_trading_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /stop_trading - Detener trading automático"""
        try:
            if hasattr(self, 'ultimate_machine') and self.ultimate_machine:
                if self.ultimate_machine.running:
                    await self.ultimate_machine.stop_integrated_trading()
                    
                    message = """⏹️ **TRADING AUTOMÁTICO DETENIDO**

✅ **Estado**: Inactivo
📊 **Posiciones**: Mantenidas (no cerradas automáticamente)
💰 **Balance**: Preservado

💡 **Para reanudar**: /start_trading"""
                    
                    await update.message.reply_text(message, parse_mode='Markdown')
                    logger.info("⏹️ Trading automático detenido por comando de Telegram")
                else:
                    await update.message.reply_text("⚠️ El trading automático ya está inactivo")
            else:
                await update.message.reply_text("❌ Ultimate Machine no disponible")
                
        except Exception as e:
            logger.error(f"Error deteniendo trading: {e}")
            await update.message.reply_text(f"❌ Error deteniendo trading: {str(e)}")
    
    async def trading_status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /trading_status - Ver estado del trading"""
        try:
            if hasattr(self, 'ultimate_machine') and self.ultimate_machine:
                # Obtener información de cuenta
                account_info = await self.ultimate_machine.mt5.get_account_info()
                positions = await self.ultimate_machine.mt5.get_positions()
                
                if account_info:
                    balance = account_info.get('balance', 0)
                    equity = account_info.get('equity', 0)
                    daily_pnl = balance - self.ultimate_machine.initial_balance if self.ultimate_machine.initial_balance > 0 else 0
                    daily_return = (daily_pnl / self.ultimate_machine.initial_balance * 100) if self.ultimate_machine.initial_balance > 0 else 0
                    unrealized_pnl = sum(pos.get('profit', 0) for pos in positions) if positions else 0
                    
                    status_icon = "🟢" if self.ultimate_machine.running else "🔴"
                    status_text = "ACTIVO" if self.ultimate_machine.running else "INACTIVO"
                    
                    message = f"""📊 **ESTADO DEL TRADING**

{status_icon} **Estado**: {status_text}

💰 **Información Financiera**:
• Balance: ${balance:,.2f}
• Equity: ${equity:,.2f}
• P&L del día: ${daily_pnl:+.2f}
• Retorno diario: {daily_return:+.2f}%
• P&L no realizado: ${unrealized_pnl:+.2f}

🏆 **Posiciones**: {len(positions) if positions else 0}
📊 **Trades hoy**: {self.ultimate_machine.daily_stats['trades']}

⚙️ **Configuración**:
• Riesgo por trade: 2-5%
• Posiciones máx: 5
• Confianza mín: 75%
• Análisis: Cada 15s"""
                    
                    await update.message.reply_text(message, parse_mode='Markdown')
                else:
                    await update.message.reply_text("❌ No se pudo obtener información de la cuenta")
            else:
                await update.message.reply_text("❌ Ultimate Machine no disponible")
                
        except Exception as e:
            logger.error(f"Error obteniendo estado: {e}")
            await update.message.reply_text(f"❌ Error obteniendo estado: {str(e)}")
    
    async def send_notification(self, message: str):
        """Enviar notificación al usuario"""
        try:
            if self.app and self.chat_id:
                await self.app.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
                logger.info("📨 Notificación enviada al usuario")
            else:
                logger.warning("⚠️ No se pudo enviar notificación - App o Chat ID no disponible")
        except Exception as e:
            logger.error(f"Error enviando notificación: {e}")
    
    async def handle_start_auto_trading(self, query):
        """Manejar botón de iniciar trading automático"""
        try:
            if hasattr(self, 'ultimate_machine') and self.ultimate_machine:
                if not self.ultimate_machine.running:
                    import asyncio
                    asyncio.create_task(self.ultimate_machine.start_integrated_trading())
                    
                    message = """🚀 **TRADING AUTOMÁTICO INICIADO**

✅ **Estado**: Activo
🎯 **Configuración**: Optimizada
📊 **Análisis**: Cada 15 segundos
💰 **Riesgo**: 2-5% por trade
🏆 **Posiciones máx**: 5 simultáneas

💡 **El bot está trabajando en segundo plano**
Puedes usar otros menús mientras busca operaciones."""
                    
                    # Crear botón para volver al menú
                    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                    keyboard = [
                        [InlineKeyboardButton("📊 Ver Estado Trading", callback_data="auto_trading_status")],
                        [InlineKeyboardButton("⏹️ Detener Trading", callback_data="stop_auto_trading")],
                        [InlineKeyboardButton("🔙 Volver al Menú Principal", callback_data="back_to_main")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
                    logger.info("🚀 Trading automático iniciado por botón")
                else:
                    await query.edit_message_text("⚠️ El trading automático ya está activo")
            else:
                await query.edit_message_text("❌ Ultimate Machine no disponible")
        except Exception as e:
            logger.error(f"Error iniciando trading: {e}")
            await query.edit_message_text(f"❌ Error: {str(e)}")
    
    async def handle_stop_auto_trading(self, query):
        """Manejar botón de detener trading automático"""
        try:
            if hasattr(self, 'ultimate_machine') and self.ultimate_machine:
                if self.ultimate_machine.running:
                    await self.ultimate_machine.stop_integrated_trading()
                    
                    message = """⏹️ **TRADING AUTOMÁTICO DETENIDO**

✅ **Estado**: Inactivo
📊 **Posiciones**: Mantenidas
💰 **Balance**: Preservado

💡 **El bot ya no busca nuevas operaciones**
Las posiciones abiertas se mantienen activas."""
                    
                    # Crear botones de navegación
                    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                    keyboard = [
                        [InlineKeyboardButton("🚀 Reiniciar Trading", callback_data="start_auto_trading")],
                        [InlineKeyboardButton("📊 Ver Estado", callback_data="auto_trading_status")],
                        [InlineKeyboardButton("🔙 Volver al Menú Principal", callback_data="back_to_main")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
                    logger.info("⏹️ Trading automático detenido por botón")
                else:
                    await query.edit_message_text("⚠️ El trading automático ya está inactivo")
            else:
                await query.edit_message_text("❌ Ultimate Machine no disponible")
        except Exception as e:
            logger.error(f"Error deteniendo trading: {e}")
            await query.edit_message_text(f"❌ Error: {str(e)}")
    
    async def handle_auto_trading_status(self, query):
        """Manejar botón de estado del trading automático"""
        try:
            if hasattr(self, 'ultimate_machine') and self.ultimate_machine:
                account_info = await self.ultimate_machine.mt5.get_account_info()
                positions = await self.ultimate_machine.mt5.get_positions()
                
                if account_info:
                    balance = account_info.get('balance', 0)
                    equity = account_info.get('equity', 0)
                    daily_pnl = balance - self.ultimate_machine.initial_balance if self.ultimate_machine.initial_balance > 0 else 0
                    daily_return = (daily_pnl / self.ultimate_machine.initial_balance * 100) if self.ultimate_machine.initial_balance > 0 else 0
                    unrealized_pnl = sum(pos.get('profit', 0) for pos in positions) if positions else 0
                    
                    status_icon = "🟢" if self.ultimate_machine.running else "🔴"
                    status_text = "ACTIVO" if self.ultimate_machine.running else "INACTIVO"
                    
                    # Agregar timestamp para forzar actualización
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    message = f"""📊 **ESTADO TRADING AUTOMÁTICO**

{status_icon} **Estado**: {status_text}

💰 **Financiero**:
• Balance: ${balance:,.2f}
• Equity: ${equity:,.2f}
• P&L día: ${daily_pnl:+.2f}
• Retorno: {daily_return:+.2f}%
• P&L no realizado: ${unrealized_pnl:+.2f}

🏆 **Posiciones**: {len(positions) if positions else 0}
📊 **Trades hoy**: {self.ultimate_machine.daily_stats['trades']}

🕐 **Actualizado**: {timestamp}"""
                    
                    # Crear botones según el estado
                    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                    if self.ultimate_machine.running:
                        keyboard = [
                            [InlineKeyboardButton("🔄 Actualizar Estado", callback_data="auto_trading_status")],
                            [InlineKeyboardButton("⏹️ Detener Trading", callback_data="stop_auto_trading")],
                            [InlineKeyboardButton("🔙 Volver al Menú Principal", callback_data="back_to_main")]
                        ]
                    else:
                        keyboard = [
                            [InlineKeyboardButton("🚀 Iniciar Trading", callback_data="start_auto_trading")],
                            [InlineKeyboardButton("🔄 Actualizar Estado", callback_data="auto_trading_status")],
                            [InlineKeyboardButton("🔙 Volver al Menú Principal", callback_data="back_to_main")]
                        ]
                    
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    try:
                        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
                    except Exception as edit_error:
                        # Si falla la edición, enviar mensaje nuevo
                        if "Message is not modified" in str(edit_error):
                            await query.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
                        else:
                            raise edit_error
                else:
                    await query.edit_message_text("❌ No se pudo obtener información")
            else:
                await query.edit_message_text("❌ Ultimate Machine no disponible")
        except Exception as e:
            logger.error(f"Error obteniendo estado: {e}")
            await query.edit_message_text(f"❌ Error: {str(e)}")
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar clicks en botones - Router principal"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        logger.info(f"🔍 [DEBUG] Button pressed: {data}")
        
        # === ROUTING DE HANDLERS ===
        
        # Trading handlers
        if data == "balance":
            await self.trading_handler.show_balance(query)
        elif data == "analysis":
            await self.trading_handler.show_analysis(query)
        elif data == "mtf_analysis":
            await self.trading_handler.show_mtf_analysis(query)
        elif data == "positions":
            await self.trading_handler.show_positions(query)
        elif data == "start_trading":
            await self.trading_handler.start_trading(query)
        elif data == "stop_trading":
            await self.trading_handler.stop_trading(query)
        elif data == "close_all":
            await self.trading_handler.close_all_positions(query)
        
        # Ultimate Money Machine handlers
        elif data == "start_auto_trading":
            await self.handle_start_auto_trading(query)
        elif data == "stop_auto_trading":
            await self.handle_stop_auto_trading(query)
        elif data == "auto_trading_status":
            await self.handle_auto_trading_status(query)
        elif data == "back_to_main":
            await self.menu_handler.show_main_menu(query)
        
        # Optimization handlers
        elif data == "optimize":
            await self.optimization_handler.show_optimize_menu(query)
        elif data == "settings":
            await self.optimization_handler.show_settings(query)
        elif data.startswith("opt_"):
            await self.optimization_handler.handle_optimization(query, data)
        
        # Monitoring handlers
        elif data == "performance":
            await self.monitoring_handler.show_performance_monitor(query)
        elif data == "test_connections":
            await self.monitoring_handler.run_connection_tests(query)
        elif data == "history":
            await self.monitoring_handler.show_history(query)
        elif data == "help":
            await self.monitoring_handler.show_help(query)
        
        # Dashboard handlers
        elif data == "dashboard_main":
            await self.dashboard_handler.show_performance_dashboard(query)
        elif data == "dashboard_daily":
            await self.dashboard_handler.show_daily_performance(query)
        elif data == "dashboard_weekly":
            await self.dashboard_handler.show_weekly_performance(query)
        elif data == "dashboard_strategy":
            await self.dashboard_handler.show_strategy_performance(query)
        elif data == "dashboard_pairs":
            await self.dashboard_handler.show_pairs_performance(query)
        elif data == "dashboard_drawdown":
            await self.dashboard_handler.show_drawdown_analysis(query)
        elif data == "dashboard_realtime":
            await self.dashboard_handler.show_realtime_metrics(query)
        elif data == "drawdown_chart":
            await query.edit_message_text("📊 Gráfico de Drawdown - Función avanzada en desarrollo")
        elif data == "realtime_autorefresh":
            await query.edit_message_text("📡 Auto-refresh activado - Función en desarrollo")
        elif data == "positions_detail":
            await query.edit_message_text("🎯 Detalle de posiciones - Redirigiendo a balance...")
        
        # Menu navigation
        elif data == "back_to_menu":
            await self.menu_handler.show_main_menu(query)
        
        else:
            # Handler no encontrado
            await query.edit_message_text(
                "❌ Función no implementada aún.",
                parse_mode='Markdown'
            )
    
    async def error_handler(self, update, context):
        """Manejar errores de Telegram (timeouts, etc.)"""
        import telegram
        
        # Solo logear errores importantes, ignorar timeouts comunes
        if isinstance(context.error, telegram.error.TimedOut):
            logger.debug("Timeout de Telegram (normal) - ignorando")
            return
        elif isinstance(context.error, telegram.error.NetworkError):
            logger.warning(f"Error de red de Telegram: {context.error}")
            return
        else:
            logger.error(f"Error no manejado en Telegram: {context.error}")
            # Para otros errores, logear más detalles si es necesario

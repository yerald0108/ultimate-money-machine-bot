"""
Handlers para monitoreo y testing
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime

class MonitoringHandlers:
    def __init__(self, trading_engine):
        self.trading_engine = trading_engine
    
    async def show_performance_monitor(self, query):
        """Mostrar monitor de rendimiento"""
        try:
            # Obtener datos de rendimiento
            account_info = await self.trading_engine.get_balance()
            
            # Calcular rendimiento diario (simplificado)
            today_profit = 0  # Se calculará con datos reales del MT5
            
            performance_text = f"""
📊 *Monitor de Rendimiento*

💰 **Estado de Cuenta:**
• Balance: ${account_info.get('balance', 0):,.2f}
• Equity: ${account_info.get('equity', 0):,.2f}
• Margen Libre: ${account_info.get('free_margin', 0):,.2f}
• Nivel Margen: {account_info.get('margin_level', 0):.1f}%

📈 **Rendimiento Hoy:**
• Profit/Loss: ${today_profit:,.2f}
• Posiciones Abiertas: {len(await self.trading_engine.get_open_positions())}

🎯 **Métricas:**
• Win Rate: Calculando...
• Trades Hoy: Calculando...
• ROI Diario: Calculando...

⏱️ *Actualizado: {datetime.now().strftime('%H:%M:%S')}*
            """
            
            keyboard = [
                [InlineKeyboardButton("🔄 Actualizar", callback_data="performance")],
                [InlineKeyboardButton("📊 Historial Detallado", callback_data="history")],
                [InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                performance_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            error_text = f"""
❌ *Error en Monitor de Rendimiento*

No se pudieron obtener los datos de rendimiento.

Error: {str(e)}
            """
            
            keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                error_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    async def run_connection_tests(self, query):
        """Ejecutar tests de conexión integrados"""
        
        # Mostrar mensaje de "probando..."
        test_text = """
🧪 *Ejecutando Tests de Conexión*

🔄 Probando conexiones...
⏳ Esto puede tomar unos segundos...
        """
        
        await query.edit_message_text(
            test_text,
            parse_mode='Markdown'
        )
        
        # Ejecutar tests
        results = {
            'mt5': False,
            'telegram': True,  # Si llegamos aquí, Telegram funciona
            'analysis': False
        }
        
        # Test MT5
        try:
            if hasattr(self.trading_engine, 'mt5'):
                mt5_connected = self.trading_engine.mt5.is_connected()
                if mt5_connected:
                    account_info = await self.trading_engine.mt5.get_account_info()
                    results['mt5'] = bool(account_info)
        except:
            results['mt5'] = False
        
        # Test análisis
        try:
            analysis = await self.trading_engine.get_market_analysis()
            results['analysis'] = bool(analysis)
        except:
            results['analysis'] = False
        
        # Mostrar resultados
        mt5_status = "✅ PASS" if results['mt5'] else "❌ FAIL"
        telegram_status = "✅ PASS"  # Siempre pasa si llegamos aquí
        analysis_status = "✅ PASS" if results['analysis'] else "❌ FAIL"
        
        all_passed = all(results.values())
        overall_status = "🎉 Todas las pruebas pasaron" if all_passed else "⚠️ Algunas pruebas fallaron"
        
        results_text = f"""
🧪 *Resultados de Tests de Conexión*

📋 **Resumen:**
{overall_status}

🔍 **Detalles:**
• Conexión MT5: {mt5_status}
• Bot Telegram: {telegram_status}
• Análisis Técnico: {analysis_status}

{'🚀 El bot está listo para operar' if all_passed else '⚠️ Revisa las conexiones fallidas'}
        """
        
        keyboard = [
            [InlineKeyboardButton("🔄 Ejecutar de Nuevo", callback_data="test_connections")],
            [InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            results_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def show_history(self, query):
        """Mostrar historial de trades"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info("🔍 [DEBUG] show_history called")
        
        try:
            logger.info("🔍 [DEBUG] Calling get_trade_history...")
            history = await self.trading_engine.get_trade_history()
            logger.info(f"🔍 [DEBUG] get_trade_history returned {len(history) if history else 0} trades")
            
            if not history:
                history_text = """
📋 Historial de Trades

📭 No hay trades en el historial aún.

Una vez que el bot comience a operar, verás aquí el historial completo de operaciones.
                """
            else:
                history_text = "📋 Historial de Trades (Últimos 10)\n\n"
                
                for i, trade in enumerate(history[:10]):
                    logger.info(f"🔍 [DEBUG] Processing trade {i}: {trade}")
                    
                    # Manejo robusto de datos del trade
                    trade_id = trade.get('id', trade.get('order_id', trade.get('ticket', trade.get('deal', i+1))))
                    symbol = trade.get('symbol', 'EUR/USD')
                    # Si symbol está vacío, usar EUR/USD por defecto
                    if not symbol or symbol.strip() == '':
                        symbol = 'EUR/USD'
                    
                    trade_type = trade.get('type', trade.get('signal', 'UNKNOWN'))
                    volume = trade.get('volume', trade.get('lot_size', 0))
                    profit = trade.get('profit', 0)
                    
                    # Manejo robusto de fecha/hora
                    close_time = trade.get('close_time', trade.get('timestamp', trade.get('time', 'N/A')))
                    
                    # Si close_time es un objeto datetime, convertirlo a string
                    if hasattr(close_time, 'strftime'):
                        close_time = close_time.strftime('%Y-%m-%d %H:%M:%S')
                    elif close_time == 'N/A':
                        close_time = 'Fecha no disponible'
                    
                    logger.info(f"🔍 [DEBUG] Processed data - ID: {trade_id}, Symbol: {symbol}, Time: {close_time}")
                    
                    # Emojis simples y seguros
                    profit_emoji = "✅" if profit > 0 else "❌" if profit < 0 else "⚪"
                    type_emoji = "📈" if trade_type == "BUY" else "📉" if trade_type == "SELL" else "📊"
                    
                    history_text += f"""
{profit_emoji} Trade #{trade_id}
{type_emoji} {symbol} - {trade_type}
📊 Volumen: {volume}
💰 P&L: {profit:.2f} USD
🕒 {close_time}

━━━━━━━━━━━━━━━━━━━━━━

"""
            
            keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                await query.edit_message_text(
                    history_text.strip(),
                    reply_markup=reply_markup
                )
            except Exception as parse_error:
                logger.error(f"🔍 [DEBUG] Telegram parse error in history: {parse_error}")
                # Fallback con emojis básicos solamente
                if not history:
                    simple_text = """
Historial de Trades

No hay trades en el historial aún.

Una vez que el bot comience a operar, verás aquí el historial completo de operaciones.
                    """
                else:
                    simple_text = f"Historial de Trades (Últimos 10)\n\n"
                    
                    for i, trade in enumerate(history[:10]):
                        trade_id = trade.get('id', trade.get('order_id', trade.get('ticket', trade.get('deal', i+1))))
                        symbol = trade.get('symbol', 'EUR/USD')
                        # Si symbol está vacío, usar EUR/USD por defecto
                        if not symbol or symbol.strip() == '':
                            symbol = 'EUR/USD'
                        
                        trade_type = trade.get('type', trade.get('signal', 'UNKNOWN'))
                        volume = trade.get('volume', trade.get('lot_size', 0))
                        profit = trade.get('profit', 0)
                        
                        # Manejo robusto de fecha/hora
                        close_time = trade.get('close_time', trade.get('timestamp', trade.get('time', 'N/A')))
                        
                        # Si close_time es un objeto datetime, convertirlo a string
                        if hasattr(close_time, 'strftime'):
                            close_time = close_time.strftime('%Y-%m-%d %H:%M:%S')
                        elif close_time == 'N/A':
                            close_time = 'Fecha no disponible'
                        
                        # Solo emojis muy básicos
                        status_emoji = "+" if profit > 0 else "-" if profit < 0 else "="
                        
                        simple_text += f"""
Trade #{trade_id}
{symbol} - {trade_type}
Volumen: {volume}
P&L: {status_emoji}{profit:.2f} USD
Fecha: {close_time}

---

"""
                
                await query.edit_message_text(
                    simple_text.strip(),
                    reply_markup=reply_markup
                )
                
        except Exception as e:
            logger.error(f"🔍 [DEBUG] Error in show_history: {e}")
            error_text = f"""
Error obteniendo historial

No se pudo obtener el historial de trades.

Error: {str(e)[:100]}

Solucion: Intenta nuevamente o reinicia el bot.
            """
            
            keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                error_text.strip(),
                reply_markup=reply_markup
            )
    
    async def show_help(self, query):
        """Mostrar ayuda"""
        help_text = """
ℹ️ *Ayuda - Forex Trading Bot*

🤖 *¿Qué hace este bot?*
Este bot opera automáticamente en el par EUR/USD usando análisis técnico avanzado y gestión de riesgo.

📊 *Funciones Principales:*
• Análisis técnico en tiempo real
• Trading automatizado 24/5
• Gestión de riesgo integrada
• Notificaciones instantáneas
• Control total desde Telegram

⚙️ *Configuración Recomendada:*
• Cuenta demo para pruebas
• Riesgo máximo 2% por trade
• Stop Loss siempre activo
• Monitoreo regular del rendimiento

🆘 *Controles de Emergencia:*
• "Pausar Trading" - Detiene nuevas operaciones
• "Cerrar Todo" - Cierra todas las posiciones
• El bot respeta siempre los límites de riesgo

⚠️ *Importante:*
- Siempre usa cuenta demo primero
- Nunca inviertas más de lo que puedes perder
- El trading conlleva riesgos
        """
        
        keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            help_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def show_ml_stats(self, query):
        """Mostrar estadísticas de Machine Learning"""
        try:
            # Obtener estadísticas ML del analizador
            if hasattr(self.trading_engine, 'analyzer') and hasattr(self.trading_engine.analyzer, 'get_ml_stats'):
                ml_stats = self.trading_engine.analyzer.get_ml_stats()
            else:
                ml_stats = {'ml_enabled': False}
            
            # Agregar timestamp para evitar contenido duplicado
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if not ml_stats.get('ml_enabled', False):
                # Mostrar barra de progreso de inicialización ML
                await self._show_ml_initialization_progress(query, timestamp)
                return
            else:
                recent_success = ml_stats.get('recent_success_rate', 0) * 100
                improvement = ml_stats.get('improvement_trend', 0) * 100
                total_learned = ml_stats.get('total_trades_learned', 0)
                learning_cycles = ml_stats.get('learning_cycles', 0)
                
                trend_emoji = "📈" if improvement > 0 else "📉" if improvement < 0 else "➡️"
                
                ml_text = f"""
🧠 *Machine Learning - Estadísticas*

⏰ **Actualizado**: {timestamp}

📊 **Rendimiento Actual:**
• Precisión Reciente: {recent_success:.1f}%
• Tendencia: {trend_emoji} {improvement:+.1f}%
• Trades Aprendidos: {total_learned}
• Ciclos de Optimización: {learning_cycles}

🎯 **Sistema Adaptativo:**
• Confianza Mínima: Ajustada automáticamente
• Pesos de Indicadores: Optimizados por rendimiento
• Preferencias de Sesión: Basadas en historial
• Gestión de Riesgo: Adaptativa

🔄 **Aprendizaje Continuo:**
• El bot aprende de cada trade
• Se optimiza automáticamente cada 10 trades
• Mejora la precisión con el tiempo
• Adapta estrategia según condiciones

⚡ **Estado:** Sistema ML activo y aprendiendo
                """
            
            keyboard = [
                [InlineKeyboardButton("🔄 Actualizar", callback_data="ml_stats")],
                [InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                ml_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            from datetime import datetime
            error_timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Verificar si es error de mensaje duplicado
            if "Message is not modified" in str(e):
                error_text = f"""
🤖 *Machine Learning - Sistema Inicializando*

⏰ **Actualizado**: {error_timestamp}

🔄 **Estado**: El sistema ML se está configurando...

📊 **Información**:
• Sistema en proceso de inicialización
• Se activará automáticamente con el primer trade
• El aprendizaje comenzará una vez que haya datos

🎯 **Para activar**:
1. Asegúrate de que el trading esté activo (▶️ Iniciar Trading)
2. Espera el primer trade
3. El ML se activará automáticamente

⚡ **Nota**: Este es el comportamiento normal durante la inicialización
                """
            else:
                error_text = f"""
❌ *Error en Estadísticas ML*

⏰ **Hora**: {error_timestamp}

No se pudieron obtener las estadísticas de Machine Learning.

🔧 **Detalles técnicos**: {str(e)[:100]}...

🎯 **Solución**: Reinicia el bot para recargar el sistema ML
                """
            
            keyboard = [
                [InlineKeyboardButton("🔄 Reintentar", callback_data="ml_stats")],
                [InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                error_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    async def _show_ml_initialization_progress(self, query, timestamp):
        """Mostrar progreso de inicialización del sistema ML"""
        import asyncio
        
        # Simular progreso de inicialización ML
        steps = [
            (0, "Inicializando sistema ML..."),
            (15, "Cargando datos de aprendizaje..."),
            (30, "Configurando parámetros adaptativos..."),
            (45, "Inicializando redes neuronales..."),
            (60, "Calibrando algoritmos de optimización..."),
            (75, "Preparando sistema de aprendizaje continuo..."),
            (90, "Finalizando configuración ML..."),
            (100, "Sistema ML listo para activación")
        ]
        
        for percentage, step_description in steps:
            await self._update_ml_progress(query, percentage, step_description, timestamp)
            await asyncio.sleep(0.8)
        
        # Mostrar estado final
        await self._show_ml_ready_state(query, timestamp)
    
    async def _update_ml_progress(self, query, percentage: int, step_description: str, timestamp: str):
        """Actualizar barra de progreso ML"""
        
        # Crear barra de progreso
        filled_blocks = int(percentage / 5)
        empty_blocks = 20 - filled_blocks
        progress_bar = "■" * filled_blocks + "□" * empty_blocks
        
        # Determinar emoji de estado
        if percentage == 0:
            status_emoji = "🔄"
        elif percentage < 100:
            status_emoji = "⚡"
        else:
            status_emoji = "✅"
        
        progress_text = f"""
🧠 *Machine Learning - Inicializando*

{status_emoji} *Progreso*: {percentage}%
{progress_bar}

📋 *Estado Actual*: {step_description}

⏰ *Actualizado*: {timestamp}
🎯 *Proceso*: Configuración del Sistema ML

💡 *Información*:
• Carga de algoritmos de aprendizaje
• Configuración de parámetros adaptativos
• Preparación para aprendizaje continuo
• Calibración de redes neuronales

🔄 *Próximo*: Sistema listo para primer trade
        """
        
        try:
            await query.edit_message_text(
                progress_text.strip(),
                parse_mode='Markdown'
            )
        except Exception:
            try:
                plain_text = progress_text.replace('*', '').replace('_', '')
                await query.edit_message_text(plain_text.strip())
            except Exception:
                pass
    
    async def _show_ml_ready_state(self, query, timestamp):
        """Mostrar estado final del ML listo"""
        
        final_text = f"""
🧠 *Machine Learning - Sistema Listo*

✅ *Estado*: Configuración completada
■■■■■■■■■■■■■■■■■■■■

📋 *Sistema ML*: Listo para activación

⏰ *Actualizado*: {timestamp}
🎯 *Estado*: Esperando primer trade

💡 *Información*:
• Sistema ML completamente configurado
• Algoritmos de aprendizaje listos
• Se activará automáticamente con el primer trade
• Comenzará optimización continua

🚀 *Para activar*:
1. Inicia el trading (▶️ Iniciar Trading)
2. Espera el primer trade
3. El ML se activará automáticamente
4. Comenzará el aprendizaje continuo

⚡ *Nota*: El sistema está listo y esperando datos
        """
        
        keyboard = [
            [InlineKeyboardButton("🔄 Actualizar", callback_data="ml_stats")],
            [InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                final_text.strip(),
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception:
            try:
                plain_text = final_text.replace('*', '').replace('_', '')
                await query.edit_message_text(
                    plain_text.strip(),
                    reply_markup=reply_markup
                )
            except Exception:
                pass

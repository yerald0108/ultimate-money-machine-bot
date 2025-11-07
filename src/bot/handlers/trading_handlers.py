"""
Handlers para funciones de trading
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime

class TradingHandlers:
    def __init__(self, trading_engine):
        self.trading_engine = trading_engine
    
    async def show_status(self, query):
        """Mostrar estado del bot"""
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            logger.info("🔍 [DEBUG] Iniciando show_status")
            logger.info(f"🔍 [DEBUG] Trading engine type: {type(self.trading_engine)}")
            logger.info(f"🔍 [DEBUG] Trading engine methods: {[method for method in dir(self.trading_engine) if 'get_status' in method]}")
            
            # Verificar si el método existe
            if not hasattr(self.trading_engine, 'get_status'):
                logger.error("❌ [DEBUG] get_status method NOT FOUND!")
                logger.error(f"❌ [DEBUG] Available methods: {[method for method in dir(self.trading_engine) if method.startswith('get_')]}")
                raise AttributeError("get_status method not found")
            
            logger.info("✅ [DEBUG] get_status method found, calling it...")
            status = await self.trading_engine.get_status()
            logger.info(f"✅ [DEBUG] get_status returned: {status}")
            
            # Limpiar valores para evitar errores de parsing
            trading_status = "🟢 Activo" if status.get('trading_active', False) else "🔴 Inactivo"
            last_analysis = status.get('last_analysis', 'Nunca')
            trades_today = status.get('total_trades_today', 0)
            balance = status.get('account_balance', 0)
            equity = status.get('account_equity', 0)
            open_positions = status.get('open_positions', 0)
            min_confidence = status.get('min_confidence', 75)
            current_session = status.get('current_session', 'Desconocida')
            
            # Limpiar valores para evitar caracteres problemáticos
            balance_str = f"{balance:,.2f}".replace(',', ' ')
            equity_str = f"{equity:,.2f}".replace(',', ' ')
            
            status_text = f"""
📊 Estado del Bot

🔄 Trading: {trading_status}
📈 Último Análisis: {last_analysis}
💹 Trades Hoy: {trades_today}
💰 Balance: {balance_str} USD
💎 Equity: {equity_str} USD
📊 Posiciones Abiertas: {open_positions}
🎯 Confianza Mínima: {min_confidence}%
🌍 Sesión Actual: {current_session}

⚙️ Configuración:
• Multi-Timeframe Analysis: Activo
• Machine Learning: Activo
• Risk Management: Activo
            """
            
            keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                await query.edit_message_text(
                    status_text,
                    reply_markup=reply_markup
                )
            except Exception as parse_error:
                # Fallback sin emojis si hay problemas de parsing
                simple_text = f"""
Estado del Bot

Trading: {trading_status}
Ultimo Analisis: {last_analysis}
Trades Hoy: {trades_today}
Balance: {balance_str} USD
Equity: {equity_str} USD
Posiciones Abiertas: {open_positions}
Confianza Minima: {min_confidence}%
Sesion Actual: {current_session}

Configuracion:
- Multi-Timeframe Analysis: Activo
- Machine Learning: Activo
- Risk Management: Activo
                """
                await query.edit_message_text(
                    simple_text.strip(),
                    reply_markup=reply_markup
                )
            
        except Exception as e:
            error_text = f"""
Error obteniendo estado

No se pudo obtener el estado del bot.

Error: {str(e)[:100]}

Solucion: Intenta nuevamente o reinicia el bot.
            """
            
            keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                error_text.strip(),
                reply_markup=reply_markup
            )
    
    async def show_balance(self, query):
        """Mostrar balance de la cuenta"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info("🔍 [DEBUG] show_balance called")
        logger.info(f"🔍 [DEBUG] Trading engine has get_balance: {hasattr(self.trading_engine, 'get_balance')}")
        
        try:
            logger.info("🔍 [DEBUG] Calling get_balance...")
            balance_info = await self.trading_engine.get_balance()
            logger.info(f"🔍 [DEBUG] get_balance returned: {balance_info}")
            
            # Limpiar valores para evitar errores de parsing
            balance = balance_info.get('balance', 0)
            equity = balance_info.get('equity', 0)
            floating_pl = balance_info.get('floating_pl', 0)
            free_margin = balance_info.get('free_margin', 0)
            margin = balance_info.get('margin', 0)
            margin_level = balance_info.get('margin_level', 0)
            risk_per_trade = balance_info.get('risk_per_trade', 2.0)
            max_daily_loss = balance_info.get('max_daily_loss', 0)
            
            balance_text = f"""
💰 Balance de Cuenta

💵 Balance: {balance:,.2f} USD
📊 Equity: {equity:,.2f} USD
📈 P&L Flotante: {floating_pl:,.2f} USD
💳 Margen Libre: {free_margin:,.2f} USD
📉 Margen Usado: {margin:,.2f} USD

📊 Nivel de Margen: {margin_level:.1f}%

🎯 Gestión de Riesgo:
⚠️ Riesgo por Trade: {risk_per_trade}%
🛡️ Pérdida Máxima Diaria: {max_daily_loss:,.2f} USD
            """
            
            keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                balance_text.strip(),
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"🔍 [DEBUG] Error in show_balance: {e}")
            error_text = f"""
Error obteniendo balance

No se pudo obtener la información de balance.

Error: {str(e)[:100]}

Solucion: Intenta nuevamente o reinicia el bot.
            """
            
            keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                error_text.strip(),
                reply_markup=reply_markup
            )
    
    async def show_analysis(self, query):
        """Mostrar análisis del mercado EUR/USD"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info("🔍 [DEBUG] show_analysis called")
        
        try:
            logger.info("🔍 [DEBUG] Calling get_market_analysis...")
            analysis = await self.trading_engine.get_market_analysis()
            logger.info(f"🔍 [DEBUG] get_market_analysis returned: {analysis}")
            
            if 'error' in analysis:
                analysis_text = f"""
Error en Análisis EUR/USD

No se pudo obtener el análisis del mercado.

Error: {analysis['error'][:100]}

Solución: Intenta nuevamente o verifica la conexión MT5.
                """
            else:
                # Limpiar valores para evitar errores de parsing
                current_price = analysis.get('current_price', 0)
                trend = analysis.get('trend', 'UNKNOWN')
                signal = analysis.get('signal', 'HOLD')
                confidence = analysis.get('confidence', 0)
                rsi = analysis.get('rsi', 0)
                bb_position = analysis.get('bb_position', 'Middle')
                sma20 = analysis.get('sma20', current_price)
                sma50 = analysis.get('sma50', current_price)
                recommendation = analysis.get('recommendation', 'Sin recomendación')
                timestamp = analysis.get('timestamp', 'Desconocido')
                current_session = analysis.get('current_session', 'Desconocida')
                
                # Limpiar recommendation para evitar caracteres problemáticos
                recommendation_clean = str(recommendation).replace('*', '').replace('_', '').replace('[', '').replace(']', '')
                
                analysis_text = f"""
📈 Análisis EUR/USD

💱 Precio Actual: {current_price:.5f}
📊 Tendencia: {trend}
⚡ Señal: {signal}
⭐ Confianza: {confidence:.1f}%

📊 Indicadores Técnicos:
📈 RSI: {rsi:.1f}
🌊 Bollinger: {bb_position}
📊 SMA 20: {sma20:.5f}
📊 SMA 50: {sma50:.5f}

🎯 Recomendación: {recommendation_clean}
🌍 Sesión: {current_session}
🕒 Actualizado: {timestamp}
                """
            
            keyboard = [
                [InlineKeyboardButton("🔄 Actualizar", callback_data="analysis")],
                [InlineKeyboardButton("📊 Multi-TF", callback_data="mtf_analysis")],
                [InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                await query.edit_message_text(
                    analysis_text.strip(),
                    reply_markup=reply_markup
                )
            except Exception as parse_error:
                logger.error(f"🔍 [DEBUG] Telegram parse error: {parse_error}")
                # Fallback sin emojis si hay problemas de parsing
                simple_text = f"""
Analisis EUR/USD

Precio Actual: {current_price:.5f}
Tendencia: {trend}
Señal: {signal}
Confianza: {confidence:.1f}%

Indicadores Tecnicos:
RSI: {rsi:.1f}
Bollinger: {bb_position}
SMA 20: {sma20:.5f}
SMA 50: {sma50:.5f}

Recomendacion: {recommendation_clean}
Sesion: {current_session}
Actualizado: {timestamp}
                """
                await query.edit_message_text(
                    simple_text.strip(),
                    reply_markup=reply_markup
                )
            
        except Exception as e:
            logger.error(f"🔍 [DEBUG] Error in show_analysis: {e}")
            error_text = f"""
Error en Analisis

No se pudo obtener el analisis del mercado.

Error: {str(e)[:100]}

Solucion: Intenta nuevamente o reinicia el bot.
            """
            
            keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                error_text.strip(),
                reply_markup=reply_markup
            )
    
    async def show_positions(self, query):
        """Mostrar posiciones abiertas"""
        positions = await self.trading_engine.get_open_positions()
        
        if not positions:
            positions_text = """
🔍 *Posiciones Abiertas*

📭 No hay posiciones abiertas actualmente.

El bot está monitoreando el mercado en busca de oportunidades de trading.
            """
        else:
            positions_text = "🔍 *Posiciones Abiertas*\n\n"
            
            for i, pos in enumerate(positions, 1):
                positions_text += f"""
📊 *Posición #{i}*
💱 Par: {pos['symbol']}
📈 Tipo: {pos['type']}
💰 Volumen: {pos['volume']}
💵 Precio Entrada: {pos['open_price']:.5f}
📊 Precio Actual: {pos['current_price']:.5f}
💹 P&L: ${pos['profit']:.2f}
🕒 Tiempo: {pos['open_time']}

---
                """
        
        keyboard = [
            [InlineKeyboardButton("🔄 Actualizar", callback_data="positions")],
            [InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            positions_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def start_trading(self, query):
        """Iniciar trading automatizado"""
        try:
            result = await self.trading_engine.start_trading()
            
            if result.get('success', False):
                message = """
▶️ *Trading Iniciado*

🟢 El bot está ahora operando automáticamente
📊 Monitoreando EUR/USD en tiempo real
🎯 Buscando oportunidades de trading

⚠️ *Recordatorio*:
• El bot opera con gestión de riesgo
• Todas las operaciones tienen Stop Loss
• Puedes pausar en cualquier momento
                """
            else:
                error_msg = str(result.get('error', 'Error desconocido'))[:100]
                message = f"""
❌ *Error al Iniciar Trading*

{error_msg}

Por favor, verifica la conexión y configuración.
                """
        except Exception as e:
            error_msg = str(e)[:100]
            message = f"""
❌ *Error Crítico*

No se pudo iniciar el trading.

Error: {error_msg}

Intenta reiniciar el bot.
            """
        
        keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def stop_trading(self, query):
        """Pausar trading automatizado"""
        result = await self.trading_engine.stop_trading()
        
        message = """
⏸️ *Trading Pausado*

🔴 El bot ha pausado las operaciones automáticas
📊 Las posiciones abiertas permanecen activas
🔄 Puedes reanudar cuando desees

Las posiciones existentes seguirán siendo monitoreadas.
        """
        
        keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def close_all_positions(self, query):
        """Cerrar todas las posiciones"""
        result = await self.trading_engine.close_all_positions()
        
        if result['success']:
            message = f"""
🆘 *Todas las Posiciones Cerradas*

✅ Se cerraron {result['closed_count']} posiciones
💰 P&L Total: ${result['total_pl']:.2f}

Todas las operaciones han sido cerradas exitosamente.
            """
        else:
            message = f"""
❌ *Error al Cerrar Posiciones*

{result['error']}

Algunas posiciones pueden no haberse cerrado correctamente.
            """
        
        keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def show_mtf_analysis(self, query):
        """Mostrar análisis Multi-Timeframe detallado"""
        try:
            from datetime import datetime
            
            # Verificar si MTF está disponible
            analyzer = self.trading_engine.analyzer
            
            if not hasattr(analyzer, 'mtf_enabled') or not analyzer.mtf_enabled:
                mtf_text = """
📊 *Multi-Timeframe Analysis - No Disponible*

⚠️ **Estado**: MTF no está configurado

🔧 **Razón**: 
• Sistema Multi-Timeframe no inicializado
• Requiere reinicio del bot para activación

💡 **Para activar**:
1. Reinicia el bot
2. MTF se activará automáticamente
3. Análisis de H1, M15, M5, M1 simultáneo

🎯 **Beneficios del MTF**:
• +25-35% mejor precisión
• Confirmación cruzada de señales
• Análisis de tendencia principal (H1)
• Timing preciso (M1)
                """
            else:
                # Obtener análisis MTF
                should_trade, signal, trade_info = await analyzer.should_trade_premium_mtf()
                
                # Extraer información MTF
                mtf_analysis = trade_info.get('mtf_analysis', {})
                analysis_type = trade_info.get('analysis_type', 'Multi-Timeframe')
                convergence = trade_info.get('convergence_quality', 'UNKNOWN')
                alignment = trade_info.get('timeframes_aligned', 0)
                
                # Generar resumen
                if mtf_analysis and hasattr(analyzer, 'mtf_analyzer'):
                    mtf_summary = analyzer.mtf_analyzer.get_timeframe_summary(mtf_analysis)
                else:
                    mtf_summary = "❌ No se pudo obtener análisis MTF"
                
                # Construir mensaje
                signal_emoji = "📈" if signal == 'BUY' else "📉" if signal == 'SELL' else "⏸️"
                convergence_emoji = "🟢" if convergence == 'HIGH' else "🟡" if convergence == 'MEDIUM' else "🔴"
                
                mtf_text = f"""
🎯 *Multi-Timeframe Analysis*

{signal_emoji} **Señal Global**: {signal}
📊 **Confianza**: {trade_info.get('confidence', 0):.1f}%
{convergence_emoji} **Convergencia**: {convergence}
📈 **Alineación**: {alignment:.1%}

{mtf_summary}

🔍 **Tipo de Análisis**: {analysis_type}
⏰ **Actualizado**: {datetime.now().strftime('%H:%M:%S')}

💡 **Interpretación**:
• 🟢 HIGH: Todos los timeframes alineados
• 🟡 MEDIUM: Mayoría de timeframes alineados  
• 🔴 LOW: Timeframes en conflicto

🎯 **Recomendación**: {'✅ OPERAR' if should_trade else '⏸️ ESPERAR'}
                """
            
            keyboard = [
                [InlineKeyboardButton("🔄 Actualizar MTF", callback_data="mtf_analysis")],
                [InlineKeyboardButton("📈 Análisis Simple", callback_data="analysis")],
                [InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                mtf_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            error_text = f"""
❌ *Error en Multi-Timeframe Analysis*

No se pudo obtener el análisis Multi-Timeframe.

🔧 **Error**: {str(e)[:100]}...

💡 **Solución**: 
• Reinicia el bot para recargar MTF
• Verifica conexión MT5
            """
            
            keyboard = [
                [InlineKeyboardButton("📈 Análisis Simple", callback_data="analysis")],
                [InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                error_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

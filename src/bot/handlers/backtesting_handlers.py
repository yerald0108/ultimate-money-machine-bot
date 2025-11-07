"""
Handlers de Backtesting para Telegram
Interfaz para ejecutar y ver resultados de backtesting
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
from typing import List
import logging
import asyncio
from ...backtesting.backtesting_engine import BacktestingEngine
from ...backtesting.report_generator import BacktestReportGenerator

class BacktestingHandlers:
    """Manejadores de backtesting para Telegram"""
    
    def __init__(self, trading_engine):
        self.trading_engine = trading_engine
        self.logger = logging.getLogger(__name__)
        self.report_generator = BacktestReportGenerator()
        
    async def show_backtesting_menu(self, query):
        """Mostrar menú principal de backtesting"""
        
        menu_text = """
🔬 **BACKTESTING AUTOMÁTICO**

Valida la rentabilidad de las estrategias con datos históricos antes de arriesgar dinero real.

📊 **Opciones Disponibles**:
• **Backtesting Rápido**: Últimos 30 días
• **Backtesting Mensual**: Últimos 3 meses  
• **Backtesting Trimestral**: Últimos 6 meses
• **Backtesting Personalizado**: Período específico

⚡ **Características**:
• Simulación realista con spreads y slippage
• Análisis Multi-Timeframe completo
• Métricas profesionales de rendimiento
• Reportes detallados automáticos

🎯 **Métricas Calculadas**:
• Win Rate y Profit Factor
• Drawdown máximo y Sharpe Ratio
• Análisis mensual y por trades
• Recomendaciones automáticas
        """
        
        keyboard = [
            [InlineKeyboardButton("⚡ Backtesting Rápido (30d)", callback_data="backtest_quick")],
            [InlineKeyboardButton("📊 Backtesting Mensual (3m)", callback_data="backtest_monthly")],
            [InlineKeyboardButton("📈 Backtesting Trimestral (6m)", callback_data="backtest_quarterly")],
            [InlineKeyboardButton("🎯 Backtesting Personalizado", callback_data="backtest_custom")],
            [InlineKeyboardButton("📋 Ver Último Reporte", callback_data="backtest_last_report")],
            [InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            menu_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def run_quick_backtest(self, query):
        """Ejecutar backtesting rápido (30 días)"""
        
        await self._run_backtest(
            query, 
            days=30, 
            name="Rápido (30 días)",
            show_progress=True
        )
    
    async def run_monthly_backtest(self, query):
        """Ejecutar backtesting mensual (3 meses)"""
        
        await self._run_backtest(
            query, 
            days=90, 
            name="Mensual (3 meses)",
            show_progress=True
        )
    
    async def run_quarterly_backtest(self, query):
        """Ejecutar backtesting trimestral (6 meses)"""
        
        await self._run_backtest(
            query, 
            days=180, 
            name="Trimestral (6 meses)",
            show_progress=True
        )
    
    async def _run_backtest(self, query, days: int, name: str, show_progress: bool = True):
        """Ejecutar backtesting con parámetros específicos"""
        
        try:
            # Verificar configuración previa
            if not hasattr(self.trading_engine, 'mt5'):
                raise Exception("Motor de trading no configurado correctamente")
            
            if not hasattr(self.trading_engine, 'analyzer'):
                raise Exception("Analizador de mercado no disponible")
            
            # Inicializar tiempo de inicio
            self._start_time = datetime.now()
            
            # Paso 1: Inicialización (0%)
            await self._update_progress(query, 0, f"Backtesting {name}", "Inicializando sistema...")
            await asyncio.sleep(1)
            
            # Calcular fechas
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Paso 2: Creando motor (10%)
            await self._update_progress(query, 10, f"Backtesting {name}", "Configurando motor de backtesting...")
            await asyncio.sleep(0.5)
            
            # Crear motor de backtesting
            backtest_engine = BacktestingEngine(
                mt5_connector=self.trading_engine.mt5,  # Usar .mt5 en lugar de .mt5_connector
                analyzer=self.trading_engine.analyzer,
                initial_balance=10000.0
            )
            
            # Paso 3: Obteniendo datos (25%)
            await self._update_progress(query, 25, f"Backtesting {name}", "Obteniendo datos históricos...")
            await asyncio.sleep(1)
            
            # Paso 4: Preparando análisis (40%)
            await self._update_progress(query, 40, f"Backtesting {name}", "Preparando análisis multi-timeframe...")
            await asyncio.sleep(0.5)
            
            # Paso 5: Ejecutando backtesting (60%)
            await self._update_progress(query, 60, f"Backtesting {name}", "Simulando trades históricos...")
            
            # Ejecutar backtesting
            results = await backtest_engine.run_backtest(
                start_date=start_date,
                end_date=end_date,
                symbol="EURUSD",
                timeframe="M15"
            )
            
            # Paso 6: Calculando métricas (80%)
            await self._update_progress(query, 80, f"Backtesting {name}", "Calculando métricas de rendimiento...")
            await asyncio.sleep(0.5)
            
            # Paso 7: Generando reporte (95%)
            await self._update_progress(query, 95, f"Backtesting {name}", "Generando reporte final...")
            
            # Generar reporte
            summary_report = self.report_generator.generate_summary_report(results)
            
            # Paso 8: Completado (100%)
            await self._update_progress(query, 100, f"Backtesting {name}", "¡Completado exitosamente!")
            await asyncio.sleep(1)
            
            # Guardar resultados para acceso posterior
            self._save_last_results(results)
            
            # Mostrar resultados
            keyboard = [
                [InlineKeyboardButton("📊 Reporte Detallado", callback_data="backtest_detailed")],
                [InlineKeyboardButton("📈 Análisis de Trades", callback_data="backtest_trades")],
                [InlineKeyboardButton("🔄 Nuevo Backtesting", callback_data="backtesting_menu")],
                [InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                summary_report,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            # Mostrar error con barra de progreso
            error_msg = str(e)
            
            # Mensajes de error más específicos
            if "mt5_connector" in error_msg:
                error_msg = "Error de configuración del conector MT5"
            elif "BacktestingEngine" in error_msg:
                error_msg = "Error inicializando motor de backtesting"
            elif "get_rates" in error_msg:
                error_msg = "Error obteniendo datos históricos de MT5"
            elif "insufficient" in error_msg.lower():
                error_msg = "Datos históricos insuficientes para el período"
            
            await self._update_progress_error(query, f"Backtesting {name}", error_msg)
            await asyncio.sleep(2)
            
            error_text = f"""
❌ **Error en Backtesting {name}**

No se pudo completar el backtesting.

🔧 **Error**: {str(e)[:200]}...

💡 **Posibles causas**:
• Datos históricos insuficientes
• Error de conexión con MT5
• Problema en análisis de datos

🔄 **Solución**: Intenta nuevamente o usa un período más corto.

⏱️ **Tiempo transcurrido**: {self._get_elapsed_time()}
            """
            
            keyboard = [
                [InlineKeyboardButton("🔄 Intentar Nuevamente", callback_data=f"backtest_{'quick' if days == 30 else 'monthly' if days == 90 else 'quarterly'}")],
                [InlineKeyboardButton("🔙 Volver al Menú", callback_data="backtesting_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                error_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            self.logger.error(f"Error en backtesting: {e}")
    
    async def show_detailed_report(self, query):
        """Mostrar reporte detallado del último backtesting"""
        
        try:
            results = self._load_last_results()
            
            if results is None:
                await query.edit_message_text(
                    "❌ No hay resultados de backtesting disponibles.\n\nEjecuta un backtesting primero.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔄 Ejecutar Backtesting", callback_data="backtesting_menu")
                    ]])
                )
                return
            
            # Generar reporte detallado (primera parte)
            detailed_report = self.report_generator.generate_detailed_report(results)
            
            # Telegram tiene límite de 4096 caracteres, dividir si es necesario
            if len(detailed_report) > 4000:
                # Enviar en partes
                parts = self._split_message(detailed_report, 4000)
                
                for i, part in enumerate(parts):
                    if i == len(parts) - 1:  # Última parte
                        keyboard = [
                            [InlineKeyboardButton("📊 Análisis de Trades", callback_data="backtest_trades")],
                            [InlineKeyboardButton("🔄 Nuevo Backtesting", callback_data="backtesting_menu")],
                            [InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                    else:
                        reply_markup = None
                    
                    if i == 0:
                        await query.edit_message_text(part, parse_mode='Markdown', reply_markup=reply_markup)
                    else:
                        await query.message.reply_text(part, parse_mode='Markdown', reply_markup=reply_markup)
            else:
                keyboard = [
                    [InlineKeyboardButton("📊 Análisis de Trades", callback_data="backtest_trades")],
                    [InlineKeyboardButton("🔄 Nuevo Backtesting", callback_data="backtesting_menu")],
                    [InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    detailed_report,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            self.logger.error(f"Error mostrando reporte detallado: {e}")
            await query.edit_message_text(
                f"❌ Error generando reporte detallado: {str(e)[:100]}...",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Volver", callback_data="backtesting_menu")
                ]])
            )
    
    async def show_trades_analysis(self, query):
        """Mostrar análisis detallado de trades"""
        
        try:
            results = self._load_last_results()
            
            if results is None or not results.trades:
                await query.edit_message_text(
                    "❌ No hay trades para analizar.\n\nEjecuta un backtesting primero.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔄 Ejecutar Backtesting", callback_data="backtesting_menu")
                    ]])
                )
                return
            
            # Mostrar primeros 10 trades
            trades_text = "🎯 **ANÁLISIS DE TRADES**\n\n"
            
            for i, trade in enumerate(results.trades[:10]):
                duration = (trade.exit_time - trade.entry_time).total_seconds() / 3600
                pips = abs(trade.exit_price - trade.entry_price) / 0.0001
                
                emoji = "✅" if trade.profit_loss > 0 else "❌"
                trades_text += f"""
{emoji} **Trade #{i+1}** ({trade.signal})
📅 {trade.entry_time.strftime('%m/%d %H:%M')} → {trade.exit_time.strftime('%m/%d %H:%M')}
💰 P&L: ${trade.profit_loss:+.2f} | 📊 {pips:.1f} pips
⏱️ Duración: {duration:.1f}h | 🎯 Confianza: {trade.confidence:.0f}%
                """
            
            if len(results.trades) > 10:
                trades_text += f"\n... y {len(results.trades) - 10} trades más"
            
            # Estadísticas adicionales
            winning_trades = [t for t in results.trades if t.profit_loss > 0]
            losing_trades = [t for t in results.trades if t.profit_loss < 0]
            
            if winning_trades:
                avg_win = sum(t.profit_loss for t in winning_trades) / len(winning_trades)
                trades_text += f"\n📈 **Ganancia Promedio**: ${avg_win:.2f}"
            
            if losing_trades:
                avg_loss = sum(t.profit_loss for t in losing_trades) / len(losing_trades)
                trades_text += f"\n📉 **Pérdida Promedio**: ${avg_loss:.2f}"
            
            keyboard = [
                [InlineKeyboardButton("📊 Reporte Completo", callback_data="backtest_detailed")],
                [InlineKeyboardButton("🔄 Nuevo Backtesting", callback_data="backtesting_menu")],
                [InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                trades_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            self.logger.error(f"Error mostrando análisis de trades: {e}")
            await query.edit_message_text(
                f"❌ Error en análisis de trades: {str(e)[:100]}...",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Volver", callback_data="backtesting_menu")
                ]])
            )
    
    def _save_last_results(self, results):
        """Guardar últimos resultados para acceso posterior"""
        try:
            # En una implementación completa, esto se guardaría en base de datos
            # Por ahora, usar variable de instancia
            self.last_results = results
        except Exception as e:
            self.logger.error(f"Error guardando resultados: {e}")
    
    def _load_last_results(self):
        """Cargar últimos resultados"""
        return getattr(self, 'last_results', None)
    
    async def _update_progress(self, query, percentage: int, title: str, current_step: str):
        """Actualizar barra de progreso visual"""
        
        # Crear barra de progreso simple
        filled_blocks = int(percentage / 5)  # 20 bloques total (100% / 5 = 20)
        empty_blocks = 20 - filled_blocks
        
        # Usar caracteres más compatibles
        progress_bar = "■" * filled_blocks + "□" * empty_blocks
        
        # Determinar emoji de estado
        if percentage == 0:
            status_emoji = "🔄"
        elif percentage < 100:
            status_emoji = "⚡"
        else:
            status_emoji = "✅"
        
        # Limpiar texto para evitar errores de parsing
        clean_title = self._clean_markdown_text(title)
        clean_step = self._clean_markdown_text(current_step)
        
        # Crear mensaje de progreso
        progress_text = f"""
🔬 *{clean_title}*

{status_emoji} *Progreso*: {percentage}%
{progress_bar}

📋 *Estado Actual*: {clean_step}

⏱️ *Tiempo transcurrido*: {self._get_elapsed_time()}
🎯 *Proceso*: Análisis Multi-Timeframe con ML

💡 *Información*:
• Simulación realista con spreads
• Cálculo de métricas profesionales  
• Generación de reportes detallados
        """
        
        try:
            await query.edit_message_text(
                progress_text.strip(),
                parse_mode='Markdown'
            )
        except Exception as e:
            # Si falla Markdown, intentar sin formato
            try:
                plain_text = progress_text.replace('*', '').replace('_', '')
                await query.edit_message_text(plain_text.strip())
            except Exception as e2:
                self.logger.warning(f"Error actualizando progreso: {e2}")
    
    def _get_elapsed_time(self) -> str:
        """Obtener tiempo transcurrido desde inicio"""
        if not hasattr(self, '_start_time'):
            self._start_time = datetime.now()
        
        elapsed = datetime.now() - self._start_time
        seconds = int(elapsed.total_seconds())
        
        if seconds < 60:
            return f"{seconds}s"
        else:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds}s"
    
    async def _update_progress_error(self, query, title: str, error_message: str):
        """Mostrar error con barra de progreso"""
        
        # Barra de progreso de error
        progress_bar = "■" * 10 + "X" + "□" * 9
        
        # Limpiar textos
        clean_title = self._clean_markdown_text(title)
        clean_error = self._clean_markdown_text(error_message[:100])
        
        error_text = f"""
🔬 *{clean_title}*

❌ *Error*: Proceso interrumpido
{progress_bar}

📋 *Problema*: {clean_error}

⏱️ *Tiempo transcurrido*: {self._get_elapsed_time()}
🎯 *Estado*: Proceso detenido por error

💡 *Información*:
• El backtesting se detuvo inesperadamente
• Revisa la conexión y datos disponibles
• Intenta con un período más corto
        """
        
        try:
            await query.edit_message_text(
                error_text.strip(),
                parse_mode='Markdown'
            )
        except Exception as e:
            # Fallback sin formato
            try:
                plain_text = error_text.replace('*', '').replace('_', '')
                await query.edit_message_text(plain_text.strip())
            except Exception as e2:
                self.logger.warning(f"Error mostrando error de progreso: {e2}")
    
    def _clean_markdown_text(self, text: str) -> str:
        """Limpiar texto para evitar errores de parsing Markdown"""
        if not text:
            return ""
        
        # Remover o escapar caracteres problemáticos
        cleaned = str(text)
        
        # Escapar caracteres especiales de Markdown
        special_chars = ['*', '_', '`', '[', ']', '(', ')', '~', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        for char in special_chars:
            if char in cleaned:
                cleaned = cleaned.replace(char, f'\\{char}')
        
        # Remover caracteres de control y no imprimibles
        cleaned = ''.join(char for char in cleaned if ord(char) >= 32 or char in ['\n', '\t'])
        
        # Limitar longitud
        if len(cleaned) > 200:
            cleaned = cleaned[:200] + "..."
        
        return cleaned
    
    def _split_message(self, message: str, max_length: int) -> List[str]:
        """Dividir mensaje largo en partes"""
        parts = []
        current_part = ""
        
        lines = message.split('\n')
        
        for line in lines:
            if len(current_part + line + '\n') <= max_length:
                current_part += line + '\n'
            else:
                if current_part:
                    parts.append(current_part.strip())
                current_part = line + '\n'
        
        if current_part:
            parts.append(current_part.strip())
        
        return parts

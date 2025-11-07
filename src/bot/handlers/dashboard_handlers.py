"""
Dashboard Handlers para métricas de rendimiento avanzadas
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DashboardHandlers:
    def __init__(self, trading_engine):
        self.trading_engine = trading_engine
    
    async def show_performance_dashboard(self, query):
        """Mostrar dashboard principal de rendimiento"""
        try:
            # Obtener datos de rendimiento
            balance_info = await self.trading_engine.get_balance()
            positions = await self.trading_engine.get_open_positions()
            trade_history = await self.trading_engine.get_trade_history()
            
            if not balance_info:
                await query.edit_message_text("❌ No se pudo obtener información de la cuenta")
                return
            
            # Calcular métricas básicas
            balance = balance_info.get('balance', 0)
            equity = balance_info.get('equity', 0)
            margin = balance_info.get('margin', 0)
            free_margin = balance_info.get('margin_free', 0)
            margin_level = balance_info.get('margin_level', 0)
            
            # Calcular P&L no realizado
            unrealized_pnl = sum(pos.get('profit', 0) for pos in positions) if positions else 0
            
            # Calcular métricas de trading
            total_trades = len(trade_history) if trade_history else 0
            winning_trades = sum(1 for trade in trade_history if trade.get('profit', 0) > 0) if trade_history else 0
            losing_trades = total_trades - winning_trades
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Calcular P&L total
            total_pnl = sum(trade.get('profit', 0) for trade in trade_history) if trade_history else 0
            avg_win = sum(trade.get('profit', 0) for trade in trade_history if trade.get('profit', 0) > 0) / winning_trades if winning_trades > 0 else 0
            avg_loss = sum(trade.get('profit', 0) for trade in trade_history if trade.get('profit', 0) < 0) / losing_trades if losing_trades > 0 else 0
            
            # Calcular ratio riesgo/beneficio
            if avg_loss != 0:
                risk_reward_ratio = abs(avg_win / avg_loss)
                ratio_text = f"{risk_reward_ratio:.2f}"
            else:
                ratio_text = "N/A"
            
            # Crear mensaje del dashboard
            dashboard_text = f"""📊 **DASHBOARD DE RENDIMIENTO**

💰 **INFORMACIÓN DE CUENTA:**
• Balance: ${balance:,.2f}
• Equity: ${equity:,.2f}
• Margen Usado: ${margin:,.2f}
• Margen Libre: ${free_margin:,.2f}
• Nivel de Margen: {margin_level:.1f}%

📈 **P&L Y POSICIONES:**
• P&L No Realizado: ${unrealized_pnl:+.2f}
• P&L Total Histórico: ${total_pnl:+.2f}
• Posiciones Abiertas: {len(positions) if positions else 0}

📊 **ESTADÍSTICAS DE TRADING:**
• Total Trades: {total_trades}
• Trades Ganadores: {winning_trades}
• Trades Perdedores: {losing_trades}
• Win Rate: {win_rate:.1f}%

💡 **MÉTRICAS AVANZADAS:**
• Ganancia Promedio: ${avg_win:.2f}
• Pérdida Promedio: ${avg_loss:.2f}
• Ratio Riesgo/Beneficio: {ratio_text}

🕐 **Actualizado**: {datetime.now().strftime('%H:%M:%S')}"""

            # Crear botones del dashboard (uno debajo del otro)
            keyboard = [
                [InlineKeyboardButton("📈 Rendimiento Diario", callback_data="dashboard_daily")],
                [InlineKeyboardButton("📊 Rendimiento Semanal", callback_data="dashboard_weekly")],
                [InlineKeyboardButton("🎯 Por Estrategia", callback_data="dashboard_strategy")],
                [InlineKeyboardButton("💱 Por Par de Divisas", callback_data="dashboard_pairs")],
                [InlineKeyboardButton("📉 Análisis de Drawdown", callback_data="dashboard_drawdown")],
                [InlineKeyboardButton("⚡ Métricas en Tiempo Real", callback_data="dashboard_realtime")],
                [InlineKeyboardButton("🔄 Actualizar Dashboard", callback_data="dashboard_main")],
                [InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_main")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(dashboard_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error mostrando dashboard: {e}")
            await query.edit_message_text(f"❌ Error mostrando dashboard: {str(e)}")
    
    async def show_daily_performance(self, query):
        """Mostrar rendimiento diario"""
        try:
            # Obtener trades del día actual
            today = datetime.now().date()
            trade_history = await self.trading_engine.get_trade_history()
            
            daily_trades = []
            if trade_history:
                for trade in trade_history:
                    trade_date = trade.get('time')
                    if isinstance(trade_date, datetime) and trade_date.date() == today:
                        daily_trades.append(trade)
            
            # Calcular métricas diarias
            daily_pnl = sum(trade.get('profit', 0) for trade in daily_trades)
            daily_trades_count = len(daily_trades)
            daily_wins = sum(1 for trade in daily_trades if trade.get('profit', 0) > 0)
            daily_losses = daily_trades_count - daily_wins
            daily_win_rate = (daily_wins / daily_trades_count * 100) if daily_trades_count > 0 else 0
            
            # Obtener balance inicial del día (aproximado)
            balance_info = await self.trading_engine.get_balance()
            current_balance = balance_info.get('balance', 0) if balance_info else 0
            initial_balance = current_balance - daily_pnl
            
            # Calcular retorno diario evitando división por cero
            if initial_balance > 0:
                daily_return = (daily_pnl / initial_balance * 100)
            elif current_balance > 0:
                daily_return = (daily_pnl / current_balance * 100)
            else:
                daily_return = 0
            
            daily_text = f"""📈 **RENDIMIENTO DIARIO**
📅 {today.strftime('%d/%m/%Y')}

💰 **RESUMEN FINANCIERO:**
• P&L del Día: ${daily_pnl:+.2f}
• Retorno Diario: {daily_return:+.2f}%
• Balance Inicial: ${initial_balance:,.2f}
• Balance Actual: ${current_balance:,.2f}

📊 **ACTIVIDAD DE TRADING:**
• Trades Ejecutados: {daily_trades_count}
• Trades Ganadores: {daily_wins}
• Trades Perdedores: {daily_losses}
• Win Rate Diario: {daily_win_rate:.1f}%

🎯 **ANÁLISIS:**
• Mejor Trade: ${max([trade.get('profit', 0) for trade in daily_trades], default=0):.2f}
• Peor Trade: ${min([trade.get('profit', 0) for trade in daily_trades], default=0):.2f}
• Promedio por Trade: ${(daily_pnl/daily_trades_count) if daily_trades_count > 0 else 0:.2f}

🕐 **Actualizado**: {datetime.now().strftime('%H:%M:%S')}"""

            keyboard = [
                [InlineKeyboardButton("🔄 Actualizar", callback_data="dashboard_daily")],
                [InlineKeyboardButton("🔙 Volver al Dashboard", callback_data="dashboard_main")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(daily_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error mostrando rendimiento diario: {e}")
            await query.edit_message_text(f"❌ Error: {str(e)}")
    
    async def show_weekly_performance(self, query):
        """Mostrar rendimiento semanal"""
        try:
            # Obtener trades de la semana actual
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
            
            trade_history = await self.trading_engine.get_trade_history()
            weekly_trades = []
            
            if trade_history:
                for trade in trade_history:
                    trade_date = trade.get('time')
                    if isinstance(trade_date, datetime) and trade_date.date() >= week_start:
                        weekly_trades.append(trade)
            
            # Calcular métricas semanales
            weekly_pnl = sum(trade.get('profit', 0) for trade in weekly_trades)
            weekly_trades_count = len(weekly_trades)
            weekly_wins = sum(1 for trade in weekly_trades if trade.get('profit', 0) > 0)
            weekly_losses = weekly_trades_count - weekly_wins
            weekly_win_rate = (weekly_wins / weekly_trades_count * 100) if weekly_trades_count > 0 else 0
            
            # Calcular rendimiento por día
            daily_breakdown = {}
            for i in range(7):
                day = week_start + timedelta(days=i)
                day_trades = [t for t in weekly_trades if isinstance(t.get('time'), datetime) and t.get('time').date() == day]
                day_pnl = sum(t.get('profit', 0) for t in day_trades)
                daily_breakdown[day.strftime('%a %d/%m')] = {'pnl': day_pnl, 'trades': len(day_trades)}
            
            weekly_text = f"""📊 **RENDIMIENTO SEMANAL**
📅 Semana del {week_start.strftime('%d/%m')} al {today.strftime('%d/%m/%Y')}

💰 **RESUMEN SEMANAL:**
• P&L de la Semana: ${weekly_pnl:+.2f}
• Trades Totales: {weekly_trades_count}
• Win Rate Semanal: {weekly_win_rate:.1f}%

📈 **DESGLOSE DIARIO:**"""

            for day, data in daily_breakdown.items():
                if data['trades'] > 0:
                    weekly_text += f"\n• {day}: ${data['pnl']:+.2f} ({data['trades']} trades)"
                else:
                    weekly_text += f"\n• {day}: Sin actividad"
            
            weekly_text += f"""

🎯 **MÉTRICAS SEMANALES:**
• Mejor Día: ${max([d['pnl'] for d in daily_breakdown.values()]):+.2f}
• Peor Día: ${min([d['pnl'] for d in daily_breakdown.values()]):+.2f}
• Promedio Diario: ${weekly_pnl/7:.2f}

🕐 **Actualizado**: {datetime.now().strftime('%H:%M:%S')}"""

            keyboard = [
                [InlineKeyboardButton("🔄 Actualizar", callback_data="dashboard_weekly")],
                [InlineKeyboardButton("🔙 Volver al Dashboard", callback_data="dashboard_main")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(weekly_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error mostrando rendimiento semanal: {e}")
            await query.edit_message_text(f"❌ Error: {str(e)}")
    
    async def show_strategy_performance(self, query):
        """Mostrar rendimiento por estrategia"""
        try:
            trade_history = await self.trading_engine.get_trade_history()
            
            if not trade_history:
                await query.edit_message_text("📊 No hay datos de trades para analizar por estrategia")
                return
            
            # Agrupar trades por estrategia
            strategy_stats = {}
            
            for trade in trade_history:
                comment = trade.get('comment', '')
                strategy = 'unknown'
                
                # Extraer estrategia del comentario
                if 'momentum' in comment.lower():
                    strategy = 'Momentum Breakout'
                elif 'scalping' in comment.lower():
                    strategy = 'Super Scalping'
                elif 'reversion' in comment.lower():
                    strategy = 'Mean Reversion'
                elif 'swing' in comment.lower():
                    strategy = 'Swing Trading'
                
                if strategy not in strategy_stats:
                    strategy_stats[strategy] = {'trades': [], 'pnl': 0, 'wins': 0}
                
                strategy_stats[strategy]['trades'].append(trade)
                strategy_stats[strategy]['pnl'] += trade.get('profit', 0)
                if trade.get('profit', 0) > 0:
                    strategy_stats[strategy]['wins'] += 1
            
            strategy_text = """🎯 **RENDIMIENTO POR ESTRATEGIA**

"""
            
            for strategy, stats in strategy_stats.items():
                total_trades = len(stats['trades'])
                win_rate = (stats['wins'] / total_trades * 100) if total_trades > 0 else 0
                avg_pnl = stats['pnl'] / total_trades if total_trades > 0 else 0
                
                strategy_text += f"""📊 **{strategy}:**
• Trades: {total_trades}
• P&L: ${stats['pnl']:+.2f}
• Win Rate: {win_rate:.1f}%
• Promedio: ${avg_pnl:+.2f}

"""
            
            strategy_text += f"🕐 **Actualizado**: {datetime.now().strftime('%H:%M:%S')}"
            
            keyboard = [
                [InlineKeyboardButton("🔄 Actualizar", callback_data="dashboard_strategy")],
                [InlineKeyboardButton("🔙 Volver al Dashboard", callback_data="dashboard_main")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(strategy_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error mostrando rendimiento por estrategia: {e}")
            await query.edit_message_text(f"❌ Error: {str(e)}")
    
    async def show_pairs_performance(self, query):
        """Mostrar rendimiento por par de divisas"""
        try:
            trade_history = await self.trading_engine.get_trade_history()
            
            if not trade_history:
                await query.edit_message_text("📊 No hay datos de trades para analizar por pares")
                return
            
            # Agrupar trades por par
            pairs_stats = {}
            
            for trade in trade_history:
                symbol = trade.get('symbol', 'UNKNOWN')
                
                if symbol not in pairs_stats:
                    pairs_stats[symbol] = {'trades': [], 'pnl': 0, 'wins': 0}
                
                pairs_stats[symbol]['trades'].append(trade)
                pairs_stats[symbol]['pnl'] += trade.get('profit', 0)
                if trade.get('profit', 0) > 0:
                    pairs_stats[symbol]['wins'] += 1
            
            pairs_text = """💱 **RENDIMIENTO POR PAR DE DIVISAS**

"""
            
            # Ordenar por P&L descendente
            sorted_pairs = sorted(pairs_stats.items(), key=lambda x: x[1]['pnl'], reverse=True)
            
            for symbol, stats in sorted_pairs:
                total_trades = len(stats['trades'])
                win_rate = (stats['wins'] / total_trades * 100) if total_trades > 0 else 0
                avg_pnl = stats['pnl'] / total_trades if total_trades > 0 else 0
                
                pairs_text += f"""💱 **{symbol}:**
• Trades: {total_trades}
• P&L: ${stats['pnl']:+.2f}
• Win Rate: {win_rate:.1f}%
• Promedio: ${avg_pnl:+.2f}

"""
            
            pairs_text += f"🕐 **Actualizado**: {datetime.now().strftime('%H:%M:%S')}"
            
            keyboard = [
                [InlineKeyboardButton("🔄 Actualizar", callback_data="dashboard_pairs")],
                [InlineKeyboardButton("🔙 Volver al Dashboard", callback_data="dashboard_main")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(pairs_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error mostrando rendimiento por pares: {e}")
            await query.edit_message_text(f"❌ Error: {str(e)}")
    
    async def show_drawdown_analysis(self, query):
        """Mostrar análisis de drawdown"""
        try:
            trade_history = await self.trading_engine.get_trade_history()
            balance_info = await self.trading_engine.get_balance()
            
            if not trade_history:
                await query.edit_message_text("📉 No hay datos suficientes para análisis de drawdown")
                return
            
            current_balance = balance_info.get('balance', 0) if balance_info else 0
            
            # Calcular drawdown histórico
            running_balance = current_balance
            peak_balance = current_balance
            max_drawdown = 0
            max_drawdown_pct = 0
            current_drawdown = 0
            current_drawdown_pct = 0
            drawdown_periods = []
            
            # Simular balance histórico (desde el más reciente hacia atrás)
            sorted_trades = sorted(trade_history, key=lambda x: x.get('time', datetime.now()), reverse=True)
            
            for trade in sorted_trades:
                profit = trade.get('profit', 0)
                running_balance -= profit  # Restar porque vamos hacia atrás
                
                # Actualizar peak si es necesario
                if running_balance > peak_balance:
                    peak_balance = running_balance
                
                # Calcular drawdown actual
                drawdown = peak_balance - running_balance
                drawdown_pct = (drawdown / peak_balance * 100) if peak_balance > 0 else 0
                
                # Actualizar máximo drawdown
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                    max_drawdown_pct = drawdown_pct
                
                # Registrar período de drawdown
                if drawdown > 0:
                    drawdown_periods.append({
                        'amount': drawdown,
                        'percentage': drawdown_pct,
                        'date': trade.get('time', datetime.now())
                    })
            
            # Calcular drawdown actual
            current_drawdown = peak_balance - current_balance
            current_drawdown_pct = (current_drawdown / peak_balance * 100) if peak_balance > 0 else 0
            
            # Estadísticas de drawdown
            avg_drawdown = sum(d['amount'] for d in drawdown_periods) / len(drawdown_periods) if drawdown_periods else 0
            drawdown_frequency = len([d for d in drawdown_periods if d['amount'] > 100])  # Drawdowns > $100
            
            # Calcular tiempo de recuperación promedio
            recovery_periods = []
            in_drawdown = False
            drawdown_start = None
            
            for i, trade in enumerate(sorted_trades):
                if not in_drawdown and drawdown_periods and i < len(drawdown_periods):
                    in_drawdown = True
                    drawdown_start = trade.get('time', datetime.now())
                elif in_drawdown and (i >= len(drawdown_periods) or drawdown_periods[i]['amount'] == 0):
                    if drawdown_start:
                        recovery_time = trade.get('time', datetime.now()) - drawdown_start
                        recovery_periods.append(recovery_time.days)
                    in_drawdown = False
            
            avg_recovery_days = sum(recovery_periods) / len(recovery_periods) if recovery_periods else 0
            
            # Evaluar nivel de riesgo
            if max_drawdown_pct < 5:
                risk_level = "🟢 BAJO"
            elif max_drawdown_pct < 15:
                risk_level = "🟡 MODERADO"
            elif max_drawdown_pct < 30:
                risk_level = "🟠 ALTO"
            else:
                risk_level = "🔴 CRÍTICO"
            
            drawdown_text = f"""📉 **ANÁLISIS DE DRAWDOWN**

💰 **DRAWDOWN ACTUAL:**
• Drawdown Actual: ${current_drawdown:.2f}
• Porcentaje Actual: {current_drawdown_pct:.2f}%
• Balance Pico: ${peak_balance:,.2f}
• Balance Actual: ${current_balance:,.2f}

📊 **DRAWDOWN HISTÓRICO:**
• Máximo Drawdown: ${max_drawdown:.2f}
• Máximo Porcentaje: {max_drawdown_pct:.2f}%
• Drawdown Promedio: ${avg_drawdown:.2f}
• Frecuencia (>$100): {drawdown_frequency} veces

⏱️ **ANÁLISIS TEMPORAL:**
• Tiempo Recuperación Promedio: {avg_recovery_days:.1f} días
• Períodos de Drawdown: {len(drawdown_periods)}
• Último Drawdown: {drawdown_periods[0]['date'].strftime('%d/%m/%Y %H:%M') if drawdown_periods else 'N/A'}

🎯 **EVALUACIÓN DE RIESGO:**
• Nivel de Riesgo: {risk_level}
• Tolerancia Recomendada: {max_drawdown_pct * 1.5:.1f}%
• Capital de Seguridad: ${max_drawdown * 2:.2f}

💡 **RECOMENDACIONES:**
• Mantener reserva de ${max_drawdown * 3:.2f}
• Revisar gestión de riesgo si drawdown > 20%
• Considerar reducir tamaño de posición

🕐 **Actualizado**: {datetime.now().strftime('%H:%M:%S')}"""

            keyboard = [
                [InlineKeyboardButton("🔄 Actualizar Análisis", callback_data="dashboard_drawdown")],
                [InlineKeyboardButton("📊 Ver Gráfico Histórico", callback_data="drawdown_chart")],
                [InlineKeyboardButton("🔙 Volver al Dashboard", callback_data="dashboard_main")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(drawdown_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error mostrando análisis de drawdown: {e}")
            await query.edit_message_text(f"❌ Error en análisis de drawdown: {str(e)}")
    
    async def show_realtime_metrics(self, query):
        """Mostrar métricas en tiempo real"""
        try:
            # Obtener datos en tiempo real
            balance_info = await self.trading_engine.get_balance()
            positions = await self.trading_engine.get_open_positions()
            market_analysis = await self.trading_engine.get_market_analysis()
            
            if not balance_info:
                await query.edit_message_text("❌ No se pueden obtener métricas en tiempo real")
                return
            
            # Métricas financieras en tiempo real
            balance = balance_info.get('balance', 0)
            equity = balance_info.get('equity', 0)
            floating_pl = balance_info.get('floating_pl', 0)
            margin = balance_info.get('margin', 0)
            free_margin = balance_info.get('margin_free', 0)
            margin_level = balance_info.get('margin_level', 0)
            
            # Análisis de posiciones abiertas
            total_positions = len(positions) if positions else 0
            buy_positions = sum(1 for pos in positions if pos.get('type') == 0) if positions else 0
            sell_positions = sum(1 for pos in positions if pos.get('type') == 1) if positions else 0
            
            # P&L por posición
            profitable_positions = sum(1 for pos in positions if pos.get('profit', 0) > 0) if positions else 0
            losing_positions = sum(1 for pos in positions if pos.get('profit', 0) < 0) if positions else 0
            
            # Volumen total
            total_volume = sum(pos.get('volume', 0) for pos in positions) if positions else 0
            
            # Exposición por divisa
            currency_exposure = {}
            if positions:
                for pos in positions:
                    symbol = pos.get('symbol', '')
                    volume = pos.get('volume', 0)
                    pos_type = pos.get('type', 0)
                    
                    if len(symbol) >= 6:
                        base_currency = symbol[:3]
                        quote_currency = symbol[3:6]
                        
                        if pos_type == 0:  # BUY
                            currency_exposure[base_currency] = currency_exposure.get(base_currency, 0) + volume
                            currency_exposure[quote_currency] = currency_exposure.get(quote_currency, 0) - volume
                        else:  # SELL
                            currency_exposure[base_currency] = currency_exposure.get(base_currency, 0) - volume
                            currency_exposure[quote_currency] = currency_exposure.get(quote_currency, 0) + volume
            
            # Métricas de rendimiento en tiempo real
            daily_return = ((equity - balance) / balance * 100) if balance > 0 else 0
            risk_percentage = (margin / equity * 100) if equity > 0 else 0
            
            # Estado del mercado
            market_status = "🟢 ACTIVO" if datetime.now().weekday() < 5 else "🔴 CERRADO"
            
            # Análisis de volatilidad actual
            volatility = "BAJA"
            if market_analysis:
                atr = market_analysis.get('atr', 0)
                if atr > 0.001:
                    volatility = "ALTA"
                elif atr > 0.0005:
                    volatility = "MEDIA"
            
            # Crear mensaje de métricas en tiempo real
            realtime_text = f"""⚡ **MÉTRICAS EN TIEMPO REAL**

💰 **ESTADO FINANCIERO ACTUAL:**
• Balance: ${balance:,.2f}
• Equity: ${equity:,.2f}
• P&L Flotante: ${floating_pl:+.2f}
• Retorno del Día: {daily_return:+.2f}%

📊 **GESTIÓN DE RIESGO:**
• Margen Usado: ${margin:,.2f}
• Margen Libre: ${free_margin:,.2f}
• Nivel de Margen: {margin_level:.1f}%
• Riesgo Actual: {risk_percentage:.1f}%

🎯 **POSICIONES ACTIVAS:**
• Total Posiciones: {total_positions}
• Posiciones BUY: {buy_positions}
• Posiciones SELL: {sell_positions}
• Volumen Total: {total_volume:.2f} lotes

📈 **ANÁLISIS DE POSICIONES:**
• Posiciones Rentables: {profitable_positions}
• Posiciones en Pérdida: {losing_positions}
• Ratio Éxito: {(profitable_positions/total_positions*100) if total_positions > 0 else 0:.1f}%

💱 **EXPOSICIÓN POR DIVISA:**"""

            # Agregar exposición por divisa
            if currency_exposure:
                for currency, exposure in sorted(currency_exposure.items(), key=lambda x: abs(x[1]), reverse=True)[:5]:
                    if abs(exposure) > 0.01:  # Solo mostrar exposiciones significativas
                        realtime_text += f"\n• {currency}: {exposure:+.2f} lotes"
            else:
                realtime_text += "\n• Sin exposición activa"

            realtime_text += f"""

🌍 **ESTADO DEL MERCADO:**
• Estado: {market_status}
• Volatilidad: {volatility}
• Sesión: {'Europea' if 7 <= datetime.now().hour <= 16 else 'Americana' if 13 <= datetime.now().hour <= 22 else 'Asiática'}

🕐 **Actualizado**: {datetime.now().strftime('%H:%M:%S')}
📡 **Próxima actualización**: {(datetime.now() + timedelta(seconds=30)).strftime('%H:%M:%S')}"""

            keyboard = [
                [InlineKeyboardButton("🔄 Actualizar Métricas", callback_data="dashboard_realtime")],
                [InlineKeyboardButton("📊 Auto-Refresh (30s)", callback_data="realtime_autorefresh")],
                [InlineKeyboardButton("🎯 Ver Posiciones Detalle", callback_data="positions_detail")],
                [InlineKeyboardButton("🔙 Volver al Dashboard", callback_data="dashboard_main")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(realtime_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error mostrando métricas en tiempo real: {e}")
            await query.edit_message_text(f"❌ Error en métricas en tiempo real: {str(e)}")

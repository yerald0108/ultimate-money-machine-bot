"""
Generador de Reportes de Backtesting
Crea reportes detallados de rendimiento y análisis
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List
import json
import logging
from .backtesting_engine import BacktestResults, BacktestTrade

class BacktestReportGenerator:
    """Generador de reportes de backtesting"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_summary_report(self, results: BacktestResults) -> str:
        """Generar reporte resumen para Telegram"""
        
        duration = (results.end_date - results.start_date).days
        roi = ((results.final_balance - results.initial_balance) / results.initial_balance) * 100
        
        # Emoji para el rendimiento
        performance_emoji = "🟢" if roi > 0 else "🔴" if roi < 0 else "🟡"
        
        report = f"""
📊 **REPORTE DE BACKTESTING**

📅 **Período**: {results.start_date.strftime('%Y-%m-%d')} a {results.end_date.strftime('%Y-%m-%d')}
⏱️ **Duración**: {duration} días

💰 **RENDIMIENTO**:
{performance_emoji} **ROI**: {roi:+.2f}%
💵 **Balance Inicial**: ${results.initial_balance:,.2f}
💵 **Balance Final**: ${results.final_balance:,.2f}
💹 **Ganancia Total**: ${results.total_profit:+,.2f}

📈 **ESTADÍSTICAS DE TRADING**:
🎯 **Total Trades**: {results.total_trades}
✅ **Trades Ganadores**: {results.winning_trades}
❌ **Trades Perdedores**: {results.losing_trades}
📊 **Win Rate**: {results.win_rate:.1f}%
⚡ **Profit Factor**: {results.profit_factor:.2f}
💸 **Drawdown Máximo**: {results.max_drawdown:.1f}%

📊 **MÉTRICAS AVANZADAS**:
📈 **Sharpe Ratio**: {results.sharpe_ratio:.2f}
💰 **Trade Promedio**: ${results.average_trade:+.2f}
🎯 **Trades/Día**: {results.total_trades/max(duration, 1):.1f}

🏆 **CALIFICACIÓN**: {self._get_performance_grade(results)}
        """
        
        return report.strip()
    
    def generate_detailed_report(self, results: BacktestResults) -> str:
        """Generar reporte detallado"""
        
        # Análisis por meses
        monthly_analysis = self._analyze_monthly_performance(results)
        
        # Análisis de trades
        trade_analysis = self._analyze_trades(results.trades)
        
        # Análisis de drawdown
        drawdown_analysis = self._analyze_drawdown(results)
        
        report = f"""
📊 **REPORTE DETALLADO DE BACKTESTING**

{self.generate_summary_report(results)}

📅 **ANÁLISIS MENSUAL**:
{monthly_analysis}

🎯 **ANÁLISIS DE TRADES**:
{trade_analysis}

📉 **ANÁLISIS DE DRAWDOWN**:
{drawdown_analysis}

📈 **RECOMENDACIONES**:
{self._generate_recommendations(results)}
        """
        
        return report.strip()
    
    def _analyze_monthly_performance(self, results: BacktestResults) -> str:
        """Analizar rendimiento mensual"""
        
        if not results.monthly_returns:
            return "• No hay datos mensuales disponibles"
        
        analysis = []
        
        for month, profit in results.monthly_returns.items():
            roi_month = (profit / results.initial_balance) * 100
            emoji = "🟢" if profit > 0 else "🔴" if profit < 0 else "🟡"
            analysis.append(f"• {month}: {emoji} ${profit:+.2f} ({roi_month:+.1f}%)")
        
        # Mejor y peor mes
        if results.monthly_returns:
            best_month = max(results.monthly_returns.items(), key=lambda x: x[1])
            worst_month = min(results.monthly_returns.items(), key=lambda x: x[1])
            
            analysis.append(f"\n🏆 **Mejor mes**: {best_month[0]} (${best_month[1]:+.2f})")
            analysis.append(f"📉 **Peor mes**: {worst_month[0]} (${worst_month[1]:+.2f})")
        
        return "\n".join(analysis)
    
    def _analyze_trades(self, trades: List[BacktestTrade]) -> str:
        """Analizar patrones de trades"""
        
        if not trades:
            return "• No hay trades para analizar"
        
        analysis = []
        
        # Análisis por señal
        buy_trades = [t for t in trades if t.signal == 'BUY']
        sell_trades = [t for t in trades if t.signal == 'SELL']
        
        if buy_trades:
            buy_profit = sum(t.profit_loss for t in buy_trades)
            buy_win_rate = len([t for t in buy_trades if t.profit_loss > 0]) / len(buy_trades) * 100
            analysis.append(f"📈 **BUY Trades**: {len(buy_trades)} | Win Rate: {buy_win_rate:.1f}% | P&L: ${buy_profit:+.2f}")
        
        if sell_trades:
            sell_profit = sum(t.profit_loss for t in sell_trades)
            sell_win_rate = len([t for t in sell_trades if t.profit_loss > 0]) / len(sell_trades) * 100
            analysis.append(f"📉 **SELL Trades**: {len(sell_trades)} | Win Rate: {sell_win_rate:.1f}% | P&L: ${sell_profit:+.2f}")
        
        # Mejor y peor trade
        best_trade = max(trades, key=lambda x: x.profit_loss)
        worst_trade = min(trades, key=lambda x: x.profit_loss)
        
        analysis.append(f"\n🏆 **Mejor trade**: ${best_trade.profit_loss:+.2f} ({best_trade.signal})")
        analysis.append(f"📉 **Peor trade**: ${worst_trade.profit_loss:+.2f} ({worst_trade.signal})")
        
        # Análisis de confianza
        high_conf_trades = [t for t in trades if t.confidence >= 70]
        if high_conf_trades:
            high_conf_profit = sum(t.profit_loss for t in high_conf_trades)
            high_conf_win_rate = len([t for t in high_conf_trades if t.profit_loss > 0]) / len(high_conf_trades) * 100
            analysis.append(f"\n🎯 **Alta Confianza (≥70%)**: {len(high_conf_trades)} trades | Win Rate: {high_conf_win_rate:.1f}% | P&L: ${high_conf_profit:+.2f}")
        
        return "\n".join(analysis)
    
    def _analyze_drawdown(self, results: BacktestResults) -> str:
        """Analizar drawdown y recuperación"""
        
        analysis = []
        
        analysis.append(f"📉 **Drawdown Máximo**: {results.max_drawdown:.1f}%")
        
        # Calcular períodos de drawdown
        equity_curve = results.equity_curve
        peak = equity_curve[0]
        in_drawdown = False
        drawdown_periods = []
        current_drawdown_start = 0
        
        for i, balance in enumerate(equity_curve):
            if balance > peak:
                if in_drawdown:
                    # Fin del drawdown
                    drawdown_periods.append(i - current_drawdown_start)
                    in_drawdown = False
                peak = balance
            elif balance < peak and not in_drawdown:
                # Inicio del drawdown
                in_drawdown = True
                current_drawdown_start = i
        
        if drawdown_periods:
            avg_recovery = np.mean(drawdown_periods)
            analysis.append(f"⏱️ **Recuperación Promedio**: {avg_recovery:.0f} trades")
            analysis.append(f"📊 **Períodos de Drawdown**: {len(drawdown_periods)}")
        
        return "\n".join(analysis)
    
    def _generate_recommendations(self, results: BacktestResults) -> str:
        """Generar recomendaciones basadas en resultados"""
        
        recommendations = []
        
        # Recomendaciones basadas en win rate
        if results.win_rate < 50:
            recommendations.append("⚠️ Win rate bajo - considera ajustar filtros de entrada")
        elif results.win_rate > 70:
            recommendations.append("✅ Excelente win rate - estrategia sólida")
        
        # Recomendaciones basadas en profit factor
        if results.profit_factor < 1.2:
            recommendations.append("⚠️ Profit factor bajo - optimizar gestión de riesgo")
        elif results.profit_factor > 2.0:
            recommendations.append("✅ Excelente profit factor - estrategia rentable")
        
        # Recomendaciones basadas en drawdown
        if results.max_drawdown > 20:
            recommendations.append("⚠️ Drawdown alto - reducir tamaño de posición")
        elif results.max_drawdown < 10:
            recommendations.append("✅ Drawdown controlado - gestión de riesgo adecuada")
        
        # Recomendaciones basadas en Sharpe ratio
        if results.sharpe_ratio < 1.0:
            recommendations.append("⚠️ Sharpe ratio bajo - mejorar consistencia")
        elif results.sharpe_ratio > 2.0:
            recommendations.append("✅ Excelente Sharpe ratio - retornos consistentes")
        
        # Recomendaciones generales
        if results.total_trades < 30:
            recommendations.append("📊 Pocos trades - considera período más largo")
        
        if not recommendations:
            recommendations.append("✅ Rendimiento balanceado - continuar con estrategia actual")
        
        return "\n".join(recommendations)
    
    def _get_performance_grade(self, results: BacktestResults) -> str:
        """Calcular calificación de rendimiento"""
        
        score = 0
        
        # Win Rate (30%)
        if results.win_rate >= 70:
            score += 30
        elif results.win_rate >= 60:
            score += 25
        elif results.win_rate >= 50:
            score += 20
        elif results.win_rate >= 40:
            score += 15
        
        # Profit Factor (25%)
        if results.profit_factor >= 2.0:
            score += 25
        elif results.profit_factor >= 1.5:
            score += 20
        elif results.profit_factor >= 1.2:
            score += 15
        elif results.profit_factor >= 1.0:
            score += 10
        
        # ROI (25%)
        roi = ((results.final_balance - results.initial_balance) / results.initial_balance) * 100
        if roi >= 20:
            score += 25
        elif roi >= 15:
            score += 20
        elif roi >= 10:
            score += 15
        elif roi >= 5:
            score += 10
        elif roi > 0:
            score += 5
        
        # Drawdown (20%)
        if results.max_drawdown <= 5:
            score += 20
        elif results.max_drawdown <= 10:
            score += 15
        elif results.max_drawdown <= 15:
            score += 10
        elif results.max_drawdown <= 20:
            score += 5
        
        # Calificación
        if score >= 85:
            return "🏆 EXCELENTE (A+)"
        elif score >= 75:
            return "🥇 MUY BUENO (A)"
        elif score >= 65:
            return "🥈 BUENO (B)"
        elif score >= 55:
            return "🥉 REGULAR (C)"
        elif score >= 45:
            return "⚠️ DEFICIENTE (D)"
        else:
            return "❌ MALO (F)"
    
    def save_detailed_report(self, results: BacktestResults, filename: str = None) -> str:
        """Guardar reporte detallado en archivo"""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backtest_report_{timestamp}.txt"
        
        report = self.generate_detailed_report(results)
        
        try:
            with open(f"reports/{filename}", 'w', encoding='utf-8') as f:
                f.write(report)
            
            self.logger.info(f"Reporte guardado: reports/{filename}")
            return f"reports/{filename}"
            
        except Exception as e:
            self.logger.error(f"Error guardando reporte: {e}")
            return None
    
    def export_trades_csv(self, results: BacktestResults, filename: str = None) -> str:
        """Exportar trades a CSV"""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backtest_trades_{timestamp}.csv"
        
        try:
            # Convertir trades a DataFrame
            trades_data = []
            for trade in results.trades:
                trades_data.append({
                    'entry_time': trade.entry_time,
                    'exit_time': trade.exit_time,
                    'signal': trade.signal,
                    'entry_price': trade.entry_price,
                    'exit_price': trade.exit_price,
                    'lot_size': trade.lot_size,
                    'profit_loss': trade.profit_loss,
                    'confidence': trade.confidence,
                    'duration_hours': (trade.exit_time - trade.entry_time).total_seconds() / 3600,
                    'reason': trade.reason
                })
            
            df = pd.DataFrame(trades_data)
            df.to_csv(f"reports/{filename}", index=False)
            
            self.logger.info(f"Trades exportados: reports/{filename}")
            return f"reports/{filename}"
            
        except Exception as e:
            self.logger.error(f"Error exportando trades: {e}")
            return None

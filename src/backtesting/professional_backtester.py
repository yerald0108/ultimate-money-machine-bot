"""
Sistema de Backtesting Profesional
Implementa métricas rigurosas y validación fuera de muestra
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
import json
# import matplotlib.pyplot as plt
# import seaborn as sns
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class Trade:
    """Estructura de un trade individual"""
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    direction: str  # 'long' or 'short'
    size: float
    pnl: float
    pnl_pct: float
    commission: float
    strategy: str
    confidence: float
    max_adverse_excursion: float  # MAE
    max_favorable_excursion: float  # MFE

@dataclass
class BacktestResults:
    """Resultados completos del backtesting"""
    trades: List[Trade]
    equity_curve: pd.Series
    metrics: Dict
    period_stats: Dict
    drawdown_analysis: Dict
    monthly_returns: pd.Series
    strategy_performance: Dict

class ProfessionalBacktester:
    """Backtester profesional con métricas institucionales"""
    
    def __init__(self, initial_capital: float = 10000, commission: float = 0.0001):
        self.initial_capital = initial_capital
        self.commission = commission  # 0.01% por trade
        self.trades = []
        self.equity_curve = []
        self.daily_returns = []
        
    def run_backtest(self, 
                    strategy_func, 
                    data: pd.DataFrame, 
                    start_date: str = None, 
                    end_date: str = None,
                    out_of_sample_pct: float = 0.2) -> BacktestResults:
        """
        Ejecutar backtesting riguroso con validación fuera de muestra
        
        Args:
            strategy_func: Función de estrategia que retorna señales
            data: DataFrame con datos OHLCV
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)
            out_of_sample_pct: % de datos para validación fuera de muestra
        """
        logger.info("🎯 Iniciando backtesting profesional...")
        
        # Preparar datos
        if start_date:
            data = data[data.index >= start_date]
        if end_date:
            data = data[data.index <= end_date]
        
        # Dividir en in-sample y out-of-sample
        split_point = int(len(data) * (1 - out_of_sample_pct))
        in_sample_data = data.iloc[:split_point]
        out_of_sample_data = data.iloc[split_point:]
        
        logger.info(f"📊 Datos in-sample: {len(in_sample_data)} períodos")
        logger.info(f"📊 Datos out-of-sample: {len(out_of_sample_data)} períodos")
        
        # Ejecutar backtesting en ambos períodos
        in_sample_results = self._execute_backtest(strategy_func, in_sample_data, "In-Sample")
        out_of_sample_results = self._execute_backtest(strategy_func, out_of_sample_data, "Out-of-Sample")
        
        # Combinar resultados
        all_trades = in_sample_results.trades + out_of_sample_results.trades
        
        # Calcular métricas completas
        metrics = self._calculate_comprehensive_metrics(all_trades, data)
        
        # Análisis de drawdown
        drawdown_analysis = self._analyze_drawdowns(all_trades)
        
        # Rendimientos mensuales
        monthly_returns = self._calculate_monthly_returns(all_trades)
        
        # Performance por estrategia
        strategy_performance = self._analyze_strategy_performance(all_trades)
        
        # Estadísticas por período
        period_stats = {
            'in_sample': self._calculate_period_stats(in_sample_results.trades),
            'out_of_sample': self._calculate_period_stats(out_of_sample_results.trades),
            'validation': self._validate_out_of_sample_performance(
                in_sample_results.trades, 
                out_of_sample_results.trades
            )
        }
        
        # Curva de equity
        equity_curve = self._build_equity_curve(all_trades)
        
        results = BacktestResults(
            trades=all_trades,
            equity_curve=equity_curve,
            metrics=metrics,
            period_stats=period_stats,
            drawdown_analysis=drawdown_analysis,
            monthly_returns=monthly_returns,
            strategy_performance=strategy_performance
        )
        
        logger.info("✅ Backtesting completado")
        return results
    
    def _execute_backtest(self, strategy_func, data: pd.DataFrame, period_name: str):
        """Ejecutar backtesting en un período específico"""
        logger.info(f"🔄 Ejecutando backtesting {period_name}...")
        
        trades = []
        position = None
        capital = self.initial_capital
        
        for i in range(1, len(data)):
            current_bar = data.iloc[i]
            previous_bars = data.iloc[:i+1]
            
            # Obtener señal de la estrategia
            signal = strategy_func(previous_bars, i)
            
            if signal is None:
                continue
                
            # Procesar señal
            if signal['action'] in ['buy', 'sell'] and position is None:
                # Abrir posición
                position = self._open_position(signal, current_bar, capital)
                
            elif signal['action'] == 'close' and position is not None:
                # Cerrar posición
                trade = self._close_position(position, current_bar)
                if trade:
                    trades.append(trade)
                    capital += trade.pnl
                position = None
        
        # Cerrar posición abierta al final
        if position is not None:
            final_bar = data.iloc[-1]
            trade = self._close_position(position, final_bar)
            if trade:
                trades.append(trade)
        
        return BacktestResults(
            trades=trades,
            equity_curve=pd.Series(),
            metrics={},
            period_stats={},
            drawdown_analysis={},
            monthly_returns=pd.Series(),
            strategy_performance={}
        )
    
    def _open_position(self, signal: Dict, bar: pd.Series, capital: float) -> Dict:
        """Abrir una posición"""
        direction = 'long' if signal['action'] == 'buy' else 'short'
        entry_price = bar['close']
        
        # Calcular tamaño de posición basado en riesgo
        risk_amount = capital * signal.get('risk_pct', 0.02)  # 2% default
        stop_loss_pips = signal.get('stop_loss_pips', 20)
        pip_value = 0.0001  # Para EUR/USD
        
        position_size = risk_amount / (stop_loss_pips * pip_value * 100000)  # Lotes estándar
        position_size = max(0.01, min(position_size, 10.0))  # Límites
        
        return {
            'direction': direction,
            'entry_time': bar.name,
            'entry_price': entry_price,
            'size': position_size,
            'stop_loss': signal.get('stop_loss'),
            'take_profit': signal.get('take_profit'),
            'strategy': signal.get('strategy', 'unknown'),
            'confidence': signal.get('confidence', 50),
            'max_adverse': 0,
            'max_favorable': 0
        }
    
    def _close_position(self, position: Dict, bar: pd.Series) -> Optional[Trade]:
        """Cerrar una posición y calcular P&L"""
        try:
            exit_price = bar['close']
            exit_time = bar.name
            
            # Calcular P&L
            if position['direction'] == 'long':
                pnl_pips = (exit_price - position['entry_price']) / 0.0001
            else:
                pnl_pips = (position['entry_price'] - exit_price) / 0.0001
            
            pnl_usd = pnl_pips * position['size'] * 10  # $10 por pip por lote
            commission_cost = position['size'] * 100000 * self.commission * 2  # Entrada y salida
            net_pnl = pnl_usd - commission_cost
            
            pnl_pct = net_pnl / self.initial_capital * 100
            
            return Trade(
                entry_time=position['entry_time'],
                exit_time=exit_time,
                entry_price=position['entry_price'],
                exit_price=exit_price,
                direction=position['direction'],
                size=position['size'],
                pnl=net_pnl,
                pnl_pct=pnl_pct,
                commission=commission_cost,
                strategy=position['strategy'],
                confidence=position['confidence'],
                max_adverse_excursion=position['max_adverse'],
                max_favorable_excursion=position['max_favorable']
            )
        except Exception as e:
            logger.error(f"Error cerrando posición: {e}")
            return None
    
    def _calculate_comprehensive_metrics(self, trades: List[Trade], data: pd.DataFrame) -> Dict:
        """Calcular métricas completas de rendimiento"""
        if not trades:
            return {}
        
        # Métricas básicas
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl < 0]
        
        win_rate = len(winning_trades) / total_trades * 100
        
        total_pnl = sum(t.pnl for t in trades)
        total_return_pct = total_pnl / self.initial_capital * 100
        
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        # Métricas de riesgo
        returns = [t.pnl_pct for t in trades]
        
        # Sharpe Ratio (anualizado)
        if len(returns) > 1:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = (avg_return * 252) / (std_return * np.sqrt(252)) if std_return > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Sortino Ratio
        negative_returns = [r for r in returns if r < 0]
        if negative_returns:
            downside_deviation = np.std(negative_returns)
            sortino_ratio = (np.mean(returns) * 252) / (downside_deviation * np.sqrt(252))
        else:
            sortino_ratio = float('inf') if np.mean(returns) > 0 else 0
        
        # Maximum Drawdown
        equity_curve = self._build_equity_curve(trades)
        running_max = equity_curve.expanding().max()
        drawdown = (equity_curve - running_max) / running_max * 100
        max_drawdown = drawdown.min()
        
        # Calmar Ratio
        calmar_ratio = total_return_pct / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Expectancy
        expectancy = (win_rate/100 * avg_win) + ((1-win_rate/100) * avg_loss)
        
        return {
            'total_trades': total_trades,
            'win_rate': round(win_rate, 2),
            'total_return_pct': round(total_return_pct, 2),
            'total_pnl': round(total_pnl, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'sortino_ratio': round(sortino_ratio, 2),
            'max_drawdown': round(max_drawdown, 2),
            'calmar_ratio': round(calmar_ratio, 2),
            'expectancy': round(expectancy, 2),
            'largest_win': round(max([t.pnl for t in trades]), 2),
            'largest_loss': round(min([t.pnl for t in trades]), 2),
            'avg_trade_duration': self._calculate_avg_duration(trades),
            'trades_per_month': self._calculate_trade_frequency(trades)
        }
    
    def _analyze_drawdowns(self, trades: List[Trade]) -> Dict:
        """Análisis detallado de drawdowns"""
        equity_curve = self._build_equity_curve(trades)
        
        # Calcular drawdowns
        running_max = equity_curve.expanding().max()
        drawdown = (equity_curve - running_max) / running_max * 100
        
        # Encontrar períodos de drawdown
        drawdown_periods = []
        in_drawdown = False
        start_dd = None
        
        for date, dd in drawdown.items():
            if dd < -0.1 and not in_drawdown:  # Inicio de drawdown (>0.1%)
                in_drawdown = True
                start_dd = date
            elif dd >= -0.01 and in_drawdown:  # Fin de drawdown
                in_drawdown = False
                if start_dd:
                    duration = (date - start_dd).days
                    max_dd = drawdown[start_dd:date].min()
                    drawdown_periods.append({
                        'start': start_dd,
                        'end': date,
                        'duration_days': duration,
                        'max_drawdown': max_dd
                    })
        
        return {
            'max_drawdown': round(drawdown.min(), 2),
            'avg_drawdown': round(drawdown[drawdown < 0].mean(), 2),
            'drawdown_periods': len(drawdown_periods),
            'longest_drawdown_days': max([dd['duration_days'] for dd in drawdown_periods]) if drawdown_periods else 0,
            'recovery_factor': abs(equity_curve.iloc[-1] - self.initial_capital) / abs(drawdown.min() * self.initial_capital / 100) if drawdown.min() < 0 else float('inf')
        }
    
    def _calculate_monthly_returns(self, trades: List[Trade]) -> pd.Series:
        """Calcular rendimientos mensuales"""
        if not trades:
            return pd.Series()
        
        # Agrupar trades por mes
        monthly_pnl = {}
        for trade in trades:
            month_key = trade.exit_time.strftime('%Y-%m')
            if month_key not in monthly_pnl:
                monthly_pnl[month_key] = 0
            monthly_pnl[month_key] += trade.pnl
        
        # Convertir a porcentajes
        monthly_returns = {}
        for month, pnl in monthly_pnl.items():
            monthly_returns[month] = pnl / self.initial_capital * 100
        
        return pd.Series(monthly_returns)
    
    def _analyze_strategy_performance(self, trades: List[Trade]) -> Dict:
        """Analizar performance por estrategia"""
        strategy_stats = {}
        
        for trade in trades:
            strategy = trade.strategy
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {
                    'trades': [],
                    'total_pnl': 0,
                    'wins': 0,
                    'losses': 0
                }
            
            strategy_stats[strategy]['trades'].append(trade)
            strategy_stats[strategy]['total_pnl'] += trade.pnl
            
            if trade.pnl > 0:
                strategy_stats[strategy]['wins'] += 1
            else:
                strategy_stats[strategy]['losses'] += 1
        
        # Calcular métricas por estrategia
        for strategy, stats in strategy_stats.items():
            total_trades = len(stats['trades'])
            win_rate = stats['wins'] / total_trades * 100 if total_trades > 0 else 0
            avg_pnl = stats['total_pnl'] / total_trades if total_trades > 0 else 0
            
            strategy_stats[strategy].update({
                'total_trades': total_trades,
                'win_rate': round(win_rate, 2),
                'avg_pnl_per_trade': round(avg_pnl, 2),
                'total_return_pct': round(stats['total_pnl'] / self.initial_capital * 100, 2)
            })
        
        return strategy_stats
    
    def _calculate_period_stats(self, trades: List[Trade]) -> Dict:
        """Calcular estadísticas para un período específico"""
        if not trades:
            return {}
        
        total_pnl = sum(t.pnl for t in trades)
        win_rate = len([t for t in trades if t.pnl > 0]) / len(trades) * 100
        
        return {
            'trades': len(trades),
            'total_pnl': round(total_pnl, 2),
            'win_rate': round(win_rate, 2),
            'return_pct': round(total_pnl / self.initial_capital * 100, 2)
        }
    
    def _validate_out_of_sample_performance(self, in_sample_trades: List[Trade], out_sample_trades: List[Trade]) -> Dict:
        """Validar que el rendimiento out-of-sample sea consistente"""
        if not in_sample_trades or not out_sample_trades:
            return {'validation': 'insufficient_data'}
        
        # Métricas in-sample
        in_win_rate = len([t for t in in_sample_trades if t.pnl > 0]) / len(in_sample_trades) * 100
        in_avg_pnl = sum(t.pnl for t in in_sample_trades) / len(in_sample_trades)
        
        # Métricas out-of-sample
        out_win_rate = len([t for t in out_sample_trades if t.pnl > 0]) / len(out_sample_trades) * 100
        out_avg_pnl = sum(t.pnl for t in out_sample_trades) / len(out_sample_trades)
        
        # Validación
        win_rate_degradation = (in_win_rate - out_win_rate) / in_win_rate * 100 if in_win_rate > 0 else 0
        pnl_degradation = (in_avg_pnl - out_avg_pnl) / abs(in_avg_pnl) * 100 if in_avg_pnl != 0 else 0
        
        # Criterios de validación
        is_valid = (
            win_rate_degradation < 20 and  # Win rate no debe degradar más del 20%
            pnl_degradation < 30 and       # PnL promedio no debe degradar más del 30%
            out_win_rate > 45              # Win rate out-of-sample debe ser > 45%
        )
        
        return {
            'is_valid': is_valid,
            'win_rate_degradation': round(win_rate_degradation, 2),
            'pnl_degradation': round(pnl_degradation, 2),
            'recommendation': 'APPROVED' if is_valid else 'NEEDS_OPTIMIZATION'
        }
    
    def _build_equity_curve(self, trades: List[Trade]) -> pd.Series:
        """Construir curva de equity"""
        if not trades:
            return pd.Series([self.initial_capital])
        
        equity_data = {}
        running_balance = self.initial_capital
        
        for trade in trades:
            running_balance += trade.pnl
            equity_data[trade.exit_time] = running_balance
        
        return pd.Series(equity_data)
    
    def _calculate_avg_duration(self, trades: List[Trade]) -> str:
        """Calcular duración promedio de trades"""
        if not trades:
            return "0 hours"
        
        durations = [(t.exit_time - t.entry_time).total_seconds() / 3600 for t in trades]
        avg_hours = np.mean(durations)
        
        if avg_hours < 1:
            return f"{int(avg_hours * 60)} minutes"
        elif avg_hours < 24:
            return f"{avg_hours:.1f} hours"
        else:
            return f"{avg_hours/24:.1f} days"
    
    def _calculate_trade_frequency(self, trades: List[Trade]) -> float:
        """Calcular frecuencia de trades por mes"""
        if not trades or len(trades) < 2:
            return 0
        
        first_trade = min(trades, key=lambda t: t.entry_time)
        last_trade = max(trades, key=lambda t: t.exit_time)
        
        duration_months = (last_trade.exit_time - first_trade.entry_time).days / 30.44
        
        return round(len(trades) / duration_months, 1) if duration_months > 0 else 0
    
    def generate_report(self, results: BacktestResults, save_path: str = None) -> str:
        """Generar reporte completo de backtesting"""
        report = []
        
        report.append("=" * 80)
        report.append("📊 REPORTE DE BACKTESTING PROFESIONAL")
        report.append("=" * 80)
        
        # Métricas principales
        metrics = results.metrics
        report.append("\n🎯 MÉTRICAS PRINCIPALES:")
        report.append(f"Total de Trades: {metrics.get('total_trades', 0)}")
        report.append(f"Win Rate: {metrics.get('win_rate', 0)}%")
        report.append(f"Retorno Total: {metrics.get('total_return_pct', 0)}%")
        report.append(f"P&L Total: ${metrics.get('total_pnl', 0):,.2f}")
        
        # Métricas de riesgo
        report.append("\n🛡️ MÉTRICAS DE RIESGO:")
        report.append(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0)}")
        report.append(f"Sortino Ratio: {metrics.get('sortino_ratio', 0)}")
        report.append(f"Max Drawdown: {metrics.get('max_drawdown', 0)}%")
        report.append(f"Calmar Ratio: {metrics.get('calmar_ratio', 0)}")
        
        # Validación out-of-sample
        validation = results.period_stats.get('validation', {})
        report.append("\n✅ VALIDACIÓN OUT-OF-SAMPLE:")
        report.append(f"Estado: {validation.get('recommendation', 'N/A')}")
        report.append(f"Degradación Win Rate: {validation.get('win_rate_degradation', 0)}%")
        report.append(f"Degradación P&L: {validation.get('pnl_degradation', 0)}%")
        
        # Performance por estrategia
        report.append("\n📈 PERFORMANCE POR ESTRATEGIA:")
        for strategy, stats in results.strategy_performance.items():
            report.append(f"{strategy}: {stats['total_trades']} trades, "
                         f"{stats['win_rate']}% win rate, "
                         f"{stats['total_return_pct']}% return")
        
        report_text = "\n".join(report)
        
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            logger.info(f"📄 Reporte guardado en: {save_path}")
        
        return report_text

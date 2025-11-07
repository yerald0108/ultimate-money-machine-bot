"""
Módulo de Backtesting Automático
Validación de estrategias con datos históricos
"""

from .backtesting_engine import BacktestingEngine, BacktestResults, BacktestTrade
from .report_generator import BacktestReportGenerator

__all__ = [
    'BacktestingEngine',
    'BacktestResults', 
    'BacktestTrade',
    'BacktestReportGenerator'
]

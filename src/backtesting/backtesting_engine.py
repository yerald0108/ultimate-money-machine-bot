"""
Motor de Backtesting Automático
Simula trades históricos para validar estrategias
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
import asyncio

@dataclass
class BacktestTrade:
    """Representa un trade en el backtesting"""
    entry_time: datetime
    exit_time: datetime
    signal: str  # BUY/SELL
    entry_price: float
    exit_price: float
    lot_size: float
    profit_loss: float
    confidence: float
    timeframe_analysis: Dict
    reason: str

@dataclass
class BacktestResults:
    """Resultados completos del backtesting"""
    start_date: datetime
    end_date: datetime
    initial_balance: float
    final_balance: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    max_drawdown: float
    sharpe_ratio: float
    total_profit: float
    average_trade: float
    trades: List[BacktestTrade]
    equity_curve: List[float]
    monthly_returns: Dict[str, float]

class BacktestingEngine:
    """Motor principal de backtesting"""
    
    def __init__(self, mt5_connector, analyzer, initial_balance: float = 10000.0):
        self.mt5_connector = mt5_connector
        self.analyzer = analyzer
        self.initial_balance = initial_balance
        self.logger = logging.getLogger(__name__)
        
        # Configuración de backtesting
        self.spread = 0.00015  # 1.5 pips para EUR/USD
        self.commission = 0.0  # Sin comisión para demo
        self.slippage = 0.00005  # 0.5 pips de slippage
        
    async def run_backtest(
        self, 
        start_date: datetime, 
        end_date: datetime,
        symbol: str = "EURUSD",
        timeframe: str = "M15"
    ) -> BacktestResults:
        """Ejecutar backtesting completo"""
        
        self.logger.info(f"🔄 Iniciando backtesting: {start_date} a {end_date}")
        
        # Obtener datos históricos
        historical_data = await self._get_historical_data(symbol, timeframe, start_date, end_date)
        
        if historical_data is None or len(historical_data) < 100:
            raise ValueError("Datos históricos insuficientes para backtesting")
        
        # Simular trading
        trades = await self._simulate_trading(historical_data, symbol)
        
        # Calcular métricas
        results = self._calculate_metrics(trades, start_date, end_date)
        
        self.logger.info(f"✅ Backtesting completado: {len(trades)} trades simulados")
        
        return results
    
    async def _get_historical_data(
        self, 
        symbol: str, 
        timeframe: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """Obtener datos históricos para backtesting"""
        
        try:
            # Usar el conector MT5 para obtener datos históricos
            data = await self.mt5_connector.get_rates_timeframe(
                timeframe_str=timeframe,
                count=10000  # Máximo disponible
            )
            
            if data is None or data.empty:
                return None
            
            # El DataFrame ya tiene 'time' como índice, necesitamos resetear para filtrar
            data_reset = data.reset_index()
            
            # Filtrar por fechas
            mask = (data_reset['time'] >= start_date) & (data_reset['time'] <= end_date)
            filtered_data = data_reset.loc[mask].copy()
            
            # Resetear índice
            filtered_data.reset_index(drop=True, inplace=True)
            
            self.logger.info(f"📊 Datos históricos: {len(filtered_data)} períodos de {timeframe}")
            
            return filtered_data
            
        except Exception as e:
            self.logger.error(f"Error obteniendo datos históricos: {e}")
            return None
    
    async def _simulate_trading(self, data: pd.DataFrame, symbol: str) -> List[BacktestTrade]:
        """Simular trading con datos históricos"""
        
        trades = []
        current_balance = self.initial_balance
        open_position = None
        
        self.logger.info("🎯 Iniciando simulación de trading...")
        
        # Procesar cada período
        for i in range(100, len(data)):  # Empezar después de 100 períodos para indicadores
            
            current_time = data.iloc[i]['time']
            current_data = data.iloc[:i+1].copy()
            
            try:
                # Analizar con Multi-Timeframe (simulado)
                should_trade, signal, trade_info = await self._simulate_analysis(current_data, i)
                
                # Si hay posición abierta, verificar cierre
                if open_position:
                    exit_signal = await self._check_exit_conditions(
                        open_position, current_data.iloc[i], trade_info
                    )
                    
                    if exit_signal:
                        # Cerrar posición
                        trade = await self._close_position(open_position, current_data.iloc[i])
                        if trade:
                            trades.append(trade)
                            current_balance += trade.profit_loss
                        open_position = None
                
                # Si no hay posición y hay señal, abrir nueva
                elif should_trade and signal in ['BUY', 'SELL']:
                    open_position = await self._open_position(
                        signal, current_data.iloc[i], trade_info, current_balance
                    )
            
            except Exception as e:
                self.logger.warning(f"Error en simulación en índice {i}: {e}")
                continue
        
        # Cerrar posición abierta al final
        if open_position:
            trade = await self._close_position(open_position, data.iloc[-1])
            if trade:
                trades.append(trade)
        
        self.logger.info(f"📈 Simulación completada: {len(trades)} trades ejecutados")
        
        return trades
    
    async def _simulate_analysis(self, data: pd.DataFrame, current_index: int) -> Tuple[bool, str, Dict]:
        """Simular análisis Multi-Timeframe para backtesting"""
        
        try:
            # Usar el analizador existente con datos históricos
            # Nota: Esto es una simulación, en realidad necesitaríamos adaptar el analizador
            
            # Por ahora, usar análisis técnico básico
            close_prices = data['close'].values
            
            if len(close_prices) < 50:
                return False, 'HOLD', {'confidence': 0, 'reason': 'Datos insuficientes'}
            
            # Calcular indicadores básicos
            sma_20 = np.mean(close_prices[-20:])
            sma_50 = np.mean(close_prices[-50:])
            current_price = close_prices[-1]
            
            # RSI simple
            gains = []
            losses = []
            for i in range(1, min(15, len(close_prices))):
                diff = close_prices[-i] - close_prices[-i-1]
                if diff > 0:
                    gains.append(diff)
                else:
                    losses.append(abs(diff))
            
            avg_gain = np.mean(gains) if gains else 0
            avg_loss = np.mean(losses) if losses else 0.0001
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            # Lógica de señales
            confidence = 0
            signal = 'HOLD'
            reasons = []
            
            # Señal alcista
            if (current_price > sma_20 > sma_50 and 
                rsi > 30 and rsi < 70):
                signal = 'BUY'
                confidence = 65
                reasons.append('Tendencia alcista')
            
            # Señal bajista
            elif (current_price < sma_20 < sma_50 and 
                  rsi > 30 and rsi < 70):
                signal = 'SELL'
                confidence = 65
                reasons.append('Tendencia bajista')
            
            # Filtros adicionales
            if confidence > 0:
                # Volatilidad
                volatility = np.std(close_prices[-20:])
                if volatility > 0.002:  # Alta volatilidad
                    confidence -= 15
                    reasons.append('Alta volatilidad')
                
                # Momentum
                momentum = (current_price - close_prices[-10]) / close_prices[-10]
                if abs(momentum) > 0.001:
                    confidence += 10
                    reasons.append('Buen momentum')
            
            trade_info = {
                'confidence': confidence,
                'reasons': reasons,
                'rsi': rsi,
                'sma_20': sma_20,
                'sma_50': sma_50,
                'volatility': volatility if 'volatility' in locals() else 0,
                'analysis_type': 'Backtesting Simulation'
            }
            
            should_trade = confidence >= 60  # Umbral para operar
            
            return should_trade, signal, trade_info
            
        except Exception as e:
            self.logger.error(f"Error en análisis simulado: {e}")
            return False, 'HOLD', {'confidence': 0, 'reason': f'Error: {e}'}
    
    async def _open_position(
        self, 
        signal: str, 
        current_bar: pd.Series, 
        trade_info: Dict, 
        current_balance: float
    ) -> Dict:
        """Abrir posición en backtesting"""
        
        entry_price = current_bar['close']
        
        # Aplicar spread
        if signal == 'BUY':
            entry_price += self.spread / 2
        else:
            entry_price -= self.spread / 2
        
        # Calcular tamaño de posición (2% de riesgo)
        risk_per_trade = current_balance * 0.02
        stop_loss_pips = 20  # 20 pips de SL
        pip_value = 1  # Para EUR/USD
        lot_size = risk_per_trade / (stop_loss_pips * pip_value)
        lot_size = min(lot_size, 1.0)  # Máximo 1 lote
        lot_size = max(lot_size, 0.01)  # Mínimo 0.01 lotes
        
        position = {
            'signal': signal,
            'entry_time': current_bar['time'],
            'entry_price': entry_price,
            'lot_size': lot_size,
            'confidence': trade_info['confidence'],
            'trade_info': trade_info,
            'stop_loss': entry_price - (stop_loss_pips * 0.0001) if signal == 'BUY' else entry_price + (stop_loss_pips * 0.0001),
            'take_profit': entry_price + (40 * 0.0001) if signal == 'BUY' else entry_price - (40 * 0.0001)  # 40 pips TP
        }
        
        return position
    
    async def _check_exit_conditions(
        self, 
        position: Dict, 
        current_bar: pd.Series, 
        trade_info: Dict
    ) -> bool:
        """Verificar condiciones de salida"""
        
        current_price = current_bar['close']
        
        # Stop Loss
        if position['signal'] == 'BUY' and current_price <= position['stop_loss']:
            return True
        elif position['signal'] == 'SELL' and current_price >= position['stop_loss']:
            return True
        
        # Take Profit
        if position['signal'] == 'BUY' and current_price >= position['take_profit']:
            return True
        elif position['signal'] == 'SELL' and current_price <= position['take_profit']:
            return True
        
        # Tiempo máximo (24 horas)
        time_diff = current_bar['time'] - position['entry_time']
        if time_diff.total_seconds() > 24 * 3600:
            return True
        
        return False
    
    async def _close_position(self, position: Dict, current_bar: pd.Series) -> Optional[BacktestTrade]:
        """Cerrar posición en backtesting"""
        
        try:
            exit_price = current_bar['close']
            
            # Aplicar spread y slippage
            if position['signal'] == 'BUY':
                exit_price -= (self.spread / 2 + self.slippage)
            else:
                exit_price += (self.spread / 2 + self.slippage)
            
            # Calcular P&L
            if position['signal'] == 'BUY':
                pips = (exit_price - position['entry_price']) / 0.0001
            else:
                pips = (position['entry_price'] - exit_price) / 0.0001
            
            profit_loss = pips * position['lot_size'] * 1.0  # $1 por pip por lote estándar
            
            trade = BacktestTrade(
                entry_time=position['entry_time'],
                exit_time=current_bar['time'],
                signal=position['signal'],
                entry_price=position['entry_price'],
                exit_price=exit_price,
                lot_size=position['lot_size'],
                profit_loss=profit_loss,
                confidence=position['confidence'],
                timeframe_analysis=position['trade_info'],
                reason=f"P&L: ${profit_loss:.2f} ({pips:.1f} pips)"
            )
            
            return trade
            
        except Exception as e:
            self.logger.error(f"Error cerrando posición: {e}")
            return None
    
    def _calculate_metrics(
        self, 
        trades: List[BacktestTrade], 
        start_date: datetime, 
        end_date: datetime
    ) -> BacktestResults:
        """Calcular métricas de rendimiento"""
        
        if not trades:
            return BacktestResults(
                start_date=start_date,
                end_date=end_date,
                initial_balance=self.initial_balance,
                final_balance=self.initial_balance,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                profit_factor=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                total_profit=0.0,
                average_trade=0.0,
                trades=[],
                equity_curve=[self.initial_balance],
                monthly_returns={}
            )
        
        # Métricas básicas
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.profit_loss > 0])
        losing_trades = len([t for t in trades if t.profit_loss < 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        # P&L
        total_profit = sum(t.profit_loss for t in trades)
        final_balance = self.initial_balance + total_profit
        average_trade = total_profit / total_trades if total_trades > 0 else 0
        
        # Profit Factor
        gross_profit = sum(t.profit_loss for t in trades if t.profit_loss > 0)
        gross_loss = abs(sum(t.profit_loss for t in trades if t.profit_loss < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Equity curve y drawdown
        equity_curve = [self.initial_balance]
        running_balance = self.initial_balance
        peak_balance = self.initial_balance
        max_drawdown = 0.0
        
        for trade in trades:
            running_balance += trade.profit_loss
            equity_curve.append(running_balance)
            
            if running_balance > peak_balance:
                peak_balance = running_balance
            
            drawdown = (peak_balance - running_balance) / peak_balance * 100
            max_drawdown = max(max_drawdown, drawdown)
        
        # Sharpe Ratio (simplificado)
        if len(trades) > 1:
            returns = [t.profit_loss / self.initial_balance for t in trades]
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0
        else:
            sharpe_ratio = 0.0
        
        # Retornos mensuales
        monthly_returns = {}
        for trade in trades:
            month_key = trade.entry_time.strftime('%Y-%m')
            if month_key not in monthly_returns:
                monthly_returns[month_key] = 0.0
            monthly_returns[month_key] += trade.profit_loss
        
        return BacktestResults(
            start_date=start_date,
            end_date=end_date,
            initial_balance=self.initial_balance,
            final_balance=final_balance,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            total_profit=total_profit,
            average_trade=average_trade,
            trades=trades,
            equity_curve=equity_curve,
            monthly_returns=monthly_returns
        )

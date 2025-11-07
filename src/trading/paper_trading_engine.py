"""
Motor de Paper Trading para Validación
Simula trading real sin riesgo de capital
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class PaperPosition:
    """Posición en paper trading"""
    id: str
    symbol: str
    direction: str  # 'long' or 'short'
    entry_price: float
    current_price: float
    size_lots: float
    entry_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    unrealized_pnl: float = 0.0
    max_favorable: float = 0.0
    max_adverse: float = 0.0
    strategy: str = 'unknown'
    confidence: float = 50.0

@dataclass
class PaperTrade:
    """Trade completado en paper trading"""
    id: str
    symbol: str
    direction: str
    entry_price: float
    exit_price: float
    size_lots: float
    entry_time: datetime
    exit_time: datetime
    pnl: float
    pnl_pips: float
    commission: float
    strategy: str
    confidence: float
    exit_reason: str  # 'stop_loss', 'take_profit', 'manual', 'time_exit'
    max_favorable: float
    max_adverse: float
    duration_minutes: int

class PaperTradingEngine:
    """Motor de paper trading con simulación realista"""
    
    def __init__(self, initial_balance: float = 10000, 
                 commission_per_lot: float = 7.0,
                 spread_pips: float = 1.5):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.commission_per_lot = commission_per_lot
        self.spread_pips = spread_pips
        
        # Posiciones y trades
        self.open_positions: Dict[str, PaperPosition] = {}
        self.closed_trades: List[PaperTrade] = []
        
        # Métricas en tiempo real
        self.equity_curve = []
        self.daily_pnl = []
        
        # Configuración de simulación
        self.slippage_pips = 0.5  # Slippage promedio
        self.max_slippage_pips = 2.0  # Slippage máximo en volatilidad
        
        logger.info(f"📊 Paper Trading Engine inicializado con ${initial_balance:,.2f}")
    
    async def open_position(self, signal: Dict, current_price: float, 
                          current_time: datetime) -> Dict:
        """Abrir una posición en paper trading"""
        try:
            # Generar ID único
            position_id = f"PT_{current_time.strftime('%Y%m%d_%H%M%S')}_{len(self.open_positions)}"
            
            # Simular slippage
            slippage = self._calculate_slippage(signal.get('confidence', 50))
            
            # Ajustar precio de entrada por spread y slippage
            if signal['action'] == 'buy':
                entry_price = current_price + (self.spread_pips * 0.0001) + slippage
            else:
                entry_price = current_price - (self.spread_pips * 0.0001) - slippage
            
            # Crear posición
            position = PaperPosition(
                id=position_id,
                symbol=signal.get('symbol', 'EURUSD'),
                direction='long' if signal['action'] == 'buy' else 'short',
                entry_price=entry_price,
                current_price=entry_price,
                size_lots=signal.get('size_lots', 0.1),
                entry_time=current_time,
                stop_loss=signal.get('stop_loss'),
                take_profit=signal.get('take_profit'),
                strategy=signal.get('strategy', 'unknown'),
                confidence=signal.get('confidence', 50)
            )
            
            # Calcular comisión
            commission = self.commission_per_lot * position.size_lots
            self.current_balance -= commission
            
            # Registrar posición
            self.open_positions[position_id] = position
            
            logger.info(f"📈 Posición abierta: {position.symbol} {position.direction} "
                       f"{position.size_lots} lotes @ {entry_price:.5f}")
            
            return {
                'success': True,
                'position_id': position_id,
                'entry_price': entry_price,
                'commission': commission,
                'slippage_pips': slippage / 0.0001
            }
            
        except Exception as e:
            logger.error(f"Error abriendo posición paper: {e}")
            return {'success': False, 'error': str(e)}
    
    async def close_position(self, position_id: str, current_price: float, 
                           current_time: datetime, reason: str = 'manual') -> Dict:
        """Cerrar una posición en paper trading"""
        try:
            if position_id not in self.open_positions:
                return {'success': False, 'error': 'Posición no encontrada'}
            
            position = self.open_positions[position_id]
            
            # Simular slippage en cierre
            slippage = self._calculate_slippage(position.confidence)
            
            # Ajustar precio de salida por spread y slippage
            if position.direction == 'long':
                exit_price = current_price - (self.spread_pips * 0.0001) - slippage
            else:
                exit_price = current_price + (self.spread_pips * 0.0001) + slippage
            
            # Calcular P&L
            if position.direction == 'long':
                pnl_pips = (exit_price - position.entry_price) / 0.0001
            else:
                pnl_pips = (position.entry_price - exit_price) / 0.0001
            
            pnl_usd = pnl_pips * position.size_lots * 10  # $10 por pip por lote
            
            # Comisión de cierre
            commission = self.commission_per_lot * position.size_lots
            net_pnl = pnl_usd - commission
            
            # Actualizar balance
            self.current_balance += net_pnl
            
            # Crear trade cerrado
            duration = (current_time - position.entry_time).total_seconds() / 60
            
            trade = PaperTrade(
                id=position.id,
                symbol=position.symbol,
                direction=position.direction,
                entry_price=position.entry_price,
                exit_price=exit_price,
                size_lots=position.size_lots,
                entry_time=position.entry_time,
                exit_time=current_time,
                pnl=net_pnl,
                pnl_pips=pnl_pips,
                commission=commission * 2,  # Entrada + salida
                strategy=position.strategy,
                confidence=position.confidence,
                exit_reason=reason,
                max_favorable=position.max_favorable,
                max_adverse=position.max_adverse,
                duration_minutes=int(duration)
            )
            
            # Registrar trade y remover posición
            self.closed_trades.append(trade)
            del self.open_positions[position_id]
            
            # Actualizar curva de equity
            self._update_equity_curve(current_time)
            
            logger.info(f"📉 Posición cerrada: {trade.symbol} {trade.direction} "
                       f"P&L: ${net_pnl:+.2f} ({pnl_pips:+.1f} pips)")
            
            return {
                'success': True,
                'pnl': net_pnl,
                'pnl_pips': pnl_pips,
                'exit_price': exit_price,
                'commission': commission * 2,
                'duration_minutes': int(duration)
            }
            
        except Exception as e:
            logger.error(f"Error cerrando posición paper: {e}")
            return {'success': False, 'error': str(e)}
    
    async def update_positions(self, current_prices: Dict[str, float], 
                             current_time: datetime):
        """Actualizar todas las posiciones abiertas"""
        try:
            positions_to_close = []
            
            for position_id, position in self.open_positions.items():
                symbol = position.symbol
                if symbol not in current_prices:
                    continue
                
                current_price = current_prices[symbol]
                position.current_price = current_price
                
                # Calcular P&L no realizado
                if position.direction == 'long':
                    unrealized_pips = (current_price - position.entry_price) / 0.0001
                else:
                    unrealized_pips = (position.entry_price - current_price) / 0.0001
                
                position.unrealized_pnl = unrealized_pips * position.size_lots * 10
                
                # Actualizar MAE y MFE
                if position.unrealized_pnl > position.max_favorable:
                    position.max_favorable = position.unrealized_pnl
                
                if position.unrealized_pnl < position.max_adverse:
                    position.max_adverse = position.unrealized_pnl
                
                # Verificar stop loss y take profit
                if position.stop_loss and self._check_stop_loss(position, current_price):
                    positions_to_close.append((position_id, 'stop_loss'))
                
                elif position.take_profit and self._check_take_profit(position, current_price):
                    positions_to_close.append((position_id, 'take_profit'))
            
            # Cerrar posiciones que tocaron SL/TP
            for position_id, reason in positions_to_close:
                await self.close_position(position_id, current_prices[self.open_positions[position_id].symbol], 
                                        current_time, reason)
            
        except Exception as e:
            logger.error(f"Error actualizando posiciones paper: {e}")
    
    def _calculate_slippage(self, confidence: float) -> float:
        """Calcular slippage basado en confianza y volatilidad"""
        # Menor confianza = mayor slippage (simulando peor timing)
        base_slippage = self.slippage_pips * 0.0001
        confidence_factor = (100 - confidence) / 100  # 0 a 1
        
        # Slippage adicional por baja confianza
        additional_slippage = confidence_factor * self.max_slippage_pips * 0.0001
        
        return base_slippage + additional_slippage
    
    def _check_stop_loss(self, position: PaperPosition, current_price: float) -> bool:
        """Verificar si se activó el stop loss"""
        if not position.stop_loss:
            return False
        
        if position.direction == 'long':
            return current_price <= position.stop_loss
        else:
            return current_price >= position.stop_loss
    
    def _check_take_profit(self, position: PaperPosition, current_price: float) -> bool:
        """Verificar si se activó el take profit"""
        if not position.take_profit:
            return False
        
        if position.direction == 'long':
            return current_price >= position.take_profit
        else:
            return current_price <= position.take_profit
    
    def _update_equity_curve(self, current_time: datetime):
        """Actualizar curva de equity"""
        total_unrealized = sum(pos.unrealized_pnl for pos in self.open_positions.values())
        current_equity = self.current_balance + total_unrealized
        
        self.equity_curve.append({
            'timestamp': current_time,
            'balance': self.current_balance,
            'equity': current_equity,
            'unrealized_pnl': total_unrealized,
            'open_positions': len(self.open_positions)
        })
        
        # Mantener solo últimos 10000 puntos
        if len(self.equity_curve) > 10000:
            self.equity_curve = self.equity_curve[-10000:]
    
    def get_performance_summary(self) -> Dict:
        """Obtener resumen de rendimiento"""
        try:
            if not self.closed_trades:
                return {
                    'total_trades': 0,
                    'current_balance': self.current_balance,
                    'total_return_pct': 0,
                    'message': 'No hay trades completados aún'
                }
            
            # Métricas básicas
            total_trades = len(self.closed_trades)
            winning_trades = [t for t in self.closed_trades if t.pnl > 0]
            losing_trades = [t for t in self.closed_trades if t.pnl <= 0]
            
            win_rate = len(winning_trades) / total_trades * 100
            total_pnl = sum(t.pnl for t in self.closed_trades)
            total_return_pct = (self.current_balance - self.initial_balance) / self.initial_balance * 100
            
            # Métricas avanzadas
            avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
            avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
            profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
            
            # Largest win/loss
            largest_win = max([t.pnl for t in self.closed_trades]) if self.closed_trades else 0
            largest_loss = min([t.pnl for t in self.closed_trades]) if self.closed_trades else 0
            
            # Drawdown
            equity_values = [point['equity'] for point in self.equity_curve]
            if equity_values:
                peak_equity = max(equity_values)
                current_equity = equity_values[-1]
                current_drawdown = (peak_equity - current_equity) / peak_equity * 100
                
                # Calcular máximo drawdown
                running_max = np.maximum.accumulate(equity_values)
                drawdowns = (equity_values - running_max) / running_max * 100
                max_drawdown = min(drawdowns) if len(drawdowns) > 0 else 0
            else:
                current_drawdown = 0
                max_drawdown = 0
            
            # Duración promedio
            avg_duration = np.mean([t.duration_minutes for t in self.closed_trades])
            
            # Performance por estrategia
            strategy_performance = {}
            for trade in self.closed_trades:
                strategy = trade.strategy
                if strategy not in strategy_performance:
                    strategy_performance[strategy] = {
                        'trades': 0,
                        'wins': 0,
                        'total_pnl': 0
                    }
                
                strategy_performance[strategy]['trades'] += 1
                strategy_performance[strategy]['total_pnl'] += trade.pnl
                if trade.pnl > 0:
                    strategy_performance[strategy]['wins'] += 1
            
            # Calcular win rate por estrategia
            for strategy, stats in strategy_performance.items():
                stats['win_rate'] = stats['wins'] / stats['trades'] * 100 if stats['trades'] > 0 else 0
            
            return {
                'total_trades': total_trades,
                'win_rate': round(win_rate, 2),
                'current_balance': round(self.current_balance, 2),
                'total_return_pct': round(total_return_pct, 2),
                'total_pnl': round(total_pnl, 2),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2),
                'profit_factor': round(profit_factor, 2),
                'largest_win': round(largest_win, 2),
                'largest_loss': round(largest_loss, 2),
                'current_drawdown_pct': round(current_drawdown, 2),
                'max_drawdown_pct': round(abs(max_drawdown), 2),
                'avg_duration_minutes': round(avg_duration, 1),
                'open_positions': len(self.open_positions),
                'strategy_performance': strategy_performance,
                'total_commission_paid': round(sum(t.commission for t in self.closed_trades), 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculando resumen de rendimiento: {e}")
            return {'error': str(e)}
    
    def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """Obtener trades recientes"""
        try:
            recent_trades = sorted(self.closed_trades, 
                                 key=lambda t: t.exit_time, 
                                 reverse=True)[:limit]
            
            return [
                {
                    'symbol': t.symbol,
                    'direction': t.direction,
                    'entry_time': t.entry_time.strftime('%Y-%m-%d %H:%M'),
                    'exit_time': t.exit_time.strftime('%Y-%m-%d %H:%M'),
                    'pnl': round(t.pnl, 2),
                    'pnl_pips': round(t.pnl_pips, 1),
                    'strategy': t.strategy,
                    'exit_reason': t.exit_reason,
                    'duration_minutes': t.duration_minutes
                }
                for t in recent_trades
            ]
            
        except Exception as e:
            logger.error(f"Error obteniendo trades recientes: {e}")
            return []
    
    def save_session(self, filepath: str):
        """Guardar sesión de paper trading"""
        try:
            session_data = {
                'initial_balance': self.initial_balance,
                'current_balance': self.current_balance,
                'commission_per_lot': self.commission_per_lot,
                'spread_pips': self.spread_pips,
                'closed_trades': [asdict(trade) for trade in self.closed_trades],
                'open_positions': {pid: asdict(pos) for pid, pos in self.open_positions.items()},
                'equity_curve': self.equity_curve[-1000:],  # Últimos 1000 puntos
                'session_start': datetime.now().isoformat(),
                'performance_summary': self.get_performance_summary()
            }
            
            # Crear directorio si no existe
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, default=str)
            
            logger.info(f"💾 Sesión de paper trading guardada en {filepath}")
            
        except Exception as e:
            logger.error(f"Error guardando sesión: {e}")
    
    def load_session(self, filepath: str):
        """Cargar sesión de paper trading"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            self.initial_balance = session_data.get('initial_balance', 10000)
            self.current_balance = session_data.get('current_balance', 10000)
            self.commission_per_lot = session_data.get('commission_per_lot', 7.0)
            self.spread_pips = session_data.get('spread_pips', 1.5)
            
            # Cargar trades cerrados
            self.closed_trades = []
            for trade_data in session_data.get('closed_trades', []):
                # Convertir strings de fecha de vuelta a datetime
                trade_data['entry_time'] = datetime.fromisoformat(trade_data['entry_time'])
                trade_data['exit_time'] = datetime.fromisoformat(trade_data['exit_time'])
                self.closed_trades.append(PaperTrade(**trade_data))
            
            # Cargar posiciones abiertas
            self.open_positions = {}
            for pid, pos_data in session_data.get('open_positions', {}).items():
                pos_data['entry_time'] = datetime.fromisoformat(pos_data['entry_time'])
                self.open_positions[pid] = PaperPosition(**pos_data)
            
            # Cargar curva de equity
            self.equity_curve = session_data.get('equity_curve', [])
            
            logger.info(f"📂 Sesión de paper trading cargada desde {filepath}")
            logger.info(f"💰 Balance: ${self.current_balance:,.2f}, "
                       f"Trades: {len(self.closed_trades)}, "
                       f"Posiciones abiertas: {len(self.open_positions)}")
            
        except FileNotFoundError:
            logger.info("No se encontró sesión previa - iniciando nueva sesión")
        except Exception as e:
            logger.error(f"Error cargando sesión: {e}")
    
    async def run_paper_trading_session(self, strategy_func, data: pd.DataFrame, 
                                      session_name: str = "paper_session"):
        """Ejecutar una sesión completa de paper trading"""
        logger.info(f"🎯 Iniciando sesión de paper trading: {session_name}")
        
        try:
            for i in range(100, len(data)):  # Empezar con suficientes datos
                current_bar = data.iloc[i]
                current_time = current_bar.name
                current_price = current_bar['close']
                
                # Actualizar posiciones existentes
                await self.update_positions({'EURUSD': current_price}, current_time)
                
                # Obtener señal de estrategia
                signal = strategy_func(data.iloc[:i+1], i)
                
                if signal and signal.get('action') in ['buy', 'sell']:
                    # Abrir nueva posición
                    await self.open_position(signal, current_price, current_time)
                
                # Actualizar equity curve cada 100 barras
                if i % 100 == 0:
                    self._update_equity_curve(current_time)
            
            # Cerrar todas las posiciones al final
            final_price = data.iloc[-1]['close']
            final_time = data.index[-1]
            
            for position_id in list(self.open_positions.keys()):
                await self.close_position(position_id, final_price, final_time, 'session_end')
            
            # Guardar sesión
            session_file = f"data/paper_trading/{session_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self.save_session(session_file)
            
            # Mostrar resumen
            summary = self.get_performance_summary()
            logger.info(f"📊 Sesión completada:")
            logger.info(f"   Trades: {summary['total_trades']}")
            logger.info(f"   Win Rate: {summary['win_rate']}%")
            logger.info(f"   Return: {summary['total_return_pct']}%")
            logger.info(f"   Max DD: {summary['max_drawdown_pct']}%")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error en sesión de paper trading: {e}")
            return None

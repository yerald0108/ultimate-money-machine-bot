"""
Sistema Avanzado de Gestión de Capital
Implementa Kelly Criterion, gestión de drawdown y protección contra ruina
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class CapitalState:
    """Estado actual del capital"""
    current_balance: float
    peak_balance: float
    current_drawdown: float
    max_drawdown: float
    risk_level: str  # 'conservative', 'moderate', 'aggressive'
    kelly_fraction: float
    position_size_multiplier: float

@dataclass
class TradeMetrics:
    """Métricas de trading para cálculos de Kelly"""
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    expectancy: float
    total_trades: int

class AdvancedCapitalManager:
    """Gestor avanzado de capital con Kelly Criterion y protección contra ruina"""
    
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.current_balance = initial_capital
        self.peak_balance = initial_capital
        self.trade_history = []
        
        # Configuración de riesgo
        self.max_portfolio_risk = 0.20  # 20% máximo del capital en riesgo
        self.max_single_trade_risk = 0.05  # 5% máximo por trade
        self.max_drawdown_limit = 0.15  # 15% drawdown máximo antes de reducir riesgo
        self.kelly_lookback_trades = 50  # Trades para calcular Kelly
        
        # Estados de protección
        self.drawdown_protection_active = False
        self.risk_reduction_factor = 1.0
        
        logger.info(f"💰 Capital Manager inicializado con ${initial_capital:,.2f}")
    
    def calculate_position_size(self, 
                              signal_confidence: float,
                              stop_loss_pips: float,
                              strategy_name: str,
                              current_price: float) -> Dict:
        """
        Calcular tamaño de posición óptimo usando Kelly Criterion modificado
        
        Returns:
            Dict con size, risk_amount, kelly_fraction, reasoning
        """
        try:
            # 1. Calcular Kelly Fraction
            kelly_fraction = self._calculate_kelly_fraction(strategy_name)
            
            # 2. Ajustar por confianza de señal
            confidence_multiplier = signal_confidence / 100
            adjusted_kelly = kelly_fraction * confidence_multiplier
            
            # 3. Aplicar límites de seguridad
            safe_kelly = min(adjusted_kelly, self.max_single_trade_risk)
            
            # 4. Aplicar factor de reducción por drawdown
            final_kelly = safe_kelly * self.risk_reduction_factor
            
            # 5. Calcular tamaño de posición
            risk_amount = self.current_balance * final_kelly
            
            # Convertir pips a precio
            pip_value_usd = 10  # $10 por pip por lote estándar en EUR/USD
            position_size_lots = risk_amount / (stop_loss_pips * pip_value_usd)
            
            # Aplicar límites de broker
            position_size_lots = max(0.01, min(position_size_lots, 10.0))
            
            # Verificar límites de exposición total
            total_exposure = self._calculate_total_exposure()
            if total_exposure + risk_amount > self.current_balance * self.max_portfolio_risk:
                # Reducir tamaño para no exceder exposición máxima
                available_risk = (self.current_balance * self.max_portfolio_risk) - total_exposure
                if available_risk <= 0:
                    return {
                        'size_lots': 0,
                        'risk_amount': 0,
                        'kelly_fraction': 0,
                        'reasoning': 'Maximum portfolio exposure reached'
                    }
                
                position_size_lots = available_risk / (stop_loss_pips * pip_value_usd)
                position_size_lots = max(0.01, min(position_size_lots, 10.0))
                risk_amount = position_size_lots * stop_loss_pips * pip_value_usd
            
            reasoning = self._generate_sizing_reasoning(
                kelly_fraction, confidence_multiplier, safe_kelly, 
                final_kelly, self.risk_reduction_factor
            )
            
            return {
                'size_lots': round(position_size_lots, 2),
                'risk_amount': round(risk_amount, 2),
                'kelly_fraction': round(final_kelly * 100, 2),
                'reasoning': reasoning,
                'risk_pct': round(risk_amount / self.current_balance * 100, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculando tamaño de posición: {e}")
            # Fallback a tamaño conservador
            return {
                'size_lots': 0.01,
                'risk_amount': self.current_balance * 0.01,
                'kelly_fraction': 1.0,
                'reasoning': 'Error calculation - using conservative fallback'
            }
    
    def _calculate_kelly_fraction(self, strategy_name: str) -> float:
        """Calcular Kelly Fraction para una estrategia específica"""
        try:
            # Filtrar trades de la estrategia
            strategy_trades = [t for t in self.trade_history 
                             if t.get('strategy') == strategy_name]
            
            if len(strategy_trades) < 10:
                # No hay suficientes datos, usar Kelly conservador
                return 0.02  # 2% por defecto
            
            # Tomar últimos N trades para cálculo
            recent_trades = strategy_trades[-self.kelly_lookback_trades:]
            
            # Calcular métricas
            wins = [t['pnl'] for t in recent_trades if t['pnl'] > 0]
            losses = [t['pnl'] for t in recent_trades if t['pnl'] < 0]
            
            if not wins or not losses:
                return 0.02  # Fallback conservador
            
            win_rate = len(wins) / len(recent_trades)
            avg_win = np.mean(wins)
            avg_loss = abs(np.mean(losses))
            
            # Kelly Formula: f = (bp - q) / b
            # donde b = avg_win/avg_loss, p = win_rate, q = 1-win_rate
            b = avg_win / avg_loss
            p = win_rate
            q = 1 - win_rate
            
            kelly_fraction = (b * p - q) / b
            
            # Aplicar límites de seguridad
            kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Máximo 25%
            
            # Aplicar factor de seguridad (Kelly fraccionario)
            safe_kelly = kelly_fraction * 0.25  # Usar 25% del Kelly completo
            
            logger.debug(f"Kelly para {strategy_name}: {safe_kelly:.3f} "
                        f"(Win rate: {win_rate:.2f}, Avg W/L: {b:.2f})")
            
            return safe_kelly
            
        except Exception as e:
            logger.error(f"Error calculando Kelly fraction: {e}")
            return 0.02  # Fallback conservador
    
    def update_balance(self, trade_result: Dict):
        """Actualizar balance y métricas después de un trade"""
        try:
            pnl = trade_result.get('pnl', 0)
            self.current_balance += pnl
            
            # Actualizar peak balance
            if self.current_balance > self.peak_balance:
                self.peak_balance = self.current_balance
            
            # Calcular drawdown actual
            current_drawdown = (self.peak_balance - self.current_balance) / self.peak_balance
            
            # Registrar trade
            trade_record = {
                'timestamp': datetime.now(),
                'pnl': pnl,
                'balance_after': self.current_balance,
                'drawdown': current_drawdown,
                'strategy': trade_result.get('strategy', 'unknown'),
                'confidence': trade_result.get('confidence', 50)
            }
            self.trade_history.append(trade_record)
            
            # Activar protecciones si es necesario
            self._check_drawdown_protection(current_drawdown)
            
            # Limpiar historial antiguo (mantener últimos 500 trades)
            if len(self.trade_history) > 500:
                self.trade_history = self.trade_history[-500:]
            
            logger.info(f"💰 Balance actualizado: ${self.current_balance:,.2f} "
                       f"(P&L: ${pnl:+.2f}, DD: {current_drawdown:.1%})")
            
        except Exception as e:
            logger.error(f"Error actualizando balance: {e}")
    
    def _check_drawdown_protection(self, current_drawdown: float):
        """Verificar y activar protecciones por drawdown"""
        try:
            if current_drawdown > self.max_drawdown_limit:
                if not self.drawdown_protection_active:
                    self.drawdown_protection_active = True
                    self.risk_reduction_factor = 0.5  # Reducir riesgo al 50%
                    logger.warning(f"🛡️ PROTECCIÓN ACTIVADA: Drawdown {current_drawdown:.1%} "
                                 f"excede límite {self.max_drawdown_limit:.1%}")
                
                # Reducción progresiva del riesgo
                if current_drawdown > self.max_drawdown_limit * 1.5:
                    self.risk_reduction_factor = 0.25  # Reducir al 25%
                elif current_drawdown > self.max_drawdown_limit * 2:
                    self.risk_reduction_factor = 0.1   # Reducir al 10%
            
            else:
                # Recuperación gradual
                if self.drawdown_protection_active and current_drawdown < self.max_drawdown_limit * 0.5:
                    self.drawdown_protection_active = False
                    self.risk_reduction_factor = 0.75  # Recuperación gradual
                    logger.info(f"🔄 Recuperación parcial: Factor de riesgo aumentado a 75%")
                
                elif current_drawdown < self.max_drawdown_limit * 0.25:
                    self.risk_reduction_factor = 1.0   # Riesgo completo
                    logger.info(f"✅ Recuperación completa: Riesgo restaurado al 100%")
            
        except Exception as e:
            logger.error(f"Error en protección por drawdown: {e}")
    
    def _calculate_total_exposure(self) -> float:
        """Calcular exposición total actual del portfolio"""
        # En una implementación completa, esto calcularía la exposición
        # de todas las posiciones abiertas
        # Por ahora, retornamos 0 como placeholder
        return 0
    
    def _generate_sizing_reasoning(self, kelly_raw: float, confidence_mult: float, 
                                 safe_kelly: float, final_kelly: float, 
                                 risk_factor: float) -> str:
        """Generar explicación del cálculo de tamaño"""
        reasoning_parts = []
        
        reasoning_parts.append(f"Kelly base: {kelly_raw:.1%}")
        
        if confidence_mult < 1.0:
            reasoning_parts.append(f"Ajuste confianza: x{confidence_mult:.2f}")
        
        if safe_kelly < kelly_raw * confidence_mult:
            reasoning_parts.append(f"Límite seguridad aplicado")
        
        if risk_factor < 1.0:
            reasoning_parts.append(f"Protección DD: x{risk_factor:.2f}")
        
        reasoning_parts.append(f"Final: {final_kelly:.1%}")
        
        return " | ".join(reasoning_parts)
    
    def get_capital_state(self) -> CapitalState:
        """Obtener estado actual del capital"""
        current_drawdown = (self.peak_balance - self.current_balance) / self.peak_balance
        
        # Determinar nivel de riesgo actual
        if self.risk_reduction_factor <= 0.25:
            risk_level = 'conservative'
        elif self.risk_reduction_factor <= 0.75:
            risk_level = 'moderate'
        else:
            risk_level = 'aggressive'
        
        return CapitalState(
            current_balance=self.current_balance,
            peak_balance=self.peak_balance,
            current_drawdown=current_drawdown,
            max_drawdown=max([t.get('drawdown', 0) for t in self.trade_history] + [0]),
            risk_level=risk_level,
            kelly_fraction=self._calculate_average_kelly(),
            position_size_multiplier=self.risk_reduction_factor
        )
    
    def _calculate_average_kelly(self) -> float:
        """Calcular Kelly promedio de todas las estrategias"""
        if not self.trade_history:
            return 0.02
        
        strategies = set(t.get('strategy', 'unknown') for t in self.trade_history)
        kelly_values = []
        
        for strategy in strategies:
            kelly = self._calculate_kelly_fraction(strategy)
            kelly_values.append(kelly)
        
        return np.mean(kelly_values) if kelly_values else 0.02
    
    def get_performance_metrics(self) -> Dict:
        """Obtener métricas de rendimiento del capital"""
        if not self.trade_history:
            return {}
        
        try:
            # Calcular métricas básicas
            total_return = (self.current_balance - self.initial_capital) / self.initial_capital
            
            # Calcular Sharpe ratio
            returns = []
            for i in range(1, len(self.trade_history)):
                prev_balance = self.trade_history[i-1]['balance_after']
                curr_balance = self.trade_history[i]['balance_after']
                daily_return = (curr_balance - prev_balance) / prev_balance
                returns.append(daily_return)
            
            if len(returns) > 1:
                avg_return = np.mean(returns)
                std_return = np.std(returns)
                sharpe_ratio = (avg_return * 252) / (std_return * np.sqrt(252)) if std_return > 0 else 0
            else:
                sharpe_ratio = 0
            
            # Calcular máximo drawdown
            max_dd = max([t.get('drawdown', 0) for t in self.trade_history] + [0])
            
            # Calcular Calmar ratio
            calmar_ratio = (total_return * 100) / (max_dd * 100) if max_dd > 0 else 0
            
            return {
                'total_return_pct': round(total_return * 100, 2),
                'current_balance': round(self.current_balance, 2),
                'peak_balance': round(self.peak_balance, 2),
                'max_drawdown_pct': round(max_dd * 100, 2),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'calmar_ratio': round(calmar_ratio, 2),
                'total_trades': len(self.trade_history),
                'risk_reduction_active': self.drawdown_protection_active,
                'current_risk_factor': self.risk_reduction_factor
            }
            
        except Exception as e:
            logger.error(f"Error calculando métricas de rendimiento: {e}")
            return {}
    
    def should_allow_new_trade(self, current_exposure: float, 
                              signal_confidence: float) -> Tuple[bool, str]:
        """Determinar si se debe permitir un nuevo trade"""
        try:
            # 1. Verificar límite de exposición total
            if current_exposure >= self.current_balance * self.max_portfolio_risk:
                return False, f"Exposición máxima alcanzada ({current_exposure/self.current_balance:.1%})"
            
            # 2. Verificar drawdown extremo
            current_drawdown = (self.peak_balance - self.current_balance) / self.peak_balance
            if current_drawdown > self.max_drawdown_limit * 2:
                return False, f"Drawdown extremo ({current_drawdown:.1%}) - trading suspendido"
            
            # 3. Verificar confianza mínima durante protección
            if self.drawdown_protection_active and signal_confidence < 75:
                return False, f"Protección activa - confianza insuficiente ({signal_confidence}%)"
            
            # 4. Verificar balance mínimo
            if self.current_balance < self.initial_capital * 0.5:
                return False, "Balance por debajo del 50% inicial - trading suspendido"
            
            return True, "Trade permitido"
            
        except Exception as e:
            logger.error(f"Error verificando permiso de trade: {e}")
            return False, "Error en verificación"
    
    def save_state(self, filepath: str):
        """Guardar estado del gestor de capital"""
        try:
            state = {
                'current_balance': self.current_balance,
                'peak_balance': self.peak_balance,
                'initial_capital': self.initial_capital,
                'trade_history': self.trade_history[-100:],  # Solo últimos 100 trades
                'drawdown_protection_active': self.drawdown_protection_active,
                'risk_reduction_factor': self.risk_reduction_factor,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(filepath, 'w') as f:
                json.dump(state, f, indent=2, default=str)
            
            logger.info(f"💾 Estado del capital guardado en {filepath}")
            
        except Exception as e:
            logger.error(f"Error guardando estado del capital: {e}")
    
    def load_state(self, filepath: str):
        """Cargar estado del gestor de capital"""
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            self.current_balance = state.get('current_balance', self.initial_capital)
            self.peak_balance = state.get('peak_balance', self.initial_capital)
            self.trade_history = state.get('trade_history', [])
            self.drawdown_protection_active = state.get('drawdown_protection_active', False)
            self.risk_reduction_factor = state.get('risk_reduction_factor', 1.0)
            
            logger.info(f"📂 Estado del capital cargado desde {filepath}")
            logger.info(f"💰 Balance actual: ${self.current_balance:,.2f}")
            
        except FileNotFoundError:
            logger.info("No se encontró archivo de estado previo - iniciando desde cero")
        except Exception as e:
            logger.error(f"Error cargando estado del capital: {e}")

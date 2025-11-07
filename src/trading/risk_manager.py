"""
Gestor de Riesgo Avanzado
Optimiza el tamaño de posición y gestión de riesgo para máxima rentabilidad
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd

logger = logging.getLogger(__name__)

class AdvancedRiskManager:
    def __init__(self):
        # Configuración base
        self.base_risk_percentage = float(os.getenv('RISK_PERCENTAGE', 2.0))
        self.max_daily_loss = float(os.getenv('MAX_DAILY_LOSS', 100.0))
        self.max_positions = 3  # Máximo 3 posiciones simultáneas
        
        # Configuración avanzada
        self.confidence_multiplier = True  # Ajustar riesgo por confianza
        self.market_regime_adjustment = True  # Ajustar por régimen de mercado
        self.performance_adjustment = True  # Ajustar por rendimiento reciente
        self.position_scaling = True  # Escalado de posiciones ganadoras
        
        # Tracking de rendimiento
        self.recent_performance = []
        self.daily_stats = {
            'trades': 0,
            'wins': 0,
            'losses': 0,
            'profit': 0.0,
            'max_drawdown': 0.0
        }
    
    def calculate_optimal_position_size(self, balance: float, confidence: float, 
                                      market_regime: Dict, recent_performance: List[Dict],
                                      stop_loss_pips: int) -> float:
        """Calcular tamaño óptimo de posición basado en múltiples factores"""
        try:
            # Riesgo base
            base_risk = self.base_risk_percentage / 100
            
            # === AJUSTE POR CONFIANZA ===
            confidence_factor = 1.0
            if self.confidence_multiplier:
                if confidence >= 90:
                    confidence_factor = 1.5  # Aumentar riesgo en señales muy fuertes
                elif confidence >= 80:
                    confidence_factor = 1.2
                elif confidence >= 75:
                    confidence_factor = 1.0
                else:
                    confidence_factor = 0.7  # Reducir riesgo en señales débiles
            
            # === AJUSTE POR RÉGIMEN DE MERCADO ===
            regime_factor = 1.0
            if self.market_regime_adjustment and market_regime:
                regime = market_regime.get('regime', 'UNKNOWN')
                strength = market_regime.get('strength', 50)
                
                if regime == 'TRENDING' and strength > 70:
                    regime_factor = 1.3  # Más agresivo en tendencias fuertes
                elif regime == 'RANGING':
                    regime_factor = 0.8  # Más conservador en rangos
                elif regime == 'TRANSITIONAL':
                    regime_factor = 0.6  # Muy conservador en transiciones
            
            # === AJUSTE POR RENDIMIENTO RECIENTE ===
            performance_factor = 1.0
            if self.performance_adjustment and recent_performance:
                # Analizar últimos 10 trades
                recent_trades = recent_performance[-10:] if len(recent_performance) >= 10 else recent_performance
                
                if recent_trades:
                    win_rate = sum(1 for trade in recent_trades if trade.get('profit', 0) > 0) / len(recent_trades)
                    avg_profit = sum(trade.get('profit', 0) for trade in recent_trades) / len(recent_trades)
                    
                    if win_rate >= 0.7 and avg_profit > 0:
                        performance_factor = 1.4  # Racha ganadora - ser más agresivo
                    elif win_rate >= 0.6:
                        performance_factor = 1.1
                    elif win_rate <= 0.3:
                        performance_factor = 0.5  # Racha perdedora - ser conservador
                    elif avg_profit < 0:
                        performance_factor = 0.7
            
            # === CÁLCULO FINAL ===
            adjusted_risk = base_risk * confidence_factor * regime_factor * performance_factor
            
            # Limitar el riesgo ajustado
            adjusted_risk = max(0.005, min(0.05, adjusted_risk))  # Entre 0.5% y 5%
            
            # Calcular tamaño de lote
            risk_amount = balance * adjusted_risk
            pip_value = 10  # Para EUR/USD, 1 pip = $10 por lote estándar
            lot_size = risk_amount / (stop_loss_pips * pip_value)
            
            # Redondear a incrementos válidos
            lot_size = round(lot_size, 2)
            lot_size = max(0.01, min(2.0, lot_size))  # Entre 0.01 y 2.0 lotes
            
            logger.info(f"Cálculo de posición:")
            logger.info(f"  - Riesgo base: {base_risk:.1%}")
            logger.info(f"  - Factor confianza: {confidence_factor:.2f}")
            logger.info(f"  - Factor régimen: {regime_factor:.2f}")
            logger.info(f"  - Factor rendimiento: {performance_factor:.2f}")
            logger.info(f"  - Riesgo ajustado: {adjusted_risk:.1%}")
            logger.info(f"  - Tamaño final: {lot_size} lotes")
            
            return lot_size
            
        except Exception as e:
            logger.error(f"Error calculando tamaño de posición: {e}")
            return 0.01  # Tamaño mínimo por seguridad
    
    def should_allow_new_trade(self, current_positions: List[Dict], 
                              daily_profit: float, confidence: float) -> Tuple[bool, str]:
        """Determinar si se debe permitir un nuevo trade"""
        try:
            # Verificar número máximo de posiciones
            if len(current_positions) >= self.max_positions:
                return False, f"Máximo de posiciones alcanzado ({self.max_positions})"
            
            # Verificar pérdida diaria máxima
            if daily_profit <= -self.max_daily_loss:
                return False, f"Pérdida diaria máxima alcanzada (${abs(daily_profit):.2f})"
            
            # Verificar confianza mínima
            if confidence < 75:
                return False, f"Confianza insuficiente ({confidence:.0f}% < 75%)"
            
            # Verificar correlación de posiciones (evitar sobre-exposición)
            if len(current_positions) >= 2:
                same_direction = sum(1 for pos in current_positions 
                                   if pos.get('type', '').upper() == 'BUY')
                
                if same_direction == len(current_positions):
                    return False, "Todas las posiciones en la misma dirección"
            
            # Verificar drawdown
            if daily_profit < -self.max_daily_loss * 0.7:
                return False, f"Acercándose al límite de pérdida diaria"
            
            return True, "Trade permitido"
            
        except Exception as e:
            logger.error(f"Error verificando si permitir trade: {e}")
            return False, "Error en verificación de riesgo"
    
    def calculate_trailing_stop(self, position: Dict, current_price: float, 
                               atr: float) -> Optional[float]:
        """Calcular trailing stop dinámico"""
        try:
            entry_price = position.get('open_price', 0)
            position_type = position.get('type', '').upper()
            current_sl = position.get('sl', 0)
            
            if not entry_price or not position_type:
                return None
            
            # Calcular trailing distance basado en ATR
            trailing_distance = atr * 1.5
            
            if position_type == 'BUY':
                # Para posiciones largas, subir el SL si el precio sube
                profit_pips = (current_price - entry_price) * 10000
                
                if profit_pips > 20:  # Solo activar trailing después de 20 pips de ganancia
                    new_sl = current_price - trailing_distance
                    
                    # Solo mover SL hacia arriba
                    if new_sl > current_sl:
                        return round(new_sl, 5)
            
            elif position_type == 'SELL':
                # Para posiciones cortas, bajar el SL si el precio baja
                profit_pips = (entry_price - current_price) * 10000
                
                if profit_pips > 20:  # Solo activar trailing después de 20 pips de ganancia
                    new_sl = current_price + trailing_distance
                    
                    # Solo mover SL hacia abajo
                    if new_sl < current_sl:
                        return round(new_sl, 5)
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculando trailing stop: {e}")
            return None
    
    def should_scale_position(self, position: Dict, current_price: float, 
                             entry_price: float) -> tuple[bool, float]:
        """Determinar si se debe escalar una posición ganadora"""
        try:
            if not self.position_scaling:
                return False, 0.0
            
            position_type = position.get('type', '').upper()
            current_profit_pips = 0
            
            # Calcular profit en pips
            if position_type == 'BUY':
                current_profit_pips = (current_price - entry_price) * 10000
            elif position_type == 'SELL':
                current_profit_pips = (entry_price - current_price) * 10000
            
            # Criterios para escalado
            min_profit_for_scaling = 30  # Mínimo 30 pips de ganancia
            scaling_intervals = [30, 50, 80]  # Escalar en estos niveles de pips
            scaling_size = 0.5  # 50% del tamaño original
            
            if current_profit_pips >= min_profit_for_scaling:
                # Verificar si ya se escaló en este nivel
                for interval in scaling_intervals:
                    if current_profit_pips >= interval:
                        # Verificar si no se ha escalado ya en este nivel
                        # (esto requeriría tracking adicional en producción)
                        scaling_volume = position.get('volume', 0.01) * scaling_size
                        return True, round(scaling_volume, 2)
            
            return False, 0.0
            
        except Exception as e:
            logger.error(f"Error evaluando escalado de posición: {e}")
            return False, 0.0
    
    def calculate_partial_close_size(self, position: Dict, current_price: float, 
                                   entry_price: float, target_profit_pips: int = 50) -> Optional[float]:
        """Calcular tamaño para cierre parcial de posición"""
        try:
            position_type = position.get('type', '').upper()
            current_profit_pips = 0
            
            # Calcular profit en pips
            if position_type == 'BUY':
                current_profit_pips = (current_price - entry_price) * 10000
            elif position_type == 'SELL':
                current_profit_pips = (entry_price - current_price) * 10000
            
            # Si alcanzó el target, cerrar 50% de la posición
            if current_profit_pips >= target_profit_pips:
                original_volume = position.get('volume', 0.01)
                partial_close_volume = original_volume * 0.5
                return round(partial_close_volume, 2)
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculando cierre parcial: {e}")
            return None
    
    def update_performance_tracking(self, trade_result: Dict):
        """Actualizar tracking de rendimiento"""
        try:
            self.recent_performance.append({
                'timestamp': datetime.now(),
                'profit': trade_result.get('profit', 0),
                'win': trade_result.get('profit', 0) > 0,
                'confidence': trade_result.get('confidence', 0)
            })
            
            # Mantener solo últimos 50 trades
            if len(self.recent_performance) > 50:
                self.recent_performance = self.recent_performance[-50:]
            
            # Actualizar estadísticas diarias
            self.daily_stats['trades'] += 1
            if trade_result.get('profit', 0) > 0:
                self.daily_stats['wins'] += 1
            else:
                self.daily_stats['losses'] += 1
            
            self.daily_stats['profit'] += trade_result.get('profit', 0)
            
        except Exception as e:
            logger.error(f"Error actualizando tracking de rendimiento: {e}")
    
    def get_risk_metrics(self) -> Dict:
        """Obtener métricas de riesgo actuales"""
        try:
            if not self.recent_performance:
                return {}
            
            recent_trades = self.recent_performance[-20:] if len(self.recent_performance) >= 20 else self.recent_performance
            
            total_trades = len(recent_trades)
            winning_trades = sum(1 for trade in recent_trades if trade['profit'] > 0)
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            profits = [trade['profit'] for trade in recent_trades]
            avg_profit = sum(profits) / len(profits) if profits else 0
            max_profit = max(profits) if profits else 0
            max_loss = min(profits) if profits else 0
            
            # Calcular Sharpe ratio simplificado
            profit_std = pd.Series(profits).std() if len(profits) > 1 else 0
            sharpe_ratio = avg_profit / profit_std if profit_std > 0 else 0
            
            return {
                'total_trades': total_trades,
                'win_rate': win_rate,
                'avg_profit': avg_profit,
                'max_profit': max_profit,
                'max_loss': max_loss,
                'sharpe_ratio': sharpe_ratio,
                'current_streak': self._calculate_current_streak(),
                'risk_score': self._calculate_risk_score()
            }
            
        except Exception as e:
            logger.error(f"Error calculando métricas de riesgo: {e}")
            return {}
    
    def _calculate_current_streak(self) -> Dict:
        """Calcular racha actual de wins/losses"""
        if not self.recent_performance:
            return {'type': 'none', 'count': 0}
        
        current_streak = 0
        streak_type = 'none'
        
        for trade in reversed(self.recent_performance):
            if current_streak == 0:
                streak_type = 'win' if trade['profit'] > 0 else 'loss'
                current_streak = 1
            elif (streak_type == 'win' and trade['profit'] > 0) or (streak_type == 'loss' and trade['profit'] <= 0):
                current_streak += 1
            else:
                break
        
        return {'type': streak_type, 'count': current_streak}
    
    def _calculate_risk_score(self) -> float:
        """Calcular score de riesgo (0-100, menor es mejor)"""
        try:
            if not self.recent_performance:
                return 50  # Score neutral
            
            recent_trades = self.recent_performance[-10:]
            
            # Factores de riesgo
            win_rate = sum(1 for trade in recent_trades if trade['profit'] > 0) / len(recent_trades)
            avg_profit = sum(trade['profit'] for trade in recent_trades) / len(recent_trades)
            
            # Score basado en win rate (invertido)
            win_rate_score = (1 - win_rate) * 50
            
            # Score basado en profit promedio (invertido si es negativo)
            profit_score = max(0, -avg_profit * 10) if avg_profit < 0 else 0
            
            # Score de racha perdedora
            streak = self._calculate_current_streak()
            streak_score = streak['count'] * 5 if streak['type'] == 'loss' else 0
            
            total_score = min(100, win_rate_score + profit_score + streak_score)
            
            return total_score
            
        except Exception as e:
            logger.error(f"Error calculando risk score: {e}")
            return 50

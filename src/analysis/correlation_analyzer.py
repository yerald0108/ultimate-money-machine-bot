"""
Analizador de Correlaciones Multi-Pair
Gestiona correlaciones entre pares de divisas para optimizar diversificación
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import asyncio

logger = logging.getLogger(__name__)

class CorrelationAnalyzer:
    def __init__(self, mt5_connector):
        self.mt5 = mt5_connector
        
        # Pares principales soportados
        self.supported_pairs = {
            'EURUSD': {'pip_value': 10, 'spread_avg': 1.5, 'session_preference': ['london', 'new_york']},
            'GBPUSD': {'pip_value': 10, 'spread_avg': 2.0, 'session_preference': ['london', 'new_york']},
            'USDJPY': {'pip_value': 10, 'spread_avg': 1.8, 'session_preference': ['asian', 'london']},
            'USDCHF': {'pip_value': 10, 'spread_avg': 2.2, 'session_preference': ['london', 'new_york']},
            'AUDUSD': {'pip_value': 10, 'spread_avg': 2.5, 'session_preference': ['asian', 'london']},
            'NZDUSD': {'pip_value': 10, 'spread_avg': 3.0, 'session_preference': ['asian', 'london']},
            'EURGBP': {'pip_value': 10, 'spread_avg': 2.8, 'session_preference': ['london']},
            'EURJPY': {'pip_value': 10, 'spread_avg': 2.5, 'session_preference': ['london', 'asian']}
        }
        
        # Matriz de correlaciones conocidas (aproximadas)
        self.correlation_matrix = {
            'EURUSD': {
                'GBPUSD': 0.75,   # Correlación positiva fuerte
                'USDJPY': -0.65,  # Correlación negativa
                'USDCHF': -0.85,  # Correlación negativa fuerte
                'AUDUSD': 0.60,   # Correlación positiva moderada
                'NZDUSD': 0.55,   # Correlación positiva moderada
                'EURGBP': 0.45,   # Correlación positiva débil
                'EURJPY': 0.70    # Correlación positiva fuerte
            },
            'GBPUSD': {
                'EURUSD': 0.75,
                'USDJPY': -0.55,
                'USDCHF': -0.70,
                'AUDUSD': 0.65,
                'NZDUSD': 0.60,
                'EURGBP': -0.40,  # Correlación negativa (GBP vs EUR)
                'EURJPY': 0.50
            },
            'USDJPY': {
                'EURUSD': -0.65,
                'GBPUSD': -0.55,
                'USDCHF': 0.60,   # Ambos tienen USD como base
                'AUDUSD': -0.45,
                'NZDUSD': -0.40,
                'EURGBP': -0.30,
                'EURJPY': 0.25    # JPY común pero direcciones opuestas
            }
        }
        
        # Cache de correlaciones dinámicas
        self.dynamic_correlations = {}
        self.last_correlation_update = None
        self.correlation_update_interval = 3600  # 1 hora
        
        # Límites de exposición
        self.max_correlation_exposure = 0.7  # Máximo 70% correlación
        self.max_pairs_per_currency = 3     # Máximo 3 pares con misma divisa
        
    async def get_optimal_pairs_for_session(self, current_session: str, max_pairs: int = 3) -> List[str]:
        """Obtener pares óptimos para la sesión actual"""
        try:
            optimal_pairs = []
            
            # Filtrar pares por sesión preferida
            session_pairs = []
            for pair, config in self.supported_pairs.items():
                if current_session in config['session_preference'] or current_session == 'overlap':
                    session_pairs.append(pair)
            
            # Verificar spreads actuales
            valid_pairs = []
            for pair in session_pairs:
                spread = await self._get_pair_spread(pair)
                expected_spread = self.supported_pairs[pair]['spread_avg']
                
                # Solo incluir si spread está dentro del rango aceptable
                if spread <= expected_spread * 1.5:  # Máximo 50% más que el promedio
                    valid_pairs.append((pair, spread))
            
            # Ordenar por spread (menor es mejor)
            valid_pairs.sort(key=lambda x: x[1])
            
            # Seleccionar pares con baja correlación
            for pair, spread in valid_pairs:
                if len(optimal_pairs) >= max_pairs:
                    break
                
                # Verificar correlación con pares ya seleccionados
                can_add = True
                for selected_pair in optimal_pairs:
                    correlation = self._get_pair_correlation(pair, selected_pair)
                    if abs(correlation) > self.max_correlation_exposure:
                        can_add = False
                        break
                
                if can_add:
                    optimal_pairs.append(pair)
            
            # Asegurar diversificación mínima
            if len(optimal_pairs) == 0 and valid_pairs:
                optimal_pairs.append(valid_pairs[0][0])  # Al menos un par
            
            logger.info(f"🌍 Pares óptimos para sesión {current_session}: {optimal_pairs}")
            return optimal_pairs
            
        except Exception as e:
            logger.error(f"Error obteniendo pares óptimos: {e}")
            return ['EURUSD']  # Fallback seguro
    
    def _get_pair_correlation(self, pair1: str, pair2: str) -> float:
        """Obtener correlación entre dos pares"""
        try:
            if pair1 == pair2:
                return 1.0
            
            # Buscar en matriz estática
            if pair1 in self.correlation_matrix:
                if pair2 in self.correlation_matrix[pair1]:
                    return self.correlation_matrix[pair1][pair2]
            
            if pair2 in self.correlation_matrix:
                if pair1 in self.correlation_matrix[pair2]:
                    return self.correlation_matrix[pair2][pair1]
            
            # Calcular correlación basada en divisas comunes
            return self._calculate_currency_correlation(pair1, pair2)
            
        except Exception as e:
            logger.error(f"Error calculando correlación {pair1}/{pair2}: {e}")
            return 0.0
    
    def _calculate_currency_correlation(self, pair1: str, pair2: str) -> float:
        """Calcular correlación aproximada basada en divisas comunes"""
        try:
            # Extraer divisas
            base1, quote1 = pair1[:3], pair1[3:]
            base2, quote2 = pair2[:3], pair2[3:]
            
            # Misma divisa base = correlación positiva
            if base1 == base2:
                return 0.6
            
            # Misma divisa cotizada = correlación negativa
            if quote1 == quote2:
                return -0.5
            
            # Divisas invertidas = correlación negativa fuerte
            if base1 == quote2 and quote1 == base2:
                return -0.8
            
            # Una divisa común = correlación moderada
            if base1 == quote2 or quote1 == base2:
                return 0.4
            
            if base1 in [base2, quote2] or quote1 in [base2, quote2]:
                return 0.3
            
            # Sin divisas comunes = correlación baja
            return 0.1
            
        except Exception as e:
            logger.error(f"Error calculando correlación de divisas: {e}")
            return 0.0
    
    async def _get_pair_spread(self, pair: str) -> float:
        """Obtener spread actual de un par"""
        try:
            symbol_info = await self.mt5.get_symbol_info(pair)
            if symbol_info:
                spread = symbol_info.get('spread', 30) / 10  # Convertir a pips
                return spread
            
            # Fallback al spread promedio conocido
            return self.supported_pairs.get(pair, {}).get('spread_avg', 3.0)
            
        except Exception as e:
            logger.error(f"Error obteniendo spread de {pair}: {e}")
            return 3.0
    
    async def update_dynamic_correlations(self, pairs: List[str], lookback_hours: int = 24):
        """Actualizar correlaciones dinámicas basadas en datos recientes"""
        try:
            if (self.last_correlation_update and 
                (datetime.now() - self.last_correlation_update).total_seconds() < self.correlation_update_interval):
                return
            
            logger.info("🔄 Actualizando correlaciones dinámicas...")
            
            # Obtener datos de todos los pares
            pair_data = {}
            for pair in pairs:
                try:
                    df = await self.mt5.get_rates(symbol=pair, timeframe="H1", count=lookback_hours)
                    if not df.empty:
                        pair_data[pair] = df['close'].pct_change().dropna()
                except Exception as pair_error:
                    logger.warning(f"No se pudieron obtener datos para {pair}: {pair_error}")
                    continue
            
            # Calcular correlaciones dinámicas
            for pair1 in pair_data:
                if pair1 not in self.dynamic_correlations:
                    self.dynamic_correlations[pair1] = {}
                
                for pair2 in pair_data:
                    if pair1 != pair2:
                        try:
                            # Alinear series temporales
                            common_index = pair_data[pair1].index.intersection(pair_data[pair2].index)
                            if len(common_index) > 10:  # Mínimo 10 puntos de datos
                                series1 = pair_data[pair1].loc[common_index]
                                series2 = pair_data[pair2].loc[common_index]
                                
                                correlation = series1.corr(series2)
                                if not np.isnan(correlation):
                                    self.dynamic_correlations[pair1][pair2] = correlation
                        except Exception as corr_error:
                            logger.warning(f"Error calculando correlación {pair1}/{pair2}: {corr_error}")
                            continue
            
            self.last_correlation_update = datetime.now()
            logger.info(f"✅ Correlaciones dinámicas actualizadas para {len(pair_data)} pares")
            
        except Exception as e:
            logger.error(f"Error actualizando correlaciones dinámicas: {e}")
    
    def get_correlation_risk_score(self, current_positions: List[Dict]) -> float:
        """Calcular score de riesgo por correlación de posiciones actuales"""
        try:
            if len(current_positions) <= 1:
                return 0.0
            
            total_risk = 0.0
            position_pairs = [(pos['symbol'], pos['volume'], pos['type']) for pos in current_positions]
            
            for i, (pair1, vol1, type1) in enumerate(position_pairs):
                for j, (pair2, vol2, type2) in enumerate(position_pairs[i+1:], i+1):
                    correlation = self._get_pair_correlation(pair1, pair2)
                    
                    # Ajustar correlación por dirección de trades
                    if type1 != type2:  # Direcciones opuestas
                        correlation = -correlation
                    
                    # Calcular riesgo ponderado por volumen
                    weight = min(vol1, vol2) / max(vol1, vol2) if max(vol1, vol2) > 0 else 0
                    risk_contribution = abs(correlation) * weight
                    total_risk += risk_contribution
            
            # Normalizar por número de pares de posiciones
            num_pairs = len(position_pairs) * (len(position_pairs) - 1) / 2
            normalized_risk = total_risk / num_pairs if num_pairs > 0 else 0
            
            return min(1.0, normalized_risk)
            
        except Exception as e:
            logger.error(f"Error calculando score de riesgo por correlación: {e}")
            return 0.5
    
    def can_add_position(self, new_pair: str, new_type: str, current_positions: List[Dict]) -> Tuple[bool, str]:
        """Verificar si se puede agregar una nueva posición sin exceder límites de correlación"""
        try:
            # Verificar límite de pares por divisa
            currency_count = self._count_currency_exposure(new_pair, current_positions)
            if currency_count >= self.max_pairs_per_currency:
                return False, f"Máximo {self.max_pairs_per_currency} pares por divisa alcanzado"
            
            # Simular nueva posición
            simulated_positions = current_positions + [{
                'symbol': new_pair,
                'type': new_type,
                'volume': 0.1  # Volumen estándar para simulación
            }]
            
            # Calcular riesgo de correlación con nueva posición
            correlation_risk = self.get_correlation_risk_score(simulated_positions)
            
            if correlation_risk > self.max_correlation_exposure:
                return False, f"Riesgo de correlación muy alto: {correlation_risk:.1%}"
            
            # Verificar correlaciones específicas con posiciones existentes
            for pos in current_positions:
                correlation = self._get_pair_correlation(new_pair, pos['symbol'])
                
                # Ajustar por dirección
                if new_type != pos['type']:
                    correlation = -correlation
                
                if abs(correlation) > 0.8:  # Correlación muy alta
                    return False, f"Correlación muy alta con {pos['symbol']}: {correlation:.2f}"
            
            return True, "Posición permitida"
            
        except Exception as e:
            logger.error(f"Error verificando si se puede agregar posición: {e}")
            return False, "Error en verificación de correlación"
    
    def _count_currency_exposure(self, new_pair: str, current_positions: List[Dict]) -> int:
        """Contar exposición actual a las divisas del nuevo par"""
        try:
            new_base, new_quote = new_pair[:3], new_pair[3:]
            count = 0
            
            for pos in current_positions:
                pair = pos['symbol']
                base, quote = pair[:3], pair[3:]
                
                # Contar si comparte alguna divisa
                if new_base in [base, quote] or new_quote in [base, quote]:
                    count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Error contando exposición de divisa: {e}")
            return 0
    
    def get_diversification_score(self, pairs: List[str]) -> float:
        """Calcular score de diversificación de una lista de pares"""
        try:
            if len(pairs) <= 1:
                return 1.0 if len(pairs) == 1 else 0.0
            
            total_correlation = 0.0
            pair_count = 0
            
            for i, pair1 in enumerate(pairs):
                for pair2 in pairs[i+1:]:
                    correlation = abs(self._get_pair_correlation(pair1, pair2))
                    total_correlation += correlation
                    pair_count += 1
            
            avg_correlation = total_correlation / pair_count if pair_count > 0 else 0
            diversification_score = 1.0 - avg_correlation
            
            return max(0.0, min(1.0, diversification_score))
            
        except Exception as e:
            logger.error(f"Error calculando score de diversificación: {e}")
            return 0.5
    
    def get_optimal_pair_weights(self, pairs: List[str], target_risk: float = 0.02) -> Dict[str, float]:
        """Calcular pesos óptimos para cada par basado en correlaciones"""
        try:
            if len(pairs) == 1:
                return {pairs[0]: 1.0}
            
            # Implementación simplificada de optimización de portafolio
            base_weight = 1.0 / len(pairs)  # Peso igual inicial
            weights = {}
            
            for pair in pairs:
                # Ajustar peso basado en correlaciones con otros pares
                correlation_penalty = 0.0
                
                for other_pair in pairs:
                    if pair != other_pair:
                        correlation = abs(self._get_pair_correlation(pair, other_pair))
                        correlation_penalty += correlation
                
                # Reducir peso si tiene alta correlación con otros
                avg_correlation = correlation_penalty / (len(pairs) - 1) if len(pairs) > 1 else 0
                adjusted_weight = base_weight * (1.0 - avg_correlation * 0.5)
                weights[pair] = max(0.1, adjusted_weight)  # Peso mínimo 10%
            
            # Normalizar pesos para que sumen 1.0
            total_weight = sum(weights.values())
            if total_weight > 0:
                weights = {pair: weight / total_weight for pair, weight in weights.items()}
            
            return weights
            
        except Exception as e:
            logger.error(f"Error calculando pesos óptimos: {e}")
            return {pair: 1.0/len(pairs) for pair in pairs}
    
    def get_correlation_report(self, pairs: List[str]) -> Dict:
        """Generar reporte completo de correlaciones"""
        try:
            report = {
                'pairs_analyzed': pairs,
                'correlation_matrix': {},
                'diversification_score': self.get_diversification_score(pairs),
                'optimal_weights': self.get_optimal_pair_weights(pairs),
                'high_correlation_warnings': []
            }
            
            # Matriz de correlaciones
            for pair1 in pairs:
                report['correlation_matrix'][pair1] = {}
                for pair2 in pairs:
                    correlation = self._get_pair_correlation(pair1, pair2)
                    report['correlation_matrix'][pair1][pair2] = round(correlation, 3)
                    
                    # Advertencias de alta correlación
                    if pair1 != pair2 and abs(correlation) > 0.7:
                        report['high_correlation_warnings'].append({
                            'pair1': pair1,
                            'pair2': pair2,
                            'correlation': round(correlation, 3),
                            'warning': 'Alta correlación detectada'
                        })
            
            return report
            
        except Exception as e:
            logger.error(f"Error generando reporte de correlaciones: {e}")
            return {'error': str(e)}
    
    def get_supported_pairs(self) -> List[str]:
        """Obtener lista de pares soportados"""
        return list(self.supported_pairs.keys())
    
    def get_pair_info(self, pair: str) -> Dict:
        """Obtener información detallada de un par"""
        return self.supported_pairs.get(pair, {})
    
    async def get_session_pair_recommendations(self) -> Dict[str, List[str]]:
        """Obtener recomendaciones de pares por sesión"""
        try:
            recommendations = {}
            sessions = ['asian', 'london', 'new_york', 'overlap']
            
            for session in sessions:
                recommendations[session] = await self.get_optimal_pairs_for_session(session, max_pairs=4)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error obteniendo recomendaciones por sesión: {e}")
            return {'error': str(e)}

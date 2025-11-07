"""
Sistema de Machine Learning Adaptativo en Tiempo Real
Aprende de cada trade y optimiza parámetros automáticamente
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
import pickle
from collections import deque
import asyncio

logger = logging.getLogger(__name__)

class RealTimeMLSystem:
    def __init__(self):
        # Configuración del sistema
        self.learning_rate = 0.01
        self.memory_size = 1000
        self.min_samples_for_learning = 50
        
        # Memoria de trades
        self.trade_memory = deque(maxlen=self.memory_size)
        self.feature_memory = deque(maxlen=self.memory_size)
        
        # Parámetros adaptativos
        self.adaptive_params = {
            'min_confidence': 75.0,
            'risk_multiplier': 1.0,
            'volatility_threshold': 1.5,
            'trend_strength_min': 0.6,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'macd_threshold': 0.0001,
            'bb_squeeze_threshold': 0.02
        }
        
        # Pesos de indicadores (aprende cuáles son más importantes)
        self.indicator_weights = {
            'rsi': 1.0,
            'macd': 1.0,
            'bb_position': 1.0,
            'ema_alignment': 1.0,
            'atr': 1.0,
            'adx': 1.0,
            'momentum': 1.0,
            'volume': 1.0
        }
        
        # Red neuronal simple (pesos)
        self.neural_weights = {
            'input_to_hidden': np.random.randn(8, 16) * 0.1,  # 8 inputs, 16 hidden
            'hidden_to_output': np.random.randn(16, 3) * 0.1,  # 16 hidden, 3 outputs (BUY/SELL/HOLD)
            'hidden_bias': np.zeros(16),
            'output_bias': np.zeros(3)
        }
        
        # Estadísticas de aprendizaje
        self.learning_stats = {
            'total_trades_learned': 0,
            'accuracy_improvement': 0.0,
            'last_optimization': None,
            'parameters_optimized': 0,
            'neural_updates': 0
        }
        
        # Predictor de volatilidad
        self.volatility_predictor = {
            'recent_atr': deque(maxlen=50),
            'volatility_patterns': {},
            'prediction_accuracy': 0.0
        }
        
        # Sistema de optimización genética
        self.genetic_system = {
            'population_size': 10,
            'mutation_rate': 0.1,
            'crossover_rate': 0.7,
            'generations': 0,
            'best_fitness': 0.0
        }
        
    def extract_features(self, market_data: Dict, indicators: Dict) -> np.ndarray:
        """Extraer características para ML"""
        try:
            features = []
            
            # Características de indicadores técnicos
            features.append(indicators.get('rsi', 50) / 100.0)  # Normalizar 0-1
            features.append(np.tanh(indicators.get('macd', 0) * 10000))  # Normalizar
            features.append(indicators.get('bb_position', 0.5))  # Ya normalizado 0-1
            features.append(np.tanh(indicators.get('ema_alignment', 0)))  # -1 a 1
            features.append(min(1.0, indicators.get('atr', 0.001) * 1000))  # Normalizar ATR
            features.append(indicators.get('adx', 25) / 100.0)  # Normalizar ADX
            features.append(np.tanh(indicators.get('momentum', 0) * 100))  # Normalizar momentum
            features.append(min(1.0, indicators.get('volume_ratio', 1.0)))  # Normalizar volumen
            
            return np.array(features, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Error extrayendo características: {e}")
            return np.zeros(8, dtype=np.float32)
    
    def neural_network_predict(self, features: np.ndarray) -> Tuple[str, float]:
        """Predicción usando red neuronal simple"""
        try:
            # Forward pass
            hidden = np.maximum(0, np.dot(features, self.neural_weights['input_to_hidden']) + 
                              self.neural_weights['hidden_bias'])  # ReLU
            
            output = np.dot(hidden, self.neural_weights['hidden_to_output']) + self.neural_weights['output_bias']
            
            # Softmax para probabilidades
            exp_output = np.exp(output - np.max(output))
            probabilities = exp_output / np.sum(exp_output)
            
            # Mapear a señales
            signals = ['BUY', 'SELL', 'HOLD']
            predicted_signal = signals[np.argmax(probabilities)]
            confidence = float(np.max(probabilities) * 100)
            
            return predicted_signal, confidence
            
        except Exception as e:
            logger.error(f"Error en predicción neural: {e}")
            return 'HOLD', 50.0
    
    def update_neural_network(self, features: np.ndarray, actual_result: bool, predicted_signal: str):
        """Actualizar red neuronal con resultado real"""
        try:
            # Crear target (resultado esperado)
            target = np.zeros(3)
            if actual_result:  # Trade exitoso
                if predicted_signal == 'BUY':
                    target[0] = 1.0
                elif predicted_signal == 'SELL':
                    target[1] = 1.0
                else:
                    target[2] = 1.0
            else:  # Trade fallido
                target[2] = 1.0  # Debería haber sido HOLD
            
            # Forward pass
            hidden = np.maximum(0, np.dot(features, self.neural_weights['input_to_hidden']) + 
                              self.neural_weights['hidden_bias'])
            
            output = np.dot(hidden, self.neural_weights['hidden_to_output']) + self.neural_weights['output_bias']
            exp_output = np.exp(output - np.max(output))
            probabilities = exp_output / np.sum(exp_output)
            
            # Backward pass (gradiente simple)
            output_error = target - probabilities
            
            # Actualizar pesos de salida
            self.neural_weights['hidden_to_output'] += self.learning_rate * np.outer(hidden, output_error)
            self.neural_weights['output_bias'] += self.learning_rate * output_error
            
            # Actualizar pesos ocultos (simplificado)
            hidden_error = np.dot(output_error, self.neural_weights['hidden_to_output'].T)
            hidden_error[hidden <= 0] = 0  # Derivada de ReLU
            
            self.neural_weights['input_to_hidden'] += self.learning_rate * np.outer(features, hidden_error)
            self.neural_weights['hidden_bias'] += self.learning_rate * hidden_error
            
            self.learning_stats['neural_updates'] += 1
            
        except Exception as e:
            logger.error(f"Error actualizando red neuronal: {e}")
    
    def record_trade_result(self, trade_data: Dict):
        """Registrar resultado de trade para aprendizaje"""
        try:
            # Validar datos de entrada
            required_fields = ['success', 'confidence', 'indicators']
            if not all(field in trade_data for field in required_fields):
                logger.warning("Datos de trade incompletos para ML")
                return
            
            # Extraer características
            features = self.extract_features({}, trade_data['indicators'])
            
            # Almacenar en memoria
            self.trade_memory.append({
                'timestamp': datetime.now(),
                'success': trade_data['success'],
                'profit': trade_data.get('profit', 0),
                'confidence': trade_data['confidence'],
                'signal': trade_data.get('signal', 'HOLD'),
                'features': features,
                'session': trade_data.get('session', 'unknown'),
                'market_regime': trade_data.get('market_regime', 'unknown')
            })
            
            self.feature_memory.append(features)
            
            # Actualizar red neuronal si tenemos predicción previa
            if 'predicted_signal' in trade_data:
                self.update_neural_network(
                    features, 
                    trade_data['success'], 
                    trade_data['predicted_signal']
                )
            
            # Aprender si tenemos suficientes muestras
            if len(self.trade_memory) >= self.min_samples_for_learning:
                self._learn_from_recent_trades()
            
            self.learning_stats['total_trades_learned'] += 1
            
        except Exception as e:
            logger.error(f"Error registrando trade para ML: {e}")
    
    def _learn_from_recent_trades(self):
        """Aprender de trades recientes"""
        try:
            recent_trades = list(self.trade_memory)[-50:]  # Últimos 50 trades
            
            if len(recent_trades) < 20:
                return
            
            # Calcular métricas de rendimiento
            total_trades = len(recent_trades)
            successful_trades = sum(1 for trade in recent_trades if trade['success'])
            win_rate = successful_trades / total_trades
            
            # Optimizar parámetros basado en rendimiento
            self._optimize_confidence_threshold(recent_trades, win_rate)
            self._optimize_indicator_weights(recent_trades)
            self._update_volatility_predictor(recent_trades)
            
            self.learning_stats['last_optimization'] = datetime.now()
            self.learning_stats['parameters_optimized'] += 1
            
        except Exception as e:
            logger.error(f"Error aprendiendo de trades recientes: {e}")
    
    def _optimize_confidence_threshold(self, trades: List[Dict], current_win_rate: float):
        """Optimizar umbral de confianza mínima"""
        try:
            # Analizar relación entre confianza y éxito
            confidence_success = {}
            
            for trade in trades:
                conf_bucket = int(trade['confidence'] / 5) * 5  # Buckets de 5%
                if conf_bucket not in confidence_success:
                    confidence_success[conf_bucket] = {'total': 0, 'success': 0}
                
                confidence_success[conf_bucket]['total'] += 1
                if trade['success']:
                    confidence_success[conf_bucket]['success'] += 1
            
            # Encontrar umbral óptimo
            best_threshold = self.adaptive_params['min_confidence']
            best_score = 0
            
            for conf, stats in confidence_success.items():
                if stats['total'] >= 5:  # Mínimo 5 trades
                    win_rate = stats['success'] / stats['total']
                    # Score = win_rate * número_de_trades (favorece umbrales con más datos)
                    score = win_rate * min(stats['total'], 20)
                    
                    if score > best_score and conf >= 60:  # Mínimo 60% confianza
                        best_score = score
                        best_threshold = conf
            
            # Ajustar gradualmente
            current_threshold = self.adaptive_params['min_confidence']
            adjustment = (best_threshold - current_threshold) * 0.1  # 10% del cambio
            
            self.adaptive_params['min_confidence'] = max(60, min(90, current_threshold + adjustment))
            
        except Exception as e:
            logger.error(f"Error optimizando umbral de confianza: {e}")
    
    def _optimize_indicator_weights(self, trades: List[Dict]):
        """Optimizar pesos de indicadores técnicos"""
        try:
            # Calcular correlación entre indicadores y éxito
            indicator_correlations = {}
            
            for indicator in self.indicator_weights.keys():
                values = []
                results = []
                
                for trade in trades:
                    if 'features' in trade and len(trade['features']) >= 8:
                        # Mapear características a indicadores
                        feature_map = {
                            'rsi': 0, 'macd': 1, 'bb_position': 2, 'ema_alignment': 3,
                            'atr': 4, 'adx': 5, 'momentum': 6, 'volume': 7
                        }
                        
                        if indicator in feature_map:
                            idx = feature_map[indicator]
                            values.append(trade['features'][idx])
                            results.append(1 if trade['success'] else 0)
                
                if len(values) >= 10:
                    correlation = np.corrcoef(values, results)[0, 1]
                    if not np.isnan(correlation):
                        indicator_correlations[indicator] = abs(correlation)
            
            # Ajustar pesos basado en correlaciones
            for indicator, correlation in indicator_correlations.items():
                current_weight = self.indicator_weights[indicator]
                # Ajustar peso basado en correlación (más correlación = más peso)
                target_weight = 0.5 + correlation * 1.5  # Rango 0.5 - 2.0
                adjustment = (target_weight - current_weight) * 0.05  # 5% del cambio
                
                self.indicator_weights[indicator] = max(0.1, min(3.0, current_weight + adjustment))
            
        except Exception as e:
            logger.error(f"Error optimizando pesos de indicadores: {e}")
    
    def _update_volatility_predictor(self, trades: List[Dict]):
        """Actualizar predictor de volatilidad"""
        try:
            # Recopilar datos de ATR
            for trade in trades:
                if 'features' in trade and len(trade['features']) >= 5:
                    atr_value = trade['features'][4]  # ATR normalizado
                    self.volatility_predictor['recent_atr'].append(atr_value)
            
            # Calcular patrones de volatilidad por sesión
            session_volatility = {}
            for trade in trades:
                session = trade.get('session', 'unknown')
                if session not in session_volatility:
                    session_volatility[session] = []
                
                if 'features' in trade and len(trade['features']) >= 5:
                    session_volatility[session].append(trade['features'][4])
            
            # Actualizar patrones
            for session, atr_values in session_volatility.items():
                if len(atr_values) >= 5:
                    self.volatility_predictor['volatility_patterns'][session] = {
                        'mean': np.mean(atr_values),
                        'std': np.std(atr_values),
                        'samples': len(atr_values)
                    }
            
        except Exception as e:
            logger.error(f"Error actualizando predictor de volatilidad: {e}")
    
    def predict_market_signal(self, indicators: Dict, market_data: Dict) -> Tuple[str, float, str]:
        """Predecir señal de mercado usando ML"""
        try:
            # Extraer características
            features = self.extract_features(market_data, indicators)
            
            # Predicción neural
            neural_signal, neural_confidence = self.neural_network_predict(features)
            
            # Ajustar confianza con pesos de indicadores
            weighted_confidence = self._calculate_weighted_confidence(indicators, neural_confidence)
            
            # Aplicar filtros adaptativos
            if weighted_confidence < self.adaptive_params['min_confidence']:
                return 'HOLD', weighted_confidence, 'Confianza insuficiente'
            
            # Verificar condiciones de volatilidad
            predicted_volatility = self._predict_volatility(market_data.get('session', 'unknown'))
            if predicted_volatility > self.adaptive_params['volatility_threshold']:
                return 'HOLD', weighted_confidence * 0.8, 'Volatilidad alta predicha'
            
            return neural_signal, weighted_confidence, 'ML prediction'
            
        except Exception as e:
            logger.error(f"Error en predicción ML: {e}")
            return 'HOLD', 50.0, 'Error en ML'
    
    def _calculate_weighted_confidence(self, indicators: Dict, base_confidence: float) -> float:
        """Calcular confianza ponderada por importancia de indicadores"""
        try:
            weighted_score = 0.0
            total_weight = 0.0
            
            # Mapear indicadores a pesos
            indicator_mapping = {
                'rsi': indicators.get('rsi', 50),
                'macd': indicators.get('macd', 0) * 10000,  # Desnormalizar
                'bb_position': indicators.get('bb_position', 0.5),
                'ema_alignment': indicators.get('ema_alignment', 0),
                'atr': indicators.get('atr', 0.001) * 1000,  # Desnormalizar
                'adx': indicators.get('adx', 25),
                'momentum': indicators.get('momentum', 0) * 100,  # Desnormalizar
                'volume': indicators.get('volume_ratio', 1.0)
            }
            
            for indicator, value in indicator_mapping.items():
                weight = self.indicator_weights.get(indicator, 1.0)
                
                # Calcular score del indicador (simplificado)
                if indicator == 'rsi':
                    score = 1.0 if (value < 30 or value > 70) else 0.5
                elif indicator == 'adx':
                    score = min(1.0, value / 30)  # Más ADX = más score
                else:
                    score = min(1.0, abs(value))  # Score basado en magnitud
                
                weighted_score += score * weight
                total_weight += weight
            
            # Ajustar confianza base
            if total_weight > 0:
                adjustment_factor = weighted_score / total_weight
                adjusted_confidence = base_confidence * adjustment_factor
                return max(0, min(100, adjusted_confidence))
            
            return base_confidence
            
        except Exception as e:
            logger.error(f"Error calculando confianza ponderada: {e}")
            return base_confidence
    
    def _predict_volatility(self, session: str) -> float:
        """Predecir volatilidad para la sesión actual"""
        try:
            if session in self.volatility_predictor['volatility_patterns']:
                pattern = self.volatility_predictor['volatility_patterns'][session]
                return pattern['mean'] + pattern['std']  # Predicción conservadora
            
            # Fallback: usar promedio reciente
            if len(self.volatility_predictor['recent_atr']) > 0:
                return np.mean(list(self.volatility_predictor['recent_atr']))
            
            return 1.0  # Valor por defecto
            
        except Exception as e:
            logger.error(f"Error prediciendo volatilidad: {e}")
            return 1.0
    
    def get_adaptive_parameters(self) -> Dict:
        """Obtener parámetros adaptativos actuales"""
        return self.adaptive_params.copy()
    
    def get_indicator_weights(self) -> Dict:
        """Obtener pesos actuales de indicadores"""
        return self.indicator_weights.copy()
    
    def get_learning_statistics(self) -> Dict:
        """Obtener estadísticas de aprendizaje"""
        stats = self.learning_stats.copy()
        
        # Calcular métricas adicionales
        if len(self.trade_memory) > 0:
            recent_trades = list(self.trade_memory)[-20:]
            if recent_trades:
                win_rate = sum(1 for t in recent_trades if t['success']) / len(recent_trades)
                avg_profit = sum(t['profit'] for t in recent_trades) / len(recent_trades)
                
                stats.update({
                    'recent_win_rate': win_rate,
                    'recent_avg_profit': avg_profit,
                    'total_trades_in_memory': len(self.trade_memory),
                    'current_min_confidence': self.adaptive_params['min_confidence']
                })
        
        return stats
    
    def save_model(self, filepath: str):
        """Guardar modelo ML en archivo"""
        try:
            model_data = {
                'adaptive_params': self.adaptive_params,
                'indicator_weights': self.indicator_weights,
                'neural_weights': {k: v.tolist() if isinstance(v, np.ndarray) else v 
                                 for k, v in self.neural_weights.items()},
                'learning_stats': self.learning_stats,
                'volatility_predictor': {
                    'volatility_patterns': self.volatility_predictor['volatility_patterns'],
                    'prediction_accuracy': self.volatility_predictor['prediction_accuracy']
                }
            }
            
            with open(filepath, 'w') as f:
                json.dump(model_data, f, indent=2, default=str)
            
            logger.info(f"Modelo ML guardado en: {filepath}")
            
        except Exception as e:
            logger.error(f"Error guardando modelo ML: {e}")
    
    def load_model(self, filepath: str):
        """Cargar modelo ML desde archivo"""
        try:
            with open(filepath, 'r') as f:
                model_data = json.load(f)
            
            self.adaptive_params = model_data.get('adaptive_params', self.adaptive_params)
            self.indicator_weights = model_data.get('indicator_weights', self.indicator_weights)
            
            # Cargar pesos neurales
            neural_data = model_data.get('neural_weights', {})
            for key, value in neural_data.items():
                if isinstance(value, list):
                    self.neural_weights[key] = np.array(value, dtype=np.float32)
            
            self.learning_stats = model_data.get('learning_stats', self.learning_stats)
            
            # Cargar predictor de volatilidad
            vol_data = model_data.get('volatility_predictor', {})
            self.volatility_predictor['volatility_patterns'] = vol_data.get('volatility_patterns', {})
            self.volatility_predictor['prediction_accuracy'] = vol_data.get('prediction_accuracy', 0.0)
            
            logger.info(f"Modelo ML cargado desde: {filepath}")
            
        except Exception as e:
            logger.error(f"Error cargando modelo ML: {e}")
    
    def reset_learning(self):
        """Reiniciar sistema de aprendizaje"""
        try:
            self.trade_memory.clear()
            self.feature_memory.clear()
            
            # Reinicializar red neuronal
            self.neural_weights = {
                'input_to_hidden': np.random.randn(8, 16) * 0.1,
                'hidden_to_output': np.random.randn(16, 3) * 0.1,
                'hidden_bias': np.zeros(16),
                'output_bias': np.zeros(3)
            }
            
            # Reinicializar estadísticas
            self.learning_stats = {
                'total_trades_learned': 0,
                'accuracy_improvement': 0.0,
                'last_optimization': None,
                'parameters_optimized': 0,
                'neural_updates': 0
            }
            
            logger.info("Sistema de aprendizaje ML reiniciado")
            
        except Exception as e:
            logger.error(f"Error reiniciando ML: {e}")
    
    def get_model_summary(self) -> Dict:
        """Obtener resumen del modelo ML"""
        try:
            return {
                'model_type': 'Real-Time Adaptive ML',
                'neural_network': {
                    'input_size': 8,
                    'hidden_size': 16,
                    'output_size': 3,
                    'total_parameters': 8*16 + 16*3 + 16 + 3
                },
                'memory_usage': {
                    'trade_memory': len(self.trade_memory),
                    'max_memory': self.memory_size
                },
                'learning_progress': self.learning_stats,
                'adaptive_parameters': len(self.adaptive_params),
                'indicator_weights': len(self.indicator_weights),
                'volatility_patterns': len(self.volatility_predictor['volatility_patterns'])
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen del modelo: {e}")
            return {'error': str(e)}

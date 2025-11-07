"""
Sistema de Machine Learning Adaptativo
El bot aprende de sus propios trades y se optimiza automáticamente
"""

import json
import os
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class AdaptiveLearningSystem:
    def __init__(self):
        self.learning_data_file = "data/learning_data.json"
        self.model_file = "data/adaptive_model.json"
        
        # Crear directorio si no existe
        os.makedirs("data", exist_ok=True)
        
        # Memoria de trades
        self.trade_memory = deque(maxlen=1000)  # Últimos 1000 trades
        
        # Pesos adaptativos para indicadores
        self.indicator_weights = {
            'rsi': 1.0,
            'macd': 1.0,
            'bollinger': 1.0,
            'sma_cross': 1.0,
            'ema_cross': 1.0,
            'stochastic': 1.0,
            'atr': 1.0,
            'momentum': 1.0
        }
        
        # Parámetros adaptativos
        self.adaptive_params = {
            'min_confidence': 78.0,
            'risk_multiplier': 1.0,
            'sl_multiplier': 1.0,
            'tp_multiplier': 1.0,
            'session_preferences': {
                'asian': 0.8,
                'london': 1.2,
                'new_york': 1.1,
                'overlap': 1.5
            }
        }
        
        # Estadísticas de aprendizaje
        self.learning_stats = {
            'total_trades_learned': 0,
            'accuracy_improvement': 0.0,
            'last_optimization': None,
            'learning_cycles': 0
        }
        
        # Cargar datos existentes
        self.load_learning_data()
        
    def load_learning_data(self):
        """Cargar datos de aprendizaje previos"""
        try:
            if os.path.exists(self.learning_data_file):
                with open(self.learning_data_file, 'r') as f:
                    data = json.load(f)
                    
                self.trade_memory = deque(data.get('trades', []), maxlen=1000)
                self.indicator_weights = data.get('weights', self.indicator_weights)
                self.adaptive_params = data.get('params', self.adaptive_params)
                self.learning_stats = data.get('stats', self.learning_stats)
                
                logger.info(f"Datos de aprendizaje cargados: {len(self.trade_memory)} trades")
                
        except Exception as e:
            logger.error(f"Error cargando datos de aprendizaje: {e}")
    
    def save_learning_data(self):
        """Guardar datos de aprendizaje"""
        try:
            data = {
                'trades': list(self.trade_memory),
                'weights': self.indicator_weights,
                'params': self.adaptive_params,
                'stats': self.learning_stats,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.learning_data_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
            logger.info("Datos de aprendizaje guardados")
            
        except Exception as e:
            logger.error(f"Error guardando datos de aprendizaje: {e}")
    
    def record_trade(self, trade_data: Dict):
        """Registrar un trade para aprendizaje"""
        try:
            # Enriquecer datos del trade
            enriched_trade = {
                'timestamp': datetime.now().isoformat(),
                'entry_time': trade_data.get('entry_time'),
                'exit_time': trade_data.get('exit_time'),
                'signal': trade_data.get('signal'),
                'confidence': trade_data.get('confidence'),
                'profit': trade_data.get('profit', 0),
                'pips': trade_data.get('pips', 0),
                'success': trade_data.get('profit', 0) > 0,
                'indicators': trade_data.get('indicators', {}),
                'market_regime': trade_data.get('market_regime', {}),
                'session': self._get_current_session(),
                'hour': datetime.now().hour,
                'weekday': datetime.now().weekday(),
                'reasons': trade_data.get('reasons', [])
            }
            
            self.trade_memory.append(enriched_trade)
            self.learning_stats['total_trades_learned'] += 1
            
            # Aprender cada 10 trades
            if len(self.trade_memory) >= 10 and len(self.trade_memory) % 10 == 0:
                self.learn_from_trades()
            
            # Guardar datos
            self.save_learning_data()
            
            logger.info(f"Trade registrado para aprendizaje: {trade_data.get('signal')} - Profit: ${trade_data.get('profit', 0):.2f}")
            
        except Exception as e:
            logger.error(f"Error registrando trade: {e}")
    
    def learn_from_trades(self):
        """Aprender de los trades recientes y optimizar parámetros"""
        try:
            if len(self.trade_memory) < 20:
                return
            
            logger.info("🧠 Iniciando ciclo de aprendizaje...")
            
            # Convertir a DataFrame para análisis
            df = pd.DataFrame(list(self.trade_memory))
            
            # Aprender de indicadores
            self._learn_indicator_performance(df)
            
            # Aprender de sesiones
            self._learn_session_performance(df)
            
            # Aprender de confianza
            self._learn_confidence_optimization(df)
            
            # Aprender de gestión de riesgo
            self._learn_risk_management(df)
            
            # Actualizar estadísticas
            self.learning_stats['learning_cycles'] += 1
            self.learning_stats['last_optimization'] = datetime.now().isoformat()
            
            # Calcular mejora de precisión
            recent_trades = df.tail(50)
            if len(recent_trades) >= 20:
                recent_accuracy = recent_trades['success'].mean()
                old_trades = df.head(50) if len(df) >= 100 else df.head(len(df)//2)
                old_accuracy = old_trades['success'].mean() if len(old_trades) > 0 else 0
                
                self.learning_stats['accuracy_improvement'] = recent_accuracy - old_accuracy
            
            logger.info(f"✅ Ciclo de aprendizaje completado. Mejora de precisión: {self.learning_stats['accuracy_improvement']:.1%}")
            
        except Exception as e:
            logger.error(f"Error en aprendizaje: {e}")
    
    def _learn_indicator_performance(self, df: pd.DataFrame):
        """Aprender qué indicadores son más efectivos"""
        try:
            # Analizar correlación entre indicadores y éxito
            successful_trades = df[df['success'] == True]
            failed_trades = df[df['success'] == False]
            
            if len(successful_trades) < 5 or len(failed_trades) < 5:
                return
            
            # Analizar razones de trades exitosos vs fallidos
            successful_reasons = []
            failed_reasons = []
            
            for _, trade in successful_trades.iterrows():
                if 'reasons' in trade and trade['reasons']:
                    successful_reasons.extend(trade['reasons'])
            
            for _, trade in failed_trades.iterrows():
                if 'reasons' in trade and trade['reasons']:
                    failed_reasons.extend(trade['reasons'])
            
            # Calcular efectividad de cada razón/indicador
            reason_effectiveness = {}
            
            for reason in set(successful_reasons + failed_reasons):
                success_count = successful_reasons.count(reason)
                fail_count = failed_reasons.count(reason)
                total = success_count + fail_count
                
                if total >= 3:  # Mínimo 3 ocurrencias
                    effectiveness = success_count / total
                    reason_effectiveness[reason] = effectiveness
            
            # Actualizar pesos de indicadores
            for reason, effectiveness in reason_effectiveness.items():
                for indicator in self.indicator_weights.keys():
                    if indicator.lower() in reason.lower():
                        # Ajustar peso basado en efectividad
                        if effectiveness > 0.7:
                            self.indicator_weights[indicator] = min(1.5, self.indicator_weights[indicator] * 1.1)
                        elif effectiveness < 0.4:
                            self.indicator_weights[indicator] = max(0.5, self.indicator_weights[indicator] * 0.9)
            
            logger.info(f"Pesos de indicadores actualizados: {self.indicator_weights}")
            
        except Exception as e:
            logger.error(f"Error aprendiendo indicadores: {e}")
    
    def _learn_session_performance(self, df: pd.DataFrame):
        """Aprender qué sesiones son más rentables"""
        try:
            session_performance = df.groupby('session').agg({
                'success': 'mean',
                'profit': 'mean'
            }).to_dict()
            
            if 'success' in session_performance:
                for session, success_rate in session_performance['success'].items():
                    if session in self.adaptive_params['session_preferences']:
                        if success_rate > 0.6:
                            self.adaptive_params['session_preferences'][session] = min(1.8, 
                                self.adaptive_params['session_preferences'][session] * 1.05)
                        elif success_rate < 0.4:
                            self.adaptive_params['session_preferences'][session] = max(0.5,
                                self.adaptive_params['session_preferences'][session] * 0.95)
            
            logger.info(f"Preferencias de sesión actualizadas: {self.adaptive_params['session_preferences']}")
            
        except Exception as e:
            logger.error(f"Error aprendiendo sesiones: {e}")
    
    def _learn_confidence_optimization(self, df: pd.DataFrame):
        """Optimizar el nivel de confianza mínima"""
        try:
            # Analizar relación entre confianza y éxito
            confidence_bins = pd.cut(df['confidence'], bins=[0, 70, 75, 80, 85, 90, 100])
            confidence_performance = df.groupby(confidence_bins)['success'].mean()
            
            # Encontrar el punto óptimo
            best_confidence = 78.0
            best_performance = 0.0
            
            for bin_range, performance in confidence_performance.items():
                if pd.notna(performance) and performance > best_performance:
                    best_performance = performance
                    # Usar el punto medio del bin
                    best_confidence = (bin_range.left + bin_range.right) / 2
            
            # Ajustar confianza mínima gradualmente
            current_confidence = self.adaptive_params['min_confidence']
            target_confidence = best_confidence
            
            # Cambio gradual (máximo 2 puntos por ciclo)
            if abs(target_confidence - current_confidence) > 2:
                if target_confidence > current_confidence:
                    self.adaptive_params['min_confidence'] = current_confidence + 2
                else:
                    self.adaptive_params['min_confidence'] = current_confidence - 2
            else:
                self.adaptive_params['min_confidence'] = target_confidence
            
            # Limitar entre 70 y 95
            self.adaptive_params['min_confidence'] = max(70, min(95, self.adaptive_params['min_confidence']))
            
            logger.info(f"Confianza mínima optimizada: {self.adaptive_params['min_confidence']:.1f}%")
            
        except Exception as e:
            logger.error(f"Error optimizando confianza: {e}")
    
    def _learn_risk_management(self, df: pd.DataFrame):
        """Optimizar gestión de riesgo"""
        try:
            # Analizar trades por profit factor
            recent_trades = df.tail(50)
            
            if len(recent_trades) < 20:
                return
            
            winning_trades = recent_trades[recent_trades['success'] == True]
            losing_trades = recent_trades[recent_trades['success'] == False]
            
            if len(winning_trades) > 0 and len(losing_trades) > 0:
                avg_win = winning_trades['profit'].mean()
                avg_loss = abs(losing_trades['profit'].mean())
                
                current_profit_factor = avg_win / avg_loss if avg_loss > 0 else 1
                
                # Ajustar multiplicadores basado en profit factor
                if current_profit_factor > 2.0:
                    # Buen profit factor, ser más agresivo
                    self.adaptive_params['risk_multiplier'] = min(1.3, self.adaptive_params['risk_multiplier'] * 1.02)
                elif current_profit_factor < 1.2:
                    # Mal profit factor, ser más conservador
                    self.adaptive_params['risk_multiplier'] = max(0.7, self.adaptive_params['risk_multiplier'] * 0.98)
                
                logger.info(f"Multiplicador de riesgo ajustado: {self.adaptive_params['risk_multiplier']:.2f}")
            
        except Exception as e:
            logger.error(f"Error optimizando gestión de riesgo: {e}")
    
    def get_adaptive_confidence(self, base_confidence: float, current_session: str) -> float:
        """Obtener confianza ajustada por aprendizaje"""
        try:
            # Aplicar peso de sesión
            session_multiplier = self.adaptive_params['session_preferences'].get(current_session, 1.0)
            
            # Ajustar confianza
            adjusted_confidence = base_confidence * session_multiplier
            
            return min(100, max(0, adjusted_confidence))
            
        except Exception as e:
            logger.error(f"Error calculando confianza adaptativa: {e}")
            return base_confidence
    
    def get_adaptive_weights(self) -> Dict[str, float]:
        """Obtener pesos adaptativos de indicadores"""
        return self.indicator_weights.copy()
    
    def get_adaptive_params(self) -> Dict:
        """Obtener parámetros adaptativos actuales"""
        return self.adaptive_params.copy()
    
    def get_learning_stats(self) -> Dict:
        """Obtener estadísticas de aprendizaje"""
        stats = self.learning_stats.copy()
        
        if len(self.trade_memory) >= 20:
            recent_trades = list(self.trade_memory)[-20:]
            recent_success_rate = sum(1 for t in recent_trades if t.get('success', False)) / len(recent_trades)
            stats['recent_success_rate'] = recent_success_rate
            
            if len(self.trade_memory) >= 50:
                older_trades = list(self.trade_memory)[-50:-20]
                older_success_rate = sum(1 for t in older_trades if t.get('success', False)) / len(older_trades)
                stats['improvement_trend'] = recent_success_rate - older_success_rate
        
        return stats
    
    def _get_current_session(self) -> str:
        """Determinar sesión actual"""
        hour = datetime.utcnow().hour
        
        if 13 <= hour <= 17:
            return 'overlap'
        elif 8 <= hour <= 17:
            return 'london'
        elif 13 <= hour <= 22:
            return 'new_york'
        else:
            return 'asian'
    
    def should_trade_with_ml(self, base_should_trade: bool, base_confidence: float, 
                           current_session: str, indicators: Dict) -> Tuple[bool, float, str]:
        """Decidir si operar usando machine learning"""
        try:
            if not base_should_trade:
                return False, base_confidence, "Base analysis rejected"
            
            # Aplicar confianza adaptativa
            ml_confidence = self.get_adaptive_confidence(base_confidence, current_session)
            
            # Verificar contra confianza mínima adaptativa
            min_confidence = self.adaptive_params['min_confidence']
            
            if ml_confidence < min_confidence:
                return False, ml_confidence, f"ML confidence {ml_confidence:.1f}% < {min_confidence:.1f}%"
            
            # Aplicar filtros de sesión
            session_multiplier = self.adaptive_params['session_preferences'].get(current_session, 1.0)
            
            if session_multiplier < 0.8:
                return False, ml_confidence, f"Session {current_session} not preferred (x{session_multiplier:.1f})"
            
            return True, ml_confidence, f"ML approved: {ml_confidence:.1f}% confidence in {current_session} session"
            
        except Exception as e:
            logger.error(f"Error en decisión ML: {e}")
            return base_should_trade, base_confidence, "ML error, using base analysis"

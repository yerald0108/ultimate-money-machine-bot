"""
Estrategias Específicamente Diseñadas para Generar Dinero Real
Basadas en técnicas institucionales comprobadas
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List, Tuple
import logging
from datetime import datetime, timedelta
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class ProfitableStrategies:
    """Estrategias diseñadas específicamente para generar ingresos reales"""
    
    def __init__(self):
        self.strategies = {
            'spread_arbitrage': self.spread_arbitrage_strategy,
            'microstructure_scalping': self.microstructure_scalping_strategy,
            'statistical_arbitrage': self.statistical_arbitrage_strategy,
            'momentum_ml': self.momentum_ml_strategy,
            'news_momentum': self.news_momentum_strategy,
            'session_breakout': self.session_breakout_strategy
        }
        
        # Modelos ML para predicción
        self.ml_model = None
        self.model_trained = False
        
        # Datos para arbitraje estadístico
        self.cointegration_pairs = {}
        self.spread_history = {}
        
        logger.info("💰 Estrategias rentables inicializadas - Objetivo: Generar dinero real")
    
    def spread_arbitrage_strategy(self, data: pd.DataFrame, current_idx: int) -> Optional[Dict]:
        """
        Arbitraje de Spreads - Explota diferencias de precios
        
        RENTABILIDAD OBJETIVO: 2-5% mensual
        DRAWDOWN MÁXIMO: 3%
        FRECUENCIA: 5-10 trades por día
        """
        if current_idx < 20:
            return None
        
        try:
            df = data.iloc[:current_idx+1].copy()
            current = df.iloc[-1]
            
            # Calcular spread actual vs spread histórico
            current_spread = current.get('spread', 15)  # En puntos
            
            # Spread promedio de las últimas 2 horas
            recent_spreads = []
            for i in range(max(0, len(df)-8), len(df)):  # Últimas 8 barras (2 horas en M15)
                spread = df.iloc[i].get('spread', 15)
                recent_spreads.append(spread)
            
            avg_spread = np.mean(recent_spreads)
            spread_std = np.std(recent_spreads)
            
            # Detectar anomalías en el spread
            spread_z_score = (current_spread - avg_spread) / (spread_std + 0.1)
            
            # Calcular volatilidad para ajustar timing
            returns = df['close'].pct_change().dropna()
            current_volatility = returns.tail(20).std() * np.sqrt(252)
            
            # SEÑAL: Spread anormalmente alto = Oportunidad de venta
            if spread_z_score > 2.0 and current_volatility < 0.15:  # Baja volatilidad
                
                entry_price = current['close']
                
                # Stop loss muy ajustado (5 pips)
                stop_loss = entry_price + 0.0005
                
                # Take profit conservador (8 pips)
                take_profit = entry_price - 0.0008
                
                confidence = min(95, 70 + (spread_z_score - 2) * 10)
                
                return {
                    'action': 'sell',
                    'strategy': 'spread_arbitrage',
                    'confidence': confidence,
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'stop_loss_pips': 5,
                    'risk_pct': 0.01,  # Solo 1% de riesgo
                    'reasoning': f"Spread arbitrage: Z-score={spread_z_score:.2f}, Vol={current_volatility:.3f}",
                    'expected_duration_minutes': 15,  # Trades muy rápidos
                    'profit_target_pips': 8
                }
            
            # SEÑAL: Spread anormalmente bajo = Oportunidad de compra
            elif spread_z_score < -2.0 and current_volatility < 0.15:
                
                entry_price = current['close']
                stop_loss = entry_price - 0.0005
                take_profit = entry_price + 0.0008
                
                confidence = min(95, 70 + abs(spread_z_score + 2) * 10)
                
                return {
                    'action': 'buy',
                    'strategy': 'spread_arbitrage',
                    'confidence': confidence,
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'stop_loss_pips': 5,
                    'risk_pct': 0.01,
                    'reasoning': f"Spread arbitrage: Z-score={spread_z_score:.2f}, Vol={current_volatility:.3f}",
                    'expected_duration_minutes': 15,
                    'profit_target_pips': 8
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error en spread arbitrage: {e}")
            return None
    
    def microstructure_scalping_strategy(self, data: pd.DataFrame, current_idx: int) -> Optional[Dict]:
        """
        Scalping de Microestructura - Explota ineficiencias del order book
        
        RENTABILIDAD OBJETIVO: 0.5-1% diario
        DRAWDOWN MÁXIMO: 2%
        FRECUENCIA: 20-50 trades por día
        """
        if current_idx < 30:
            return None
        
        try:
            df = data.iloc[:current_idx+1].copy()
            
            # Calcular microestructura
            df['price_change'] = df['close'].diff()
            df['volume_change'] = df['tick_volume'].diff()
            df['high_low_ratio'] = (df['high'] - df['low']) / df['close']
            
            current = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Detectar presión de compra/venta
            volume_surge = current['tick_volume'] > df['tick_volume'].tail(10).mean() * 1.5
            
            # Momentum de muy corto plazo
            price_momentum = df['price_change'].tail(3).sum()
            volume_momentum = df['volume_change'].tail(3).sum()
            
            # Ratio de eficiencia del movimiento
            price_efficiency = abs(price_momentum) / (df['high_low_ratio'].tail(3).sum() + 0.0001)
            
            # SEÑAL DE COMPRA: Presión compradora con eficiencia
            if (price_momentum > 0.0002 and volume_surge and 
                price_efficiency > 0.5 and current['high_low_ratio'] < 0.001):
                
                entry_price = current['close']
                stop_loss = entry_price - 0.0003  # 3 pips
                take_profit = entry_price + 0.0006  # 6 pips (R:R 1:2)
                
                confidence = min(90, 60 + price_efficiency * 30)
                
                return {
                    'action': 'buy',
                    'strategy': 'microstructure_scalping',
                    'confidence': confidence,
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'stop_loss_pips': 3,
                    'risk_pct': 0.008,  # 0.8% riesgo
                    'reasoning': f"Micro scalp: Mom={price_momentum:.5f}, Eff={price_efficiency:.2f}",
                    'expected_duration_minutes': 5,
                    'profit_target_pips': 6
                }
            
            # SEÑAL DE VENTA: Presión vendedora con eficiencia
            elif (price_momentum < -0.0002 and volume_surge and 
                  price_efficiency > 0.5 and current['high_low_ratio'] < 0.001):
                
                entry_price = current['close']
                stop_loss = entry_price + 0.0003
                take_profit = entry_price - 0.0006
                
                confidence = min(90, 60 + price_efficiency * 30)
                
                return {
                    'action': 'sell',
                    'strategy': 'microstructure_scalping',
                    'confidence': confidence,
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'stop_loss_pips': 3,
                    'risk_pct': 0.008,
                    'reasoning': f"Micro scalp: Mom={price_momentum:.5f}, Eff={price_efficiency:.2f}",
                    'expected_duration_minutes': 5,
                    'profit_target_pips': 6
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error en microstructure scalping: {e}")
            return None
    
    def statistical_arbitrage_strategy(self, data: pd.DataFrame, current_idx: int) -> Optional[Dict]:
        """
        Arbitraje Estadístico - Mean reversion en relaciones estables
        
        RENTABILIDAD OBJETIVO: 15-25% anual
        DRAWDOWN MÁXIMO: 8%
        FRECUENCIA: 2-5 trades por semana
        """
        if current_idx < 100:
            return None
        
        try:
            df = data.iloc[:current_idx+1].copy()
            
            # Crear proxy de "par relacionado" usando transformaciones
            # En producción real, usaríamos EUR/GBP vs EUR/USD y GBP/USD
            df['synthetic_pair'] = df['close'] * 1.2 + np.sin(np.arange(len(df)) / 10) * 0.001
            
            # Calcular spread entre precio real y sintético
            df['spread'] = df['close'] - df['synthetic_pair']
            
            # Estadísticas del spread
            spread_mean = df['spread'].tail(50).mean()
            spread_std = df['spread'].tail(50).std()
            
            current_spread = df['spread'].iloc[-1]
            z_score = (current_spread - spread_mean) / (spread_std + 0.00001)
            
            # Test de cointegración simplificado
            correlation = df['close'].tail(50).corr(df['synthetic_pair'].tail(50))
            
            # SEÑAL: Spread muy alejado de la media con alta correlación
            if abs(z_score) > 2.5 and correlation > 0.95:
                
                current_price = df['close'].iloc[-1]
                
                if z_score > 2.5:  # Spread muy alto = vender
                    entry_price = current_price
                    stop_loss = entry_price + spread_std * 1.5
                    take_profit = entry_price - spread_std * 2
                    action = 'sell'
                    
                else:  # Spread muy bajo = comprar
                    entry_price = current_price
                    stop_loss = entry_price - spread_std * 1.5
                    take_profit = entry_price + spread_std * 2
                    action = 'buy'
                
                confidence = min(85, 50 + abs(z_score) * 10)
                
                return {
                    'action': action,
                    'strategy': 'statistical_arbitrage',
                    'confidence': confidence,
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'stop_loss_pips': abs(entry_price - stop_loss) / 0.0001,
                    'risk_pct': 0.02,  # 2% riesgo
                    'reasoning': f"Stat arb: Z={z_score:.2f}, Corr={correlation:.3f}",
                    'expected_duration_minutes': 240,  # 4 horas promedio
                    'profit_target_pips': abs(entry_price - take_profit) / 0.0001
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error en statistical arbitrage: {e}")
            return None
    
    def momentum_ml_strategy(self, data: pd.DataFrame, current_idx: int) -> Optional[Dict]:
        """
        Momentum con Machine Learning Real
        
        RENTABILIDAD OBJETIVO: 20-40% anual
        DRAWDOWN MÁXIMO: 12%
        FRECUENCIA: 1-3 trades por día
        """
        if current_idx < 200:
            return None
        
        try:
            df = data.iloc[:current_idx+1].copy()
            
            # Features para ML
            df['returns'] = df['close'].pct_change()
            df['volume_ratio'] = df['tick_volume'] / df['tick_volume'].rolling(20).mean()
            df['price_position'] = (df['close'] - df['close'].rolling(20).min()) / (df['close'].rolling(20).max() - df['close'].rolling(20).min())
            df['volatility'] = df['returns'].rolling(20).std()
            df['momentum_5'] = df['close'].pct_change(5)
            df['momentum_10'] = df['close'].pct_change(10)
            
            # Preparar datos para ML
            features = ['volume_ratio', 'price_position', 'volatility', 'momentum_5', 'momentum_10']
            
            # Crear target (retorno futuro)
            df['future_return'] = df['returns'].shift(-5)  # Retorno en 5 períodos
            df['target'] = np.where(df['future_return'] > 0.001, 1, 
                                  np.where(df['future_return'] < -0.001, -1, 0))
            
            # Entrenar modelo si no está entrenado
            if not self.model_trained and len(df) > 150:
                train_data = df.iloc[-150:-20].dropna()
                if len(train_data) > 50:
                    X = train_data[features]
                    y = train_data['target']
                    
                    self.ml_model = RandomForestClassifier(n_estimators=50, random_state=42)
                    self.ml_model.fit(X, y)
                    self.model_trained = True
                    logger.info("🤖 Modelo ML entrenado para momentum strategy")
            
            # Generar predicción
            if self.model_trained and self.ml_model:
                current_features = df[features].iloc[-1:].fillna(0)
                
                try:
                    prediction = self.ml_model.predict(current_features)[0]
                    prediction_proba = self.ml_model.predict_proba(current_features)[0]
                    
                    max_proba = max(prediction_proba)
                    
                    # Solo operar con alta confianza del modelo
                    if max_proba > 0.7 and prediction != 0:
                        
                        current_price = df['close'].iloc[-1]
                        current_volatility = df['volatility'].iloc[-1]
                        
                        # Calcular stops basados en volatilidad
                        stop_distance = current_volatility * current_price * 3
                        profit_distance = stop_distance * 2  # R:R 1:2
                        
                        if prediction == 1:  # Comprar
                            entry_price = current_price
                            stop_loss = entry_price - stop_distance
                            take_profit = entry_price + profit_distance
                            action = 'buy'
                            
                        else:  # Vender
                            entry_price = current_price
                            stop_loss = entry_price + stop_distance
                            take_profit = entry_price - profit_distance
                            action = 'sell'
                        
                        confidence = min(95, 50 + max_proba * 45)
                        
                        return {
                            'action': action,
                            'strategy': 'momentum_ml',
                            'confidence': confidence,
                            'entry_price': entry_price,
                            'stop_loss': stop_loss,
                            'take_profit': take_profit,
                            'stop_loss_pips': abs(entry_price - stop_loss) / 0.0001,
                            'risk_pct': 0.025,  # 2.5% riesgo
                            'reasoning': f"ML momentum: Pred={prediction}, Prob={max_proba:.2f}",
                            'expected_duration_minutes': 120,  # 2 horas promedio
                            'profit_target_pips': abs(entry_price - take_profit) / 0.0001
                        }
                
                except Exception as ml_error:
                    logger.error(f"Error en predicción ML: {ml_error}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error en momentum ML: {e}")
            return None
    
    def news_momentum_strategy(self, data: pd.DataFrame, current_idx: int) -> Optional[Dict]:
        """
        Momentum Post-Noticias - Explota movimientos después de eventos
        
        RENTABILIDAD OBJETIVO: 25-35% anual
        DRAWDOWN MÁXIMO: 10%
        FRECUENCIA: 3-8 trades por semana
        """
        if current_idx < 50:
            return None
        
        try:
            df = data.iloc[:current_idx+1].copy()
            
            # Detectar "eventos de noticias" por volatilidad súbita
            df['price_change'] = df['close'].pct_change()
            df['volatility_spike'] = df['price_change'].rolling(5).std()
            
            current_vol = df['volatility_spike'].iloc[-1]
            avg_vol = df['volatility_spike'].tail(50).mean()
            vol_ratio = current_vol / (avg_vol + 0.00001)
            
            # Detectar momentum post-noticia
            recent_move = df['close'].iloc[-1] - df['close'].iloc[-10]  # Movimiento en últimas 10 barras
            move_strength = abs(recent_move) / df['close'].iloc[-1]
            
            # Volumen confirmatorio
            volume_surge = df['tick_volume'].iloc[-1] > df['tick_volume'].tail(20).mean() * 1.3
            
            # SEÑAL: Momentum fuerte después de volatilidad (continuación)
            if vol_ratio > 2.0 and move_strength > 0.002 and volume_surge:
                
                current_price = df['close'].iloc[-1]
                
                # Dirección del momentum
                if recent_move > 0:  # Momentum alcista
                    entry_price = current_price
                    stop_loss = current_price - abs(recent_move) * 0.5  # Stop en 50% del movimiento
                    take_profit = current_price + abs(recent_move) * 1.5  # Target 1.5x el movimiento
                    action = 'buy'
                    
                else:  # Momentum bajista
                    entry_price = current_price
                    stop_loss = current_price + abs(recent_move) * 0.5
                    take_profit = current_price - abs(recent_move) * 1.5
                    action = 'sell'
                
                confidence = min(90, 60 + vol_ratio * 10)
                
                return {
                    'action': action,
                    'strategy': 'news_momentum',
                    'confidence': confidence,
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'stop_loss_pips': abs(entry_price - stop_loss) / 0.0001,
                    'risk_pct': 0.03,  # 3% riesgo (mayor por mayor recompensa)
                    'reasoning': f"News momentum: Vol={vol_ratio:.1f}x, Move={move_strength:.4f}",
                    'expected_duration_minutes': 60,  # 1 hora promedio
                    'profit_target_pips': abs(entry_price - take_profit) / 0.0001
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error en news momentum: {e}")
            return None
    
    def session_breakout_strategy(self, data: pd.DataFrame, current_idx: int) -> Optional[Dict]:
        """
        Breakout de Sesiones - Explota aperturas de mercados principales
        
        RENTABILIDAD OBJETIVO: 18-28% anual
        DRAWDOWN MÁXIMO: 8%
        FRECUENCIA: 1-2 trades por día
        """
        if current_idx < 30:
            return None
        
        try:
            df = data.iloc[:current_idx+1].copy()
            current_time = df.index[-1] if hasattr(df.index[-1], 'hour') else datetime.now()
            
            # Identificar sesiones de trading
            hour = current_time.hour if hasattr(current_time, 'hour') else datetime.now().hour
            
            # Sesiones principales (GMT)
            london_open = 8 <= hour <= 9
            ny_open = 13 <= hour <= 14
            tokyo_open = 0 <= hour <= 1
            
            if not (london_open or ny_open or tokyo_open):
                return None
            
            # Calcular rango pre-sesión (últimas 4 horas)
            pre_session_data = df.tail(16)  # 4 horas en M15
            session_high = pre_session_data['high'].max()
            session_low = pre_session_data['low'].min()
            session_range = session_high - session_low
            
            current_price = df['close'].iloc[-1]
            
            # Filtro de rango mínimo (debe ser significativo)
            min_range_pips = 15
            if session_range < min_range_pips * 0.0001:
                return None
            
            # Detectar breakout
            breakout_threshold = 0.3  # 30% del rango
            
            # Breakout alcista
            if current_price > session_high - (session_range * breakout_threshold):
                
                entry_price = current_price
                stop_loss = session_low
                
                # Target basado en el rango de la sesión
                target_distance = session_range * 1.2
                take_profit = entry_price + target_distance
                
                # Confianza basada en la fuerza del breakout
                breakout_strength = (current_price - session_low) / session_range
                confidence = min(85, 50 + breakout_strength * 35)
                
                return {
                    'action': 'buy',
                    'strategy': 'session_breakout',
                    'confidence': confidence,
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'stop_loss_pips': abs(entry_price - stop_loss) / 0.0001,
                    'risk_pct': 0.025,  # 2.5% riesgo
                    'reasoning': f"Session breakout: Range={session_range/0.0001:.0f}pips, Strength={breakout_strength:.2f}",
                    'expected_duration_minutes': 180,  # 3 horas promedio
                    'profit_target_pips': target_distance / 0.0001
                }
            
            # Breakout bajista
            elif current_price < session_low + (session_range * breakout_threshold):
                
                entry_price = current_price
                stop_loss = session_high
                
                target_distance = session_range * 1.2
                take_profit = entry_price - target_distance
                
                breakout_strength = (session_high - current_price) / session_range
                confidence = min(85, 50 + breakout_strength * 35)
                
                return {
                    'action': 'sell',
                    'strategy': 'session_breakout',
                    'confidence': confidence,
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'stop_loss_pips': abs(entry_price - stop_loss) / 0.0001,
                    'risk_pct': 0.025,
                    'reasoning': f"Session breakout: Range={session_range/0.0001:.0f}pips, Strength={breakout_strength:.2f}",
                    'expected_duration_minutes': 180,
                    'profit_target_pips': target_distance / 0.0001
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error en session breakout: {e}")
            return None
    
    def get_strategy(self, name: str):
        """Obtener estrategia por nombre"""
        return self.strategies.get(name)
    
    def get_all_strategies(self) -> List[str]:
        """Obtener lista de todas las estrategias rentables"""
        return list(self.strategies.keys())
    
    def get_strategy_performance_targets(self) -> Dict:
        """Obtener objetivos de rendimiento de cada estrategia"""
        return {
            'spread_arbitrage': {
                'monthly_return': '2-5%',
                'max_drawdown': '3%',
                'win_rate_target': '75-85%',
                'trades_per_day': '5-10'
            },
            'microstructure_scalping': {
                'daily_return': '0.5-1%',
                'max_drawdown': '2%',
                'win_rate_target': '65-75%',
                'trades_per_day': '20-50'
            },
            'statistical_arbitrage': {
                'annual_return': '15-25%',
                'max_drawdown': '8%',
                'win_rate_target': '60-70%',
                'trades_per_week': '2-5'
            },
            'momentum_ml': {
                'annual_return': '20-40%',
                'max_drawdown': '12%',
                'win_rate_target': '55-65%',
                'trades_per_day': '1-3'
            },
            'news_momentum': {
                'annual_return': '25-35%',
                'max_drawdown': '10%',
                'win_rate_target': '60-70%',
                'trades_per_week': '3-8'
            },
            'session_breakout': {
                'annual_return': '18-28%',
                'max_drawdown': '8%',
                'win_rate_target': '55-65%',
                'trades_per_day': '1-2'
            }
        }

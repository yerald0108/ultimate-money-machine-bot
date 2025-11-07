"""
Analizador de mercado para EUR/USD
Implementa análisis técnico y generación de señales
"""

import pandas as pd
import numpy as np
import ta
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

class MarketAnalyzer:
    def __init__(self):
        self.symbol = "EURUSD"
        self.min_confidence = 70  # Confianza mínima para señales
        
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcular indicadores técnicos"""
        try:
            if df.empty or len(df) < 50:
                logger.warning("Datos insuficientes para análisis técnico")
                return df
            
            # RSI
            df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
            
            # MACD
            macd = ta.trend.MACD(df['close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_histogram'] = macd.macd_diff()
            
            # Bollinger Bands
            bollinger = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
            df['bb_upper'] = bollinger.bollinger_hband()
            df['bb_middle'] = bollinger.bollinger_mavg()
            df['bb_lower'] = bollinger.bollinger_lband()
            
            # Moving Averages
            df['sma_20'] = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator()
            df['sma_50'] = ta.trend.SMAIndicator(df['close'], window=50).sma_indicator()
            df['ema_12'] = ta.trend.EMAIndicator(df['close'], window=12).ema_indicator()
            df['ema_26'] = ta.trend.EMAIndicator(df['close'], window=26).ema_indicator()
            
            # Stochastic
            stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
            df['stoch_k'] = stoch.stoch()
            df['stoch_d'] = stoch.stoch_signal()
            
            # ATR (Average True Range)
            df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()
            
            # Williams %R
            df['williams_r'] = ta.momentum.WilliamsRIndicator(df['high'], df['low'], df['close']).williams_r()
            
            # ADX (Average Directional Index)
            df['adx'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close']).adx()
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculando indicadores técnicos: {e}")
            return df
    
    def analyze_trend(self, df: pd.DataFrame) -> Dict:
        """Analizar tendencia del mercado"""
        try:
            if df.empty or len(df) < 20:
                return {'trend': 'UNKNOWN', 'strength': 0, 'confidence': 0}
            
            latest = df.iloc[-1]
            
            # Análisis de medias móviles
            sma_trend = 'BULLISH' if latest['close'] > latest['sma_20'] > latest['sma_50'] else 'BEARISH'
            ema_trend = 'BULLISH' if latest['ema_12'] > latest['ema_26'] else 'BEARISH'
            
            # ADX para fuerza de tendencia
            adx_strength = latest['adx'] if not pd.isna(latest['adx']) else 25
            
            # Determinar tendencia principal
            trend_signals = []
            if sma_trend == 'BULLISH':
                trend_signals.append(1)
            else:
                trend_signals.append(-1)
                
            if ema_trend == 'BULLISH':
                trend_signals.append(1)
            else:
                trend_signals.append(-1)
            
            # Análisis de precio vs Bollinger Bands
            if latest['close'] > latest['bb_middle']:
                trend_signals.append(1)
            else:
                trend_signals.append(-1)
            
            trend_score = sum(trend_signals)
            
            if trend_score >= 2:
                trend = 'BULLISH'
            elif trend_score <= -2:
                trend = 'BEARISH'
            else:
                trend = 'SIDEWAYS'
            
            # Calcular confianza
            confidence = min(100, abs(trend_score) * 25 + adx_strength)
            
            return {
                'trend': trend,
                'strength': adx_strength,
                'confidence': confidence,
                'sma_trend': sma_trend,
                'ema_trend': ema_trend
            }
            
        except Exception as e:
            logger.error(f"Error analizando tendencia: {e}")
            return {'trend': 'UNKNOWN', 'strength': 0, 'confidence': 0}
    
    def generate_signals(self, df: pd.DataFrame) -> Dict:
        """Generar señales de trading"""
        try:
            if df.empty or len(df) < 50:
                return {'signal': 'HOLD', 'confidence': 0, 'reasons': []}
            
            latest = df.iloc[-1]
            previous = df.iloc[-2]
            
            signals = []
            reasons = []
            
            # Señal RSI
            rsi = latest['rsi']
            if not pd.isna(rsi):
                if rsi < 30:
                    signals.append(1)  # Sobreventa - señal de compra
                    reasons.append(f"RSI sobreventa ({rsi:.1f})")
                elif rsi > 70:
                    signals.append(-1)  # Sobrecompra - señal de venta
                    reasons.append(f"RSI sobrecompra ({rsi:.1f})")
            
            # Señal MACD
            if not pd.isna(latest['macd']) and not pd.isna(latest['macd_signal']):
                if latest['macd'] > latest['macd_signal'] and previous['macd'] <= previous['macd_signal']:
                    signals.append(1)  # Cruce alcista
                    reasons.append("MACD cruce alcista")
                elif latest['macd'] < latest['macd_signal'] and previous['macd'] >= previous['macd_signal']:
                    signals.append(-1)  # Cruce bajista
                    reasons.append("MACD cruce bajista")
            
            # Señal Bollinger Bands
            if not pd.isna(latest['bb_upper']) and not pd.isna(latest['bb_lower']):
                if latest['close'] <= latest['bb_lower']:
                    signals.append(1)  # Precio en banda inferior
                    reasons.append("Precio en banda inferior de Bollinger")
                elif latest['close'] >= latest['bb_upper']:
                    signals.append(-1)  # Precio en banda superior
                    reasons.append("Precio en banda superior de Bollinger")
            
            # Señal Stochastic
            if not pd.isna(latest['stoch_k']) and not pd.isna(latest['stoch_d']):
                if latest['stoch_k'] < 20 and latest['stoch_k'] > latest['stoch_d']:
                    signals.append(1)  # Sobreventa y cruce alcista
                    reasons.append("Stochastic sobreventa con cruce alcista")
                elif latest['stoch_k'] > 80 and latest['stoch_k'] < latest['stoch_d']:
                    signals.append(-1)  # Sobrecompra y cruce bajista
                    reasons.append("Stochastic sobrecompra con cruce bajista")
            
            # Señal Williams %R
            if not pd.isna(latest['williams_r']):
                if latest['williams_r'] > -20:
                    signals.append(-1)  # Sobrecompra
                    reasons.append("Williams %R sobrecompra")
                elif latest['williams_r'] < -80:
                    signals.append(1)  # Sobreventa
                    reasons.append("Williams %R sobreventa")
            
            # Análisis de tendencia
            trend_analysis = self.analyze_trend(df)
            if trend_analysis['trend'] == 'BULLISH' and trend_analysis['confidence'] > 60:
                signals.append(1)
                reasons.append(f"Tendencia alcista fuerte ({trend_analysis['confidence']:.0f}%)")
            elif trend_analysis['trend'] == 'BEARISH' and trend_analysis['confidence'] > 60:
                signals.append(-1)
                reasons.append(f"Tendencia bajista fuerte ({trend_analysis['confidence']:.0f}%)")
            
            # Calcular señal final
            if not signals:
                final_signal = 'HOLD'
                confidence = 0
            else:
                signal_sum = sum(signals)
                signal_count = len(signals)
                
                if signal_sum >= 2:
                    final_signal = 'BUY'
                elif signal_sum <= -2:
                    final_signal = 'SELL'
                else:
                    final_signal = 'HOLD'
                
                # Calcular confianza basada en consenso
                if final_signal != 'HOLD':
                    confidence = min(100, abs(signal_sum) * 20 + (signal_count * 10))
                else:
                    confidence = 0
            
            return {
                'signal': final_signal,
                'confidence': confidence,
                'reasons': reasons,
                'signal_count': len(signals),
                'trend_analysis': trend_analysis
            }
            
        except Exception as e:
            logger.error(f"Error generando señales: {e}")
            return {'signal': 'HOLD', 'confidence': 0, 'reasons': []}
    
    def calculate_support_resistance(self, df: pd.DataFrame) -> Dict:
        """Calcular niveles de soporte y resistencia"""
        try:
            if df.empty or len(df) < 20:
                return {'support': None, 'resistance': None}
            
            # Usar últimos 50 períodos para cálculo
            recent_df = df.tail(50)
            
            # Encontrar máximos y mínimos locales
            highs = recent_df['high'].rolling(window=5, center=True).max()
            lows = recent_df['low'].rolling(window=5, center=True).min()
            
            # Identificar niveles de resistencia (máximos locales)
            resistance_levels = []
            for i in range(2, len(recent_df) - 2):
                if recent_df['high'].iloc[i] == highs.iloc[i]:
                    resistance_levels.append(recent_df['high'].iloc[i])
            
            # Identificar niveles de soporte (mínimos locales)
            support_levels = []
            for i in range(2, len(recent_df) - 2):
                if recent_df['low'].iloc[i] == lows.iloc[i]:
                    support_levels.append(recent_df['low'].iloc[i])
            
            # Obtener niveles más relevantes
            current_price = df['close'].iloc[-1]
            
            # Resistencia más cercana por encima del precio actual
            resistance = None
            if resistance_levels:
                above_price = [r for r in resistance_levels if r > current_price]
                if above_price:
                    resistance = min(above_price)
            
            # Soporte más cercano por debajo del precio actual
            support = None
            if support_levels:
                below_price = [s for s in support_levels if s < current_price]
                if below_price:
                    support = max(below_price)
            
            return {
                'support': support,
                'resistance': resistance,
                'current_price': current_price
            }
            
        except Exception as e:
            logger.error(f"Error calculando soporte/resistencia: {e}")
            return {'support': None, 'resistance': None}
    
    def calculate_stop_loss_take_profit(self, signal: str, entry_price: float, 
                                      atr: float, risk_reward_ratio: float = 2.0) -> Tuple[float, float]:
        """Calcular Stop Loss y Take Profit"""
        try:
            if pd.isna(atr) or atr <= 0:
                atr = 0.0010  # ATR por defecto para EUR/USD
            
            # Multiplicador para SL basado en ATR
            sl_multiplier = 1.5
            
            if signal == 'BUY':
                stop_loss = entry_price - (atr * sl_multiplier)
                take_profit = entry_price + (atr * sl_multiplier * risk_reward_ratio)
            elif signal == 'SELL':
                stop_loss = entry_price + (atr * sl_multiplier)
                take_profit = entry_price - (atr * sl_multiplier * risk_reward_ratio)
            else:
                return None, None
            
            return round(stop_loss, 5), round(take_profit, 5)
            
        except Exception as e:
            logger.error(f"Error calculando SL/TP: {e}")
            return None, None
    
    def get_market_summary(self, df: pd.DataFrame) -> Dict:
        """Obtener resumen completo del análisis de mercado"""
        try:
            if df.empty:
                return {}
            
            # Calcular indicadores
            df_with_indicators = self.calculate_technical_indicators(df)
            
            # Obtener última fila
            latest = df_with_indicators.iloc[-1]
            
            # Generar señales
            signals = self.generate_signals(df_with_indicators)
            
            # Analizar tendencia
            trend = self.analyze_trend(df_with_indicators)
            
            # Calcular soporte y resistencia
            sr_levels = self.calculate_support_resistance(df_with_indicators)
            
            # Determinar emojis
            trend_emoji = "🟢" if trend['trend'] == 'BULLISH' else "🔴" if trend['trend'] == 'BEARISH' else "🟡"
            signal_emoji = "📈" if signals['signal'] == 'BUY' else "📉" if signals['signal'] == 'SELL' else "⏸️"
            
            # Determinar estado del RSI
            rsi_status = "Sobreventa" if latest['rsi'] < 30 else "Sobrecompra" if latest['rsi'] > 70 else "Neutral"
            
            # Determinar señal MACD
            macd_signal = "Alcista" if latest['macd'] > latest['macd_signal'] else "Bajista"
            
            # Posición en Bollinger Bands
            if latest['close'] > latest['bb_upper']:
                bb_position = "Sobre banda superior"
            elif latest['close'] < latest['bb_lower']:
                bb_position = "Bajo banda inferior"
            else:
                bb_position = "Entre bandas"
            
            # Recomendación final
            if signals['confidence'] >= self.min_confidence:
                recommendation = f"{signals['signal']} - Alta confianza"
            elif signals['confidence'] >= 50:
                recommendation = f"{signals['signal']} - Confianza media"
            else:
                recommendation = "ESPERAR - Baja confianza"
            
            return {
                'current_price': latest['close'],
                'trend': trend['trend'],
                'trend_emoji': trend_emoji,
                'signal': signals['signal'],
                'signal_emoji': signal_emoji,
                'confidence': signals['confidence'],
                'rsi': latest['rsi'],
                'rsi_status': rsi_status,
                'macd_signal': macd_signal,
                'bollinger_position': bb_position,
                'sma20': latest['sma_20'],
                'sma50': latest['sma_50'],
                'recommendation': recommendation,
                'reasons': signals['reasons'],
                'support': sr_levels.get('support'),
                'resistance': sr_levels.get('resistance'),
                'atr': latest['atr'],
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Error generando resumen de mercado: {e}")
            return {}
    
    def should_trade(self, df: pd.DataFrame) -> Tuple[bool, str, Dict]:
        """Determinar si se debe realizar un trade"""
        try:
            signals = self.generate_signals(df)
            
            # Verificar confianza mínima
            if signals['confidence'] < self.min_confidence:
                return False, 'HOLD', {'reason': 'Confianza insuficiente'}
            
            # Verificar que no sea HOLD
            if signals['signal'] == 'HOLD':
                return False, 'HOLD', {'reason': 'Señal neutral'}
            
            # Obtener datos para SL/TP
            latest = df.iloc[-1]
            atr = latest.get('atr', 0.0010)
            
            # Calcular SL y TP
            sl, tp = self.calculate_stop_loss_take_profit(
                signals['signal'], 
                latest['close'], 
                atr
            )
            
            trade_info = {
                'signal': signals['signal'],
                'confidence': signals['confidence'],
                'entry_price': latest['close'],
                'stop_loss': sl,
                'take_profit': tp,
                'reasons': signals['reasons'],
                'atr': atr
            }
            
            return True, signals['signal'], trade_info
            
        except Exception as e:
            logger.error(f"Error determinando si operar: {e}")
            return False, 'HOLD', {'reason': 'Error en análisis'}

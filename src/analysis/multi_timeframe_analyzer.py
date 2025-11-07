"""
Multi-Timeframe Analysis System
Analiza múltiples marcos temporales simultáneamente para máxima precisión
"""

import pandas as pd
import numpy as np
import ta
import logging
import warnings
from datetime import datetime, timedelta

# Suprimir warnings de TA para evitar spam en logs
warnings.filterwarnings('ignore', category=RuntimeWarning, module='ta')
warnings.filterwarnings('ignore', message='invalid value encountered in scalar divide')
from typing import Dict, List, Tuple, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class TimeFrame(Enum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"

class TrendDirection(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"

class MultiTimeframeAnalyzer:
    def __init__(self, mt5_connector):
        self.mt5 = mt5_connector
        self.symbol = "EURUSD"
        
        # Configuración de timeframes
        self.timeframes = {
            TimeFrame.H1: {"periods": 200, "weight": 0.35},    # Tendencia principal
            TimeFrame.M15: {"periods": 300, "weight": 0.30},   # Marco actual
            TimeFrame.M5: {"periods": 400, "weight": 0.25},    # Confirmación
            TimeFrame.M1: {"periods": 500, "weight": 0.10}     # Timing preciso
        }
        
        # Umbrales de alineación
        self.alignment_threshold = 0.75  # 75% de timeframes deben estar alineados
        self.min_timeframes_required = 3  # Mínimo 3 timeframes para señal válida
        
    async def get_multi_timeframe_data(self) -> Dict[TimeFrame, pd.DataFrame]:
        """Obtener datos de múltiples timeframes"""
        try:
            timeframe_data = {}
            
            for tf, config in self.timeframes.items():
                logger.info(f"Obteniendo datos para {tf.value}...")
                
                # Obtener datos según el timeframe
                if tf == TimeFrame.M1:
                    df = await self.mt5.get_rates_timeframe("M1", config["periods"])
                elif tf == TimeFrame.M5:
                    df = await self.mt5.get_rates_timeframe("M5", config["periods"])
                elif tf == TimeFrame.M15:
                    df = await self.mt5.get_rates_timeframe("M15", config["periods"])
                elif tf == TimeFrame.H1:
                    df = await self.mt5.get_rates_timeframe("H1", config["periods"])
                else:
                    # Fallback al método actual para M15
                    df = await self.mt5.get_rates(count=config["periods"])
                
                if not df.empty:
                    # Calcular indicadores para este timeframe
                    df = self._calculate_timeframe_indicators(df, tf)
                    timeframe_data[tf] = df
                    logger.info(f"✅ {tf.value}: {len(df)} períodos obtenidos")
                else:
                    logger.warning(f"⚠️ No se pudieron obtener datos para {tf.value}")
            
            return timeframe_data
            
        except Exception as e:
            logger.error(f"Error obteniendo datos multi-timeframe: {e}")
            return {}
    
    def _calculate_timeframe_indicators(self, df: pd.DataFrame, timeframe: TimeFrame) -> pd.DataFrame:
        """Calcular indicadores técnicos específicos para cada timeframe"""
        try:
            if df.empty or len(df) < 50:
                return df
            
            # Ajustar períodos según timeframe
            if timeframe == TimeFrame.H1:
                # Períodos más largos para H1
                rsi_period = 21
                macd_fast = 17
                macd_slow = 39
                sma_short = 34
                sma_long = 89
            elif timeframe == TimeFrame.M15:
                # Períodos estándar para M15
                rsi_period = 14
                macd_fast = 12
                macd_slow = 26
                sma_short = 21
                sma_long = 50
            elif timeframe == TimeFrame.M5:
                # Períodos más cortos para M5
                rsi_period = 10
                macd_fast = 8
                macd_slow = 17
                sma_short = 13
                sma_long = 34
            else:  # M1
                # Períodos muy cortos para M1
                rsi_period = 7
                macd_fast = 5
                macd_slow = 13
                sma_short = 8
                sma_long = 21
            
            # Indicadores básicos
            df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=rsi_period).rsi()
            
            # MACD
            macd = ta.trend.MACD(df['close'], window_fast=macd_fast, window_slow=macd_slow)
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_histogram'] = macd.macd_diff()
            
            # Medias móviles
            df['sma_short'] = ta.trend.SMAIndicator(df['close'], window=sma_short).sma_indicator()
            df['sma_long'] = ta.trend.SMAIndicator(df['close'], window=sma_long).sma_indicator()
            df['ema_short'] = ta.trend.EMAIndicator(df['close'], window=sma_short).ema_indicator()
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(df['close'], window=20)
            df['bb_upper'] = bb.bollinger_hband()
            df['bb_lower'] = bb.bollinger_lband()
            df['bb_middle'] = bb.bollinger_mavg()
            
            # ATR para volatilidad
            df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
            
            # Stochastic
            stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
            df['stoch_k'] = stoch.stoch()
            df['stoch_d'] = stoch.stoch_signal()
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculando indicadores para {timeframe.value}: {e}")
            return df
    
    def analyze_timeframe_trend(self, df: pd.DataFrame, timeframe: TimeFrame) -> Dict:
        """Analizar tendencia en un timeframe específico"""
        try:
            if df.empty or len(df) < 20:
                return {'direction': TrendDirection.NEUTRAL, 'strength': 0, 'confidence': 0}
            
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            signals = []
            
            # 1. Análisis de medias móviles
            if 'sma_short' in df.columns and 'sma_long' in df.columns:
                if latest['sma_short'] > latest['sma_long']:
                    if latest['close'] > latest['sma_short']:
                        signals.append(('MA_BULLISH', 0.8))
                    else:
                        signals.append(('MA_NEUTRAL', 0.3))
                else:
                    if latest['close'] < latest['sma_short']:
                        signals.append(('MA_BEARISH', 0.8))
                    else:
                        signals.append(('MA_NEUTRAL', 0.3))
            
            # 2. Análisis RSI
            if 'rsi' in df.columns:
                rsi = latest['rsi']
                if rsi > 70:
                    signals.append(('RSI_OVERBOUGHT', -0.6))
                elif rsi > 60:
                    signals.append(('RSI_BULLISH', 0.4))
                elif rsi < 30:
                    signals.append(('RSI_OVERSOLD', 0.6))
                elif rsi < 40:
                    signals.append(('RSI_BEARISH', -0.4))
                else:
                    signals.append(('RSI_NEUTRAL', 0.0))
            
            # 3. Análisis MACD
            if 'macd' in df.columns and 'macd_signal' in df.columns:
                if latest['macd'] > latest['macd_signal']:
                    if prev['macd'] <= prev['macd_signal']:  # Cruce alcista
                        signals.append(('MACD_BULLISH_CROSS', 0.9))
                    else:
                        signals.append(('MACD_BULLISH', 0.5))
                else:
                    if prev['macd'] >= prev['macd_signal']:  # Cruce bajista
                        signals.append(('MACD_BEARISH_CROSS', -0.9))
                    else:
                        signals.append(('MACD_BEARISH', -0.5))
            
            # 4. Análisis Bollinger Bands
            if 'bb_upper' in df.columns and 'bb_lower' in df.columns:
                if latest['close'] > latest['bb_upper']:
                    signals.append(('BB_BREAKOUT_UP', 0.7))
                elif latest['close'] < latest['bb_lower']:
                    signals.append(('BB_BREAKOUT_DOWN', -0.7))
                elif latest['close'] > latest['bb_middle']:
                    signals.append(('BB_UPPER_HALF', 0.3))
                else:
                    signals.append(('BB_LOWER_HALF', -0.3))
            
            # 5. Análisis de momentum (precio)
            price_change = (latest['close'] - prev['close']) / prev['close']
            if abs(price_change) > 0.0005:  # Cambio significativo
                if price_change > 0:
                    signals.append(('MOMENTUM_BULLISH', 0.4))
                else:
                    signals.append(('MOMENTUM_BEARISH', -0.4))
            
            # Calcular dirección y fuerza
            total_signal = sum(signal[1] for signal in signals)
            signal_count = len(signals)
            
            if signal_count == 0:
                return {'direction': TrendDirection.NEUTRAL, 'strength': 0, 'confidence': 0}
            
            avg_signal = total_signal / signal_count
            strength = min(abs(avg_signal) * 100, 100)
            confidence = min((signal_count / 5) * 100, 100)  # Máximo 5 señales
            
            if avg_signal > 0.2:
                direction = TrendDirection.BULLISH
            elif avg_signal < -0.2:
                direction = TrendDirection.BEARISH
            else:
                direction = TrendDirection.NEUTRAL
            
            return {
                'direction': direction,
                'strength': strength,
                'confidence': confidence,
                'signals': signals,
                'raw_signal': avg_signal,
                'timeframe': timeframe.value
            }
            
        except Exception as e:
            logger.error(f"Error analizando tendencia en {timeframe.value}: {e}")
            return {'direction': TrendDirection.NEUTRAL, 'strength': 0, 'confidence': 0}
    
    async def get_multi_timeframe_signal(self) -> Dict:
        """Obtener señal consolidada de múltiples timeframes"""
        try:
            logger.info("🔄 Iniciando análisis multi-timeframe...")
            
            # Obtener datos de todos los timeframes
            timeframe_data = await self.get_multi_timeframe_data()
            
            if len(timeframe_data) < self.min_timeframes_required:
                logger.warning(f"Insuficientes timeframes: {len(timeframe_data)}/{self.min_timeframes_required}")
                return {
                    'signal': 'HOLD',
                    'confidence': 0,
                    'reason': f'Datos insuficientes ({len(timeframe_data)} timeframes)',
                    'timeframe_analysis': {}
                }
            
            # Analizar cada timeframe
            timeframe_analysis = {}
            weighted_signals = []
            
            for tf, df in timeframe_data.items():
                analysis = self.analyze_timeframe_trend(df, tf)
                timeframe_analysis[tf.value] = analysis
                
                # Aplicar peso del timeframe
                weight = self.timeframes[tf]["weight"]
                if analysis['direction'] == TrendDirection.BULLISH:
                    weighted_signals.append(analysis['strength'] * weight / 100)
                elif analysis['direction'] == TrendDirection.BEARISH:
                    weighted_signals.append(-analysis['strength'] * weight / 100)
                else:
                    weighted_signals.append(0)
                
                logger.info(f"📊 {tf.value}: {analysis['direction'].value} (Fuerza: {analysis['strength']:.1f}%)")
            
            # Calcular señal consolidada
            total_weighted_signal = sum(weighted_signals)
            
            # Verificar alineación de timeframes
            bullish_count = sum(1 for tf, analysis in timeframe_analysis.items() 
                              if analysis['direction'] == TrendDirection.BULLISH)
            bearish_count = sum(1 for tf, analysis in timeframe_analysis.items() 
                               if analysis['direction'] == TrendDirection.BEARISH)
            neutral_count = len(timeframe_analysis) - bullish_count - bearish_count
            
            total_timeframes = len(timeframe_analysis)
            alignment_ratio = max(bullish_count, bearish_count) / total_timeframes
            
            # Determinar señal final
            if alignment_ratio >= self.alignment_threshold:
                if total_weighted_signal > 0.3:
                    signal = 'BUY'
                    confidence = min(95, alignment_ratio * 100 + abs(total_weighted_signal) * 20)
                elif total_weighted_signal < -0.3:
                    signal = 'SELL'
                    confidence = min(95, alignment_ratio * 100 + abs(total_weighted_signal) * 20)
                else:
                    signal = 'HOLD'
                    # Dar algo de confianza cuando hay buena alineación pero señal débil
                    confidence = min(30, alignment_ratio * 40)
            else:
                signal = 'HOLD'
                # Dar confianza mínima basada en alineación parcial
                confidence = min(15, alignment_ratio * 20)
            
            # Calcular confianza adicional basada en convergencia
            convergence_bonus = 0
            if signal != 'HOLD':
                # Bonus por timeframes alineados
                convergence_bonus += alignment_ratio * 15
                
                # Bonus por fuerza de señales
                avg_strength = np.mean([analysis['strength'] for analysis in timeframe_analysis.values()])
                convergence_bonus += (avg_strength / 100) * 10
            
            final_confidence = min(95, confidence + convergence_bonus)
            
            # Razones detalladas
            reasons = []
            for tf, analysis in timeframe_analysis.items():
                if analysis['direction'] != TrendDirection.NEUTRAL:
                    reasons.append(f"{tf}: {analysis['direction'].value} ({analysis['strength']:.0f}%)")
            
            result = {
                'signal': signal,
                'confidence': final_confidence,
                'total_weighted_signal': total_weighted_signal,
                'alignment_ratio': alignment_ratio,
                'timeframe_analysis': timeframe_analysis,
                'timeframes_count': {
                    'bullish': bullish_count,
                    'bearish': bearish_count,
                    'neutral': neutral_count,
                    'total': total_timeframes
                },
                'reasons': reasons,
                'convergence_quality': 'HIGH' if alignment_ratio >= 0.8 else 'MEDIUM' if alignment_ratio >= 0.6 else 'LOW'
            }
            
            logger.info(f"🎯 Señal Multi-TF: {signal} (Confianza: {final_confidence:.1f}%)")
            logger.info(f"📊 Alineación: {alignment_ratio:.1%} ({bullish_count}B/{bearish_count}B/{neutral_count}N)")
            
            return result
            
        except Exception as e:
            logger.error(f"Error en análisis multi-timeframe: {e}")
            return {
                'signal': 'HOLD',
                'confidence': 0,
                'reason': f'Error en análisis: {str(e)}',
                'timeframe_analysis': {}
            }
    
    def get_timeframe_summary(self, analysis: Dict) -> str:
        """Generar resumen legible del análisis multi-timeframe"""
        try:
            if not analysis or 'timeframe_analysis' not in analysis:
                return "❌ Análisis no disponible"
            
            signal = analysis['signal']
            confidence = analysis['confidence']
            alignment = analysis['alignment_ratio']
            
            # Emoji según señal
            signal_emoji = "📈" if signal == 'BUY' else "📉" if signal == 'SELL' else "⏸️"
            
            # Calidad de convergencia
            quality = analysis.get('convergence_quality', 'LOW')
            quality_emoji = "🟢" if quality == 'HIGH' else "🟡" if quality == 'MEDIUM' else "🔴"
            
            summary = f"{signal_emoji} **{signal}** - Confianza: {confidence:.1f}%\n"
            summary += f"{quality_emoji} Convergencia: {quality} ({alignment:.1%})\n\n"
            
            # Desglose por timeframe
            summary += "📊 **Análisis por Timeframe:**\n"
            
            tf_analysis = analysis['timeframe_analysis']
            for tf_name, tf_data in tf_analysis.items():
                direction = tf_data['direction'].value
                strength = tf_data['strength']
                
                if direction == 'BULLISH':
                    emoji = "🟢"
                elif direction == 'BEARISH':
                    emoji = "🔴"
                else:
                    emoji = "⚪"
                
                summary += f"{emoji} {tf_name}: {direction} ({strength:.0f}%)\n"
            
            # Contadores
            counts = analysis['timeframes_count']
            summary += f"\n📈 Alcistas: {counts['bullish']} | "
            summary += f"📉 Bajistas: {counts['bearish']} | "
            summary += f"⚪ Neutrales: {counts['neutral']}"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generando resumen: {e}")
            return f"❌ Error generando resumen: {str(e)}"

"""
Analizador Avanzado para Máxima Rentabilidad
Incluye estrategias optimizadas y filtros adicionales
"""

import pandas as pd
import numpy as np
import ta
import logging
import warnings
from datetime import datetime, timedelta

# Suprimir warnings específicos de TA
warnings.filterwarnings('ignore', category=RuntimeWarning, module='ta')
warnings.filterwarnings('ignore', message='invalid value encountered in scalar divide')
from typing import Dict, List, Tuple, Optional

# Suprimir warnings específicos de pandas/ta que no son críticos
warnings.filterwarnings('ignore', category=FutureWarning, module='ta')

# Importar sistema de ML
try:
    from ..ml.adaptive_learning import AdaptiveLearningSystem
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# Importar Multi-Timeframe Analysis
try:
    from .multi_timeframe_analyzer import MultiTimeframeAnalyzer
    MTF_AVAILABLE = True
except ImportError:
    MTF_AVAILABLE = False

logger = logging.getLogger(__name__)

class AdvancedMarketAnalyzer:
    def __init__(self, mt5_connector=None):
        self.symbol = "EURUSD"
        self.min_confidence = 78  # Optimizado para máxima rentabilidad
        self.mt5_connector = mt5_connector
        
        # Filtros adicionales para mejorar precisión
        self.trend_strength_filter = True
        self.volatility_filter = True
        self.session_filter = True
        
        # Sistema de Machine Learning
        self.ml_system = AdaptiveLearningSystem() if ML_AVAILABLE else None
        self.ml_enabled = ML_AVAILABLE
        
        # Sistema Multi-Timeframe
        self.mtf_analyzer = MultiTimeframeAnalyzer(mt5_connector) if MTF_AVAILABLE and mt5_connector else None
        self.mtf_enabled = MTF_AVAILABLE and mt5_connector is not None
        
    def calculate_advanced_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcular indicadores técnicos avanzados"""
        try:
            if df.empty or len(df) < 100:
                logger.warning("Datos insuficientes para análisis avanzado")
                return df
            
            # Indicadores básicos
            df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
            df['rsi_fast'] = ta.momentum.RSIIndicator(df['close'], window=7).rsi()
            
            # MACD múltiple
            macd = ta.trend.MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_histogram'] = macd.macd_diff()
            
            # MACD rápido para señales tempranas
            macd_fast = ta.trend.MACD(df['close'], window_slow=21, window_fast=8, window_sign=5)
            df['macd_fast'] = macd_fast.macd()
            df['macd_fast_signal'] = macd_fast.macd_signal()
            
            # Bollinger Bands múltiples
            bb20 = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
            df['bb_upper'] = bb20.bollinger_hband()
            df['bb_middle'] = bb20.bollinger_mavg()
            df['bb_lower'] = bb20.bollinger_lband()
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
            
            # Bollinger Bands ajustadas
            bb10 = ta.volatility.BollingerBands(df['close'], window=10, window_dev=1.5)
            df['bb_upper_fast'] = bb10.bollinger_hband()
            df['bb_lower_fast'] = bb10.bollinger_lband()
            
            # Medias móviles múltiples
            df['sma_9'] = ta.trend.SMAIndicator(df['close'], window=9).sma_indicator()
            df['sma_21'] = ta.trend.SMAIndicator(df['close'], window=21).sma_indicator()
            df['sma_50'] = ta.trend.SMAIndicator(df['close'], window=50).sma_indicator()
            df['sma_200'] = ta.trend.SMAIndicator(df['close'], window=200).sma_indicator()
            
            # EMAs para tendencias
            df['ema_8'] = ta.trend.EMAIndicator(df['close'], window=8).ema_indicator()
            df['ema_13'] = ta.trend.EMAIndicator(df['close'], window=13).ema_indicator()
            df['ema_21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
            df['ema_55'] = ta.trend.EMAIndicator(df['close'], window=55).ema_indicator()
            
            # Stochastic optimizado
            stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'], window=14, smooth_window=3)
            df['stoch_k'] = stoch.stoch()
            df['stoch_d'] = stoch.stoch_signal()
            
            # Williams %R
            df['williams_r'] = ta.momentum.WilliamsRIndicator(df['high'], df['low'], df['close'], lbp=14).williams_r()
            
            # ADX para fuerza de tendencia
            adx = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14)
            df['adx'] = adx.adx()
            df['adx_pos'] = adx.adx_pos()
            df['adx_neg'] = adx.adx_neg()
            
            # ATR para volatilidad
            df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
            df['atr_fast'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=7).average_true_range()
            
            # CCI (Commodity Channel Index)
            df['cci'] = ta.trend.CCIIndicator(df['high'], df['low'], df['close'], window=20).cci()
            
            # Momentum
            df['momentum'] = ta.momentum.ROCIndicator(df['close'], window=10).roc()
            
            # Parabolic SAR
            psar = ta.trend.PSARIndicator(df['high'], df['low'], df['close'])
            df['psar'] = psar.psar()
            
            # Ichimoku Cloud (simplificado)
            ichimoku = ta.trend.IchimokuIndicator(df['high'], df['low'])
            df['ichimoku_a'] = ichimoku.ichimoku_a()
            df['ichimoku_b'] = ichimoku.ichimoku_b()
            
            # Volume indicators (si hay datos de volumen)
            if 'tick_volume' in df.columns:
                # Usar indicadores de volumen disponibles en la versión actual de ta
                try:
                    df['volume_sma'] = ta.volume.VolumeSMAIndicator(df['close'], df['tick_volume'], window=20).volume_sma()
                except AttributeError:
                    # Fallback: calcular SMA simple del volumen
                    df['volume_sma'] = df['tick_volume'].rolling(window=20).mean()
                
                # VWAP simplificado (Volume Weighted Average Price)
                try:
                    df['vwap'] = (df['close'] * df['tick_volume']).cumsum() / df['tick_volume'].cumsum()
                except:
                    df['vwap'] = df['close']  # Fallback al precio de cierre
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculando indicadores avanzados: {e}")
            return df
    
    def detect_market_regime(self, df: pd.DataFrame) -> Dict:
        """Detectar régimen de mercado (trending vs ranging)"""
        try:
            if df.empty or len(df) < 50:
                return {'regime': 'UNKNOWN', 'strength': 0}
            
            latest = df.iloc[-1]
            
            # ADX para determinar si hay tendencia
            adx_value = latest.get('adx', 25)
            
            # Análisis de volatilidad
            atr_current = latest.get('atr', 0)
            atr_avg = df['atr'].tail(20).mean() if 'atr' in df.columns else 0
            
            # Análisis de medias móviles
            sma_alignment = 0
            if all(col in df.columns for col in ['sma_9', 'sma_21', 'sma_50']):
                if latest['sma_9'] > latest['sma_21'] > latest['sma_50']:
                    sma_alignment = 1  # Tendencia alcista
                elif latest['sma_9'] < latest['sma_21'] < latest['sma_50']:
                    sma_alignment = -1  # Tendencia bajista
            
            # Determinar régimen
            if adx_value > 25 and abs(sma_alignment) == 1:
                regime = 'TRENDING'
                strength = min(100, adx_value * 2)
            elif adx_value < 20:
                regime = 'RANGING'
                strength = 100 - adx_value * 2
            else:
                regime = 'TRANSITIONAL'
                strength = 50
            
            return {
                'regime': regime,
                'strength': strength,
                'adx': adx_value,
                'volatility_ratio': atr_current / atr_avg if atr_avg > 0 else 1,
                'trend_direction': sma_alignment
            }
            
        except Exception as e:
            logger.error(f"Error detectando régimen de mercado: {e}")
            return {'regime': 'UNKNOWN', 'strength': 0}
    
    def generate_premium_signals(self, df: pd.DataFrame) -> Dict:
        """Generar señales premium con múltiples confirmaciones"""
        try:
            if df.empty or len(df) < 100:
                return {'signal': 'HOLD', 'confidence': 0, 'reasons': []}
            
            latest = df.iloc[-1]
            previous = df.iloc[-2]
            
            # Detectar régimen de mercado
            market_regime = self.detect_market_regime(df)
            
            signals = []
            reasons = []
            confidence_factors = []
            
            # === SEÑALES PARA MERCADO TRENDING ===
            if market_regime['regime'] == 'TRENDING':
                
                # Señal EMA Crossover (muy efectiva en trending)
                if (latest['ema_8'] > latest['ema_21'] and 
                    previous['ema_8'] <= previous['ema_21']):
                    signals.append(1)
                    reasons.append("EMA 8/21 cruce alcista")
                    confidence_factors.append(25)
                elif (latest['ema_8'] < latest['ema_21'] and 
                      previous['ema_8'] >= previous['ema_21']):
                    signals.append(-1)
                    reasons.append("EMA 8/21 cruce bajista")
                    confidence_factors.append(25)
                
                # Confirmación con MACD rápido
                if (latest['macd_fast'] > latest['macd_fast_signal'] and 
                    latest['macd_fast'] > 0):
                    signals.append(1)
                    reasons.append("MACD rápido alcista")
                    confidence_factors.append(15)
                elif (latest['macd_fast'] < latest['macd_fast_signal'] and 
                      latest['macd_fast'] < 0):
                    signals.append(-1)
                    reasons.append("MACD rápido bajista")
                    confidence_factors.append(15)
                
                # ADX confirmación de fuerza
                if latest.get('adx', 0) > 30:
                    confidence_factors.append(20)
                    reasons.append(f"Tendencia fuerte (ADX: {latest.get('adx', 0):.1f})")
            
            # === SEÑALES PARA MERCADO RANGING ===
            elif market_regime['regime'] == 'RANGING':
                
                # Bollinger Bands mean reversion
                if latest['close'] <= latest['bb_lower_fast']:
                    signals.append(1)
                    reasons.append("Precio en banda inferior (mean reversion)")
                    confidence_factors.append(20)
                elif latest['close'] >= latest['bb_upper_fast']:
                    signals.append(-1)
                    reasons.append("Precio en banda superior (mean reversion)")
                    confidence_factors.append(20)
                
                # RSI extremos en ranging
                rsi = latest.get('rsi', 50)
                if rsi < 25:
                    signals.append(1)
                    reasons.append(f"RSI extremo sobreventa ({rsi:.1f})")
                    confidence_factors.append(25)
                elif rsi > 75:
                    signals.append(-1)
                    reasons.append(f"RSI extremo sobrecompra ({rsi:.1f})")
                    confidence_factors.append(25)
            
            # === SEÑALES UNIVERSALES ===
            
            # Stochastic con confirmación
            stoch_k = latest.get('stoch_k', 50)
            stoch_d = latest.get('stoch_d', 50)
            
            if (stoch_k < 20 and stoch_k > stoch_d and 
                previous.get('stoch_k', 50) <= previous.get('stoch_d', 50)):
                signals.append(1)
                reasons.append("Stochastic cruce alcista en sobreventa")
                confidence_factors.append(15)
            elif (stoch_k > 80 and stoch_k < stoch_d and 
                  previous.get('stoch_k', 50) >= previous.get('stoch_d', 50)):
                signals.append(-1)
                reasons.append("Stochastic cruce bajista en sobrecompra")
                confidence_factors.append(15)
            
            # CCI extremos
            cci = latest.get('cci', 0)
            if cci < -200:
                signals.append(1)
                reasons.append(f"CCI sobreventa extrema ({cci:.0f})")
                confidence_factors.append(10)
            elif cci > 200:
                signals.append(-1)
                reasons.append(f"CCI sobrecompra extrema ({cci:.0f})")
                confidence_factors.append(10)
            
            # Williams %R
            williams = latest.get('williams_r', -50)
            if williams > -10:
                signals.append(-1)
                reasons.append("Williams %R sobrecompra")
                confidence_factors.append(8)
            elif williams < -90:
                signals.append(1)
                reasons.append("Williams %R sobreventa")
                confidence_factors.append(8)
            
            # Momentum confirmation
            momentum = latest.get('momentum', 0)
            if momentum > 0.5:
                signals.append(1)
                reasons.append("Momentum alcista fuerte")
                confidence_factors.append(10)
            elif momentum < -0.5:
                signals.append(-1)
                reasons.append("Momentum bajista fuerte")
                confidence_factors.append(10)
            
            # === CALCULAR SEÑAL FINAL ===
            if not signals:
                final_signal = 'HOLD'
                confidence = 0
            else:
                signal_sum = sum(signals)
                
                if signal_sum >= 2:
                    final_signal = 'BUY'
                elif signal_sum <= -2:
                    final_signal = 'SELL'
                else:
                    final_signal = 'HOLD'
                
                # Calcular confianza basada en factores
                base_confidence = sum(confidence_factors) if confidence_factors else 0
                
                # Bonus por régimen de mercado
                regime_bonus = market_regime['strength'] * 0.3
                
                # Bonus por consenso de señales
                consensus_bonus = min(30, abs(signal_sum) * 10)
                
                confidence = min(100, base_confidence + regime_bonus + consensus_bonus)
            
            return {
                'signal': final_signal,
                'confidence': confidence,
                'reasons': reasons,
                'market_regime': market_regime,
                'signal_count': len(signals),
                'signal_strength': sum(signals) if signals else 0
            }
            
        except Exception as e:
            logger.error(f"Error generando señales premium: {e}")
            return {'signal': 'HOLD', 'confidence': 0, 'reasons': []}
    
    def calculate_dynamic_stops(self, signal: str, entry_price: float, 
                              df: pd.DataFrame) -> Tuple[float, float]:
        """Calcular SL y TP dinámicos basados en volatilidad y soporte/resistencia"""
        try:
            if df.empty:
                return None, None
            
            latest = df.iloc[-1]
            atr = latest.get('atr', 0.0010)
            
            # Detectar régimen para ajustar stops
            market_regime = self.detect_market_regime(df)
            
            # Multiplicadores basados en régimen de mercado
            if market_regime['regime'] == 'TRENDING':
                sl_multiplier = 1.2  # Stops más ajustados en trending
                tp_multiplier = 3.0  # TP más amplio para capturar tendencia
            elif market_regime['regime'] == 'RANGING':
                sl_multiplier = 0.8  # Stops más amplios en ranging
                tp_multiplier = 1.8  # TP más conservador
            else:
                sl_multiplier = 1.0  # Valores estándar
                tp_multiplier = 2.0
            
            # Ajustar por volatilidad
            volatility_ratio = market_regime.get('volatility_ratio', 1.0)
            sl_multiplier *= min(1.5, max(0.7, volatility_ratio))
            
            if signal == 'BUY':
                stop_loss = entry_price - (atr * sl_multiplier)
                take_profit = entry_price + (atr * tp_multiplier)
            elif signal == 'SELL':
                stop_loss = entry_price + (atr * sl_multiplier)
                take_profit = entry_price - (atr * tp_multiplier)
            else:
                return None, None
            
            return round(stop_loss, 5), round(take_profit, 5)
            
        except Exception as e:
            logger.error(f"Error calculando stops dinámicos: {e}")
            return None, None
    
    async def should_trade_premium_mtf(self) -> Tuple[bool, str, Dict]:
        """Determinar si se debe realizar un trade con análisis Multi-Timeframe + ML"""
        try:
            # Análisis Multi-Timeframe si está disponible
            if self.mtf_enabled and self.mtf_analyzer:
                logger.info("🔄 Usando análisis Multi-Timeframe...")
                mtf_analysis = await self.mtf_analyzer.get_multi_timeframe_signal()
                
                # Aplicar ML si está disponible
                if self.ml_enabled and self.ml_system:
                    adaptive_params = self.ml_system.get_adaptive_params()
                    min_confidence = adaptive_params.get('min_confidence', self.min_confidence)
                else:
                    min_confidence = self.min_confidence
                
                # Verificar confianza Multi-TF
                if mtf_analysis['confidence'] < min_confidence:
                    return False, 'HOLD', {
                        'reason': f'MTF confianza insuficiente ({mtf_analysis["confidence"]:.0f}% < {min_confidence:.0f}%)',
                        'mtf_analysis': mtf_analysis,
                        'analysis_type': 'Multi-Timeframe'
                    }
                
                if mtf_analysis['signal'] == 'HOLD':
                    return False, 'HOLD', {
                        'reason': 'MTF señal neutral',
                        'mtf_analysis': mtf_analysis,
                        'analysis_type': 'Multi-Timeframe'
                    }
                
                # Aplicar filtros adicionales con datos MTF
                current_session = self._get_current_session()
                
                # Filtro de sesión
                if self.session_filter:
                    current_hour = datetime.utcnow().hour
                    if not ((8 <= current_hour <= 17) or (13 <= current_hour <= 22)):
                        return False, 'HOLD', {
                            'reason': 'Fuera de sesiones principales',
                            'mtf_analysis': mtf_analysis,
                            'analysis_type': 'Multi-Timeframe'
                        }
                
                # Filtro de convergencia
                convergence_quality = mtf_analysis.get('convergence_quality', 'LOW')
                if convergence_quality == 'LOW':
                    return False, 'HOLD', {
                        'reason': f'Convergencia baja ({convergence_quality})',
                        'mtf_analysis': mtf_analysis,
                        'analysis_type': 'Multi-Timeframe'
                    }
                
                # Aplicar ML final si está disponible
                final_confidence = mtf_analysis['confidence']
                ml_status = "MTF analysis"
                
                if self.ml_enabled and self.ml_system:
                    ml_should_trade, ml_confidence, ml_reason = self.ml_system.should_trade_with_ml(
                        base_should_trade=True,
                        base_confidence=mtf_analysis['confidence'],
                        current_session=current_session,
                        indicators={}  # MTF ya incluye análisis completo
                    )
                    
                    if not ml_should_trade:
                        return False, 'HOLD', {
                            'reason': f'ML rejected MTF: {ml_reason}',
                            'mtf_analysis': mtf_analysis,
                            'analysis_type': 'Multi-Timeframe + ML'
                        }
                    
                    final_confidence = ml_confidence
                    ml_status = f"MTF + ML: {ml_reason}"
                
                # Obtener datos actuales para detectar régimen de mercado
                current_df = await self.mt5_connector.get_rates(count=200) if self.mt5_connector else pd.DataFrame()
                market_regime = self.detect_market_regime(current_df) if not current_df.empty else {
                    'regime': 'UNKNOWN', 
                    'strength': 50, 
                    'trend_direction': 0
                }
                
                # Construir información del trade
                trade_info = {
                    'signal': mtf_analysis['signal'],
                    'confidence': final_confidence,
                    'analysis_type': 'Multi-Timeframe + ML' if self.ml_enabled else 'Multi-Timeframe',
                    'mtf_analysis': mtf_analysis,
                    'convergence_quality': convergence_quality,
                    'timeframes_aligned': mtf_analysis.get('alignment_ratio', 0),
                    'reasons': mtf_analysis.get('reasons', []),
                    'ml_status': ml_status,
                    'session': current_session,
                    'market_regime': market_regime,  # Agregar market_regime faltante
                    'filters_passed': 'All MTF + ML filters passed'
                }
                
                logger.info(f"✅ MTF Trade aprobado: {mtf_analysis['signal']} (Confianza: {final_confidence:.1f}%)")
                return True, mtf_analysis['signal'], trade_info
                
            else:
                # Fallback al análisis single-timeframe
                logger.info("🔄 MTF no disponible, usando análisis single-timeframe...")
                return await self._should_trade_single_timeframe()
                
        except Exception as e:
            logger.error(f"Error en análisis MTF premium: {e}")
            # Fallback al análisis single-timeframe
            return await self._should_trade_single_timeframe()
    
    async def _should_trade_single_timeframe(self) -> Tuple[bool, str, Dict]:
        """Análisis single-timeframe como fallback"""
        try:
            # Obtener datos actuales
            if self.mt5_connector:
                df = await self.mt5_connector.get_rates(count=300)
            else:
                return False, 'HOLD', {'reason': 'No hay conector MT5 disponible'}
            
            if df.empty:
                return False, 'HOLD', {'reason': 'No se pudieron obtener datos'}
            
            # Usar el método original
            return self.should_trade_premium(df)
            
        except Exception as e:
            logger.error(f"Error en análisis single-timeframe: {e}")
            return False, 'HOLD', {'reason': f'Error en análisis: {str(e)}'}
    
    def should_trade_premium(self, df: pd.DataFrame) -> Tuple[bool, str, Dict]:
        """Determinar si se debe realizar un trade con análisis premium, filtros optimizados y ML (single-timeframe)"""
        try:
            signals = self.generate_premium_signals(df)
            
            # Aplicar pesos adaptativos de ML si está disponible
            if self.ml_enabled and self.ml_system:
                adaptive_weights = self.ml_system.get_adaptive_weights()
                adaptive_params = self.ml_system.get_adaptive_params()
                
                # Usar confianza mínima adaptativa
                min_confidence = adaptive_params.get('min_confidence', self.min_confidence)
            else:
                min_confidence = self.min_confidence
            
            # Verificar confianza mínima (ahora adaptativa)
            if signals['confidence'] < min_confidence:
                return False, 'HOLD', {'reason': f'Confianza insuficiente ({signals["confidence"]:.0f}% < {min_confidence:.0f}%)', 'analysis_type': 'Single-Timeframe'}
            
            # Verificar que no sea HOLD
            if signals['signal'] == 'HOLD':
                return False, 'HOLD', {'reason': 'Señal neutral', 'analysis_type': 'Single-Timeframe'}
            
            # FILTROS ADICIONALES PARA MEJORAR PRECISIÓN
            
            # Filtro 1: Fuerza de tendencia
            if self.trend_strength_filter:
                market_regime = signals.get('market_regime', {})
                if market_regime.get('strength', 0) < 60:
                    return False, 'HOLD', {'reason': 'Tendencia débil'}
            
            # Filtro 2: Volatilidad apropiada
            if self.volatility_filter:
                latest = df.iloc[-1]
                atr = latest.get('atr', 0)
                atr_avg = df['atr'].tail(20).mean() if 'atr' in df.columns else 0
                
                if atr_avg > 0:
                    volatility_ratio = atr / atr_avg
                    # Rechazar si volatilidad es muy alta (>2x) o muy baja (<0.5x)
                    if volatility_ratio > 2.0 or volatility_ratio < 0.5:
                        return False, 'HOLD', {'reason': f'Volatilidad inadecuada ({volatility_ratio:.1f}x)'}
            
            # Filtro 3: Sesión de mercado
            if self.session_filter:
                current_hour = datetime.utcnow().hour
                # Solo operar en sesiones principales (London: 8-17, NY: 13-22, Overlap: 13-17)
                if not ((8 <= current_hour <= 17) or (13 <= current_hour <= 22)):
                    return False, 'HOLD', {'reason': 'Fuera de sesiones principales'}
            
            # Filtro 4: Confirmación de múltiples timeframes (simplificado)
            if len(signals.get('reasons', [])) < 3:
                return False, 'HOLD', {'reason': 'Insuficientes confirmaciones'}
            
            # Filtro 5: Evitar noticias de alto impacto (simplificado - evitar viernes tarde)
            current_time = datetime.utcnow()
            if current_time.weekday() == 4 and current_time.hour >= 20:  # Viernes después 8pm UTC
                return False, 'HOLD', {'reason': 'Evitar cierre semanal'}
            
            # DECISIÓN FINAL CON MACHINE LEARNING
            latest = df.iloc[-1]
            entry_price = latest['close']
            current_session = self._get_current_session()
            
            # Aplicar ML si está disponible
            if self.ml_enabled and self.ml_system:
                ml_should_trade, ml_confidence, ml_reason = self.ml_system.should_trade_with_ml(
                    base_should_trade=True,
                    base_confidence=signals['confidence'],
                    current_session=current_session,
                    indicators=latest.to_dict()
                )
                
                if not ml_should_trade:
                    return False, 'HOLD', {'reason': f'ML rejected: {ml_reason}'}
                
                # Usar confianza ajustada por ML
                final_confidence = ml_confidence
                ml_status = f"ML enhanced: {ml_reason}"
            else:
                final_confidence = signals['confidence']
                ml_status = "ML not available"
            
            # Calcular SL y TP dinámicos
            sl, tp = self.calculate_dynamic_stops(signals['signal'], entry_price, df)
            
            trade_info = {
                'signal': signals['signal'],
                'confidence': final_confidence,
                'entry_price': entry_price,
                'stop_loss': sl,
                'take_profit': tp,
                'reasons': signals['reasons'],
                'market_regime': signals['market_regime'],
                'signal_strength': signals['signal_strength'],
                'filters_passed': 'All premium filters passed',
                'ml_status': ml_status,
                'session': current_session,
                'indicators': latest.to_dict()
            }
            
            return True, signals['signal'], trade_info
            
        except Exception as e:
            logger.error(f"Error determinando si operar (premium): {e}")
            return False, 'HOLD', {'reason': 'Error en análisis premium'}
    
    def _get_current_session(self) -> str:
        """Determinar sesión de mercado actual"""
        hour = datetime.utcnow().hour
        
        if 13 <= hour <= 17:
            return 'overlap'
        elif 8 <= hour <= 17:
            return 'london'
        elif 13 <= hour <= 22:
            return 'new_york'
        else:
            return 'asian'
    
    def record_trade_result(self, trade_data: Dict):
        """Registrar resultado de trade para aprendizaje ML"""
        try:
            if self.ml_enabled and self.ml_system:
                self.ml_system.record_trade(trade_data)
                logger.info("Trade registrado en sistema ML para aprendizaje")
        except Exception as e:
            logger.error(f"Error registrando trade en ML: {e}")
    
    def get_ml_stats(self) -> Dict:
        """Obtener estadísticas de Machine Learning"""
        try:
            if self.ml_enabled and self.ml_system:
                return self.ml_system.get_learning_stats()
            else:
                return {'ml_enabled': False, 'message': 'ML no disponible'}
        except Exception as e:
            logger.error(f"Error obteniendo stats ML: {e}")
            return {'error': str(e)}

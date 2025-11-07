"""
Estrategia de Swing Trading
Operaciones de 50-150 pips con duración de horas a días
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class SwingStrategy:
    def __init__(self, mt5_connector, analyzer, risk_manager):
        self.mt5 = mt5_connector
        self.analyzer = analyzer
        self.risk_manager = risk_manager
        
        # Configuración swing
        self.min_pip_target = 50
        self.max_pip_target = 150
        self.stop_loss_pips = 25
        self.min_confidence = 80
        
        # Indicadores para swing
        self.trend_ema_fast = 21
        self.trend_ema_slow = 55
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        
    async def find_opportunities(self, config: Dict) -> List[Dict]:
        """Encontrar oportunidades de swing trading"""
        try:
            opportunities = []
            
            # Obtener datos H1 y H4
            df_h1 = await self.mt5.get_rates(symbol="EURUSD", timeframe="H1", count=100)
            df_h4 = await self.mt5.get_rates(symbol="EURUSD", timeframe="H4", count=50)
            
            if df_h1.empty or df_h4.empty:
                return opportunities
            
            # Calcular indicadores
            df_h1 = self._calculate_swing_indicators(df_h1)
            df_h4 = self._calculate_swing_indicators(df_h4)
            
            # Detectar señales
            h1_signals = self._detect_swing_signals(df_h1, "H1")
            h4_signals = self._detect_swing_signals(df_h4, "H4")
            
            # Validar y combinar
            for signal in h1_signals + h4_signals:
                if signal['confidence'] >= self.min_confidence:
                    if await self._validate_swing_signal(signal, df_h1, df_h4):
                        opportunities.append(signal)
            
            return opportunities[:2]  # Máximo 2 swing trades
            
        except Exception as e:
            logger.error(f"Error en swing strategy: {e}")
            return []
    
    def _calculate_swing_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcular indicadores para swing trading"""
        try:
            # EMAs para tendencia
            df['ema_21'] = df['close'].ewm(span=self.trend_ema_fast).mean()
            df['ema_55'] = df['close'].ewm(span=self.trend_ema_slow).mean()
            
            # MACD
            ema_fast = df['close'].ewm(span=self.macd_fast).mean()
            ema_slow = df['close'].ewm(span=self.macd_slow).mean()
            df['macd'] = ema_fast - ema_slow
            df['macd_signal'] = df['macd'].ewm(span=self.macd_signal).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # ATR
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            true_range = np.maximum(high_low, np.maximum(high_close, low_close))
            df['atr'] = true_range.rolling(window=14).mean()
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculando indicadores swing: {e}")
            return df
    
    def _detect_swing_signals(self, df: pd.DataFrame, timeframe: str) -> List[Dict]:
        """Detectar señales de swing"""
        try:
            signals = []
            
            if len(df) < 30:
                return signals
            
            latest = df.iloc[-1]
            previous = df.iloc[-2]
            
            # Señal 1: EMA trend + MACD confirmation
            if self._detect_trend_signal(df, latest, previous):
                signal = self._create_trend_signal(df, latest, timeframe)
                if signal:
                    signals.append(signal)
            
            # Señal 2: RSI divergence
            if self._detect_rsi_divergence(df, latest):
                signal = self._create_divergence_signal(df, latest, timeframe)
                if signal:
                    signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error detectando señales swing: {e}")
            return []
    
    def _detect_trend_signal(self, df: pd.DataFrame, latest: pd.Series, previous: pd.Series) -> bool:
        """Detectar señal de tendencia"""
        try:
            # EMA crossover
            ema_cross_bull = (latest['ema_21'] > latest['ema_55'] and 
                             previous['ema_21'] <= previous['ema_55'])
            ema_cross_bear = (latest['ema_21'] < latest['ema_55'] and 
                             previous['ema_21'] >= previous['ema_55'])
            
            if not (ema_cross_bull or ema_cross_bear):
                return False
            
            # MACD confirmation
            macd_confirm = (ema_cross_bull and latest['macd'] > latest['macd_signal']) or \
                          (ema_cross_bear and latest['macd'] < latest['macd_signal'])
            
            return macd_confirm
            
        except Exception as e:
            logger.error(f"Error detectando señal de tendencia: {e}")
            return False
    
    def _create_trend_signal(self, df: pd.DataFrame, latest: pd.Series, timeframe: str) -> Optional[Dict]:
        """Crear señal de tendencia"""
        try:
            signal_type = "BUY" if latest['ema_21'] > latest['ema_55'] else "SELL"
            
            # Calcular confianza
            ema_strength = abs(latest['ema_21'] - latest['ema_55']) / latest['close'] * 1000
            macd_strength = abs(latest['macd_histogram']) * 10000
            rsi_position = 50 - abs(latest['rsi'] - 50)  # Bonus si RSI no está en extremos
            
            confidence = min(95, 70 + ema_strength + macd_strength + rsi_position * 0.3)
            
            # SL y TP
            atr = latest['atr']
            entry_price = latest['close']
            
            if signal_type == "BUY":
                stop_loss = entry_price - atr * 2
                take_profit = entry_price + atr * 4
            else:
                stop_loss = entry_price + atr * 2
                take_profit = entry_price - atr * 4
            
            return {
                'signal': signal_type,
                'confidence': confidence,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'timeframe': timeframe,
                'strategy': 'swing_trend',
                'reasons': [
                    f"EMA {self.trend_ema_fast}/{self.trend_ema_slow} trend",
                    f"MACD confirmation",
                    f"ATR: {atr*10000:.1f} pips"
                ],
                'symbol': 'EURUSD',
                'risk_pips': atr * 2 * 10000,
                'reward_pips': atr * 4 * 10000
            }
            
        except Exception as e:
            logger.error(f"Error creando señal de tendencia: {e}")
            return None
    
    def _detect_rsi_divergence(self, df: pd.DataFrame, latest: pd.Series) -> bool:
        """Detectar divergencia RSI (simplificado)"""
        try:
            if len(df) < 20:
                return False
            
            # Buscar extremos RSI recientes
            recent_data = df.tail(20)
            
            # RSI oversold con precio haciendo nuevo mínimo
            min_price_idx = recent_data['low'].idxmin()
            min_rsi_idx = recent_data['rsi'].idxmin()
            
            # Divergencia alcista: precio baja pero RSI sube
            bullish_div = (min_price_idx < min_rsi_idx and 
                          recent_data.loc[min_rsi_idx, 'rsi'] < 30)
            
            # RSI overbought con precio haciendo nuevo máximo
            max_price_idx = recent_data['high'].idxmax()
            max_rsi_idx = recent_data['rsi'].idxmax()
            
            # Divergencia bajista: precio sube pero RSI baja
            bearish_div = (max_price_idx < max_rsi_idx and 
                          recent_data.loc[max_rsi_idx, 'rsi'] > 70)
            
            return bullish_div or bearish_div
            
        except Exception as e:
            logger.error(f"Error detectando divergencia RSI: {e}")
            return False
    
    def _create_divergence_signal(self, df: pd.DataFrame, latest: pd.Series, timeframe: str) -> Optional[Dict]:
        """Crear señal de divergencia"""
        try:
            rsi = latest['rsi']
            signal_type = "BUY" if rsi < 40 else "SELL"
            
            # Confianza basada en extremo RSI
            rsi_extreme = abs(50 - rsi) / 50 * 100
            confidence = min(88, 60 + rsi_extreme * 0.4)
            
            # SL y TP conservadores
            atr = latest['atr']
            entry_price = latest['close']
            
            if signal_type == "BUY":
                stop_loss = entry_price - atr * 1.5
                take_profit = entry_price + atr * 3
            else:
                stop_loss = entry_price + atr * 1.5
                take_profit = entry_price - atr * 3
            
            return {
                'signal': signal_type,
                'confidence': confidence,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'timeframe': timeframe,
                'strategy': 'swing_divergence',
                'reasons': [
                    f"RSI divergence at {rsi:.1f}",
                    f"Mean reversion expected",
                    f"R:R = 1:2"
                ],
                'symbol': 'EURUSD',
                'risk_pips': atr * 1.5 * 10000,
                'reward_pips': atr * 3 * 10000
            }
            
        except Exception as e:
            logger.error(f"Error creando señal de divergencia: {e}")
            return None
    
    async def _validate_swing_signal(self, signal: Dict, df_h1: pd.DataFrame, df_h4: pd.DataFrame) -> bool:
        """Validar señal de swing"""
        try:
            # R:R mínimo
            if signal['reward_pips'] / signal['risk_pips'] < 1.8:
                return False
            
            # Coherencia entre timeframes
            h1_trend = self._get_trend_direction(df_h1)
            h4_trend = self._get_trend_direction(df_h4)
            
            signal_dir = 1 if signal['signal'] == 'BUY' else -1
            
            # Al menos H4 debe estar alineado
            return h4_trend * signal_dir > 0
            
        except Exception as e:
            logger.error(f"Error validando swing signal: {e}")
            return False
    
    def _get_trend_direction(self, df: pd.DataFrame) -> float:
        """Obtener dirección de tendencia"""
        try:
            latest = df.iloc[-1]
            if 'ema_21' in latest and 'ema_55' in latest:
                if latest['ema_21'] > latest['ema_55']:
                    return 1.0
                elif latest['ema_21'] < latest['ema_55']:
                    return -1.0
            return 0.0
            
        except Exception as e:
            logger.error(f"Error obteniendo dirección de tendencia: {e}")
            return 0.0

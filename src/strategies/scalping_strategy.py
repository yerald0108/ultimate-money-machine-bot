"""
Estrategia de Scalping Inteligente
Operaciones rápidas de 5-15 pips con alta frecuencia y precisión
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class ScalpingStrategy:
    def __init__(self, mt5_connector, analyzer, risk_manager):
        self.mt5 = mt5_connector
        self.analyzer = analyzer
        self.risk_manager = risk_manager
        
        # Configuración específica de scalping
        self.min_pip_target = 5
        self.max_pip_target = 15
        self.stop_loss_pips = 3
        self.max_spread = 2.0  # pips
        self.min_confidence = 70
        
        # Indicadores optimizados para scalping
        self.fast_ema_period = 5
        self.slow_ema_period = 13
        self.rsi_period = 7
        self.bb_period = 10
        self.atr_period = 7
        
        # Control de frecuencia
        self.min_time_between_trades = 30  # segundos
        self.last_trade_time = None
        self.max_trades_per_hour = 10
        self.hourly_trade_count = {}
        
        # Filtros de calidad
        self.momentum_threshold = 0.3
        self.volatility_min = 0.5
        self.volatility_max = 3.0
        
    async def find_opportunities(self, config: Dict) -> List[Dict]:
        """Encontrar oportunidades de scalping"""
        try:
            opportunities = []
            
            # Verificar condiciones básicas
            if not await self._check_scalping_conditions():
                return opportunities
            
            # Obtener datos de M1 y M5
            df_m1 = await self.mt5.get_rates(symbol="EURUSD", timeframe="M1", count=50)
            df_m5 = await self.mt5.get_rates(symbol="EURUSD", timeframe="M5", count=30)
            
            if df_m1.empty or df_m5.empty:
                return opportunities
            
            # Calcular indicadores específicos para scalping
            df_m1 = self._calculate_scalping_indicators(df_m1)
            df_m5 = self._calculate_scalping_indicators(df_m5)
            
            # Buscar señales de scalping
            m1_signals = self._detect_scalping_signals(df_m1, "M1")
            m5_signals = self._detect_scalping_signals(df_m5, "M5")
            
            # Combinar y validar señales
            for signal in m1_signals + m5_signals:
                if signal['confidence'] >= self.min_confidence:
                    # Validar con múltiples filtros
                    if await self._validate_scalping_signal(signal, df_m1, df_m5):
                        opportunities.append(signal)
            
            # Limitar oportunidades por hora
            opportunities = self._filter_by_frequency_limits(opportunities)
            
            logger.info(f"🎯 Scalping: {len(opportunities)} oportunidades encontradas")
            return opportunities
            
        except Exception as e:
            logger.error(f"Error buscando oportunidades de scalping: {e}")
            return []
    
    async def _check_scalping_conditions(self) -> bool:
        """Verificar condiciones básicas para scalping"""
        try:
            # Verificar spread
            spread = await self._get_current_spread()
            if spread > self.max_spread:
                logger.debug(f"Spread muy alto para scalping: {spread} pips")
                return False
            
            # Verificar sesión activa
            current_session = self._get_current_session()
            if current_session not in ['london', 'new_york', 'overlap']:
                logger.debug(f"Sesión no óptima para scalping: {current_session}")
                return False
            
            # Verificar tiempo desde último trade
            if self.last_trade_time:
                time_diff = (datetime.now() - self.last_trade_time).total_seconds()
                if time_diff < self.min_time_between_trades:
                    return False
            
            # Verificar límite de trades por hora
            current_hour = datetime.now().hour
            hourly_count = self.hourly_trade_count.get(current_hour, 0)
            if hourly_count >= self.max_trades_per_hour:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verificando condiciones de scalping: {e}")
            return False
    
    def _calculate_scalping_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcular indicadores específicos para scalping"""
        try:
            # EMAs rápidas para scalping
            df['ema_fast'] = df['close'].ewm(span=self.fast_ema_period).mean()
            df['ema_slow'] = df['close'].ewm(span=self.slow_ema_period).mean()
            df['ema_diff'] = df['ema_fast'] - df['ema_slow']
            df['ema_diff_pct'] = (df['ema_diff'] / df['close']) * 10000  # en pips
            
            # RSI rápido
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
            rs = gain / loss
            df['rsi_fast'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands ajustadas
            df['bb_middle'] = df['close'].rolling(window=self.bb_period).mean()
            bb_std = df['close'].rolling(window=self.bb_period).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 1.5)  # Bandas más ajustadas
            df['bb_lower'] = df['bb_middle'] - (bb_std * 1.5)
            df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            
            # ATR para volatilidad
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            true_range = np.maximum(high_low, np.maximum(high_close, low_close))
            df['atr'] = true_range.rolling(window=self.atr_period).mean()
            df['atr_pips'] = df['atr'] * 10000
            
            # Momentum para scalping
            df['momentum'] = df['close'].pct_change(periods=3) * 10000  # en pips
            df['momentum_ma'] = df['momentum'].rolling(window=5).mean()
            
            # Volumen tick (si está disponible)
            if 'tick_volume' in df.columns:
                df['volume_ma'] = df['tick_volume'].rolling(window=10).mean()
                df['volume_ratio'] = df['tick_volume'] / df['volume_ma']
            else:
                df['volume_ratio'] = 1.0
            
            # Precio vs EMAs
            df['price_above_ema_fast'] = df['close'] > df['ema_fast']
            df['price_above_ema_slow'] = df['close'] > df['ema_slow']
            df['emas_aligned_bull'] = df['ema_fast'] > df['ema_slow']
            df['emas_aligned_bear'] = df['ema_fast'] < df['ema_slow']
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculando indicadores de scalping: {e}")
            return df
    
    def _detect_scalping_signals(self, df: pd.DataFrame, timeframe: str) -> List[Dict]:
        """Detectar señales específicas de scalping"""
        try:
            signals = []
            
            if len(df) < 20:
                return signals
            
            latest = df.iloc[-1]
            previous = df.iloc[-2]
            
            # SEÑAL 1: EMA Crossover con momentum
            if self._detect_ema_crossover_signal(df, latest, previous, timeframe):
                signals.append(self._create_ema_crossover_signal(df, latest, timeframe))
            
            # SEÑAL 2: RSI Reversal en extremos
            if self._detect_rsi_reversal_signal(df, latest, previous, timeframe):
                signals.append(self._create_rsi_reversal_signal(df, latest, timeframe))
            
            # SEÑAL 3: Bollinger Band Bounce
            if self._detect_bb_bounce_signal(df, latest, previous, timeframe):
                signals.append(self._create_bb_bounce_signal(df, latest, timeframe))
            
            # SEÑAL 4: Momentum Breakout
            if self._detect_momentum_breakout_signal(df, latest, previous, timeframe):
                signals.append(self._create_momentum_breakout_signal(df, latest, timeframe))
            
            return [s for s in signals if s is not None]
            
        except Exception as e:
            logger.error(f"Error detectando señales de scalping: {e}")
            return []
    
    def _detect_ema_crossover_signal(self, df: pd.DataFrame, latest: pd.Series, previous: pd.Series, timeframe: str) -> bool:
        """Detectar cruce de EMAs con confirmación"""
        try:
            # Cruce alcista
            bullish_cross = (latest['ema_fast'] > latest['ema_slow'] and 
                           previous['ema_fast'] <= previous['ema_slow'])
            
            # Cruce bajista
            bearish_cross = (latest['ema_fast'] < latest['ema_slow'] and 
                           previous['ema_fast'] >= previous['ema_slow'])
            
            if not (bullish_cross or bearish_cross):
                return False
            
            # Confirmación con momentum
            momentum_confirm = abs(latest['momentum']) > self.momentum_threshold
            
            # Confirmación con volumen
            volume_confirm = latest['volume_ratio'] > 1.1
            
            # Volatilidad apropiada
            volatility_ok = self.volatility_min <= latest['atr_pips'] <= self.volatility_max * (2 if timeframe == "M1" else 1)
            
            return momentum_confirm and volume_confirm and volatility_ok
            
        except Exception as e:
            logger.error(f"Error detectando cruce EMA: {e}")
            return False
    
    def _create_ema_crossover_signal(self, df: pd.DataFrame, latest: pd.Series, timeframe: str) -> Optional[Dict]:
        """Crear señal de cruce EMA"""
        try:
            signal_type = "BUY" if latest['ema_fast'] > latest['ema_slow'] else "SELL"
            
            # Calcular confianza
            ema_strength = abs(latest['ema_diff_pct'])
            momentum_strength = abs(latest['momentum']) / 2
            volume_strength = min(50, (latest['volume_ratio'] - 1) * 100)
            
            confidence = min(95, 60 + ema_strength + momentum_strength + volume_strength)
            
            # Calcular SL y TP
            atr_pips = latest['atr_pips']
            
            if signal_type == "BUY":
                entry_price = latest['close']
                stop_loss = entry_price - (atr_pips * 0.8) / 10000
                take_profit = entry_price + (atr_pips * 1.5) / 10000
            else:
                entry_price = latest['close']
                stop_loss = entry_price + (atr_pips * 0.8) / 10000
                take_profit = entry_price - (atr_pips * 1.5) / 10000
            
            return {
                'signal': signal_type,
                'confidence': confidence,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'timeframe': timeframe,
                'strategy': 'ema_crossover',
                'reasons': [
                    f"EMA {self.fast_ema_period}/{self.slow_ema_period} crossover",
                    f"Momentum: {latest['momentum']:.1f} pips",
                    f"Volume ratio: {latest['volume_ratio']:.2f}"
                ],
                'symbol': 'EURUSD',
                'risk_pips': atr_pips * 0.8,
                'reward_pips': atr_pips * 1.5
            }
            
        except Exception as e:
            logger.error(f"Error creando señal EMA crossover: {e}")
            return None
    
    def _detect_rsi_reversal_signal(self, df: pd.DataFrame, latest: pd.Series, previous: pd.Series, timeframe: str) -> bool:
        """Detectar reversión RSI en extremos"""
        try:
            rsi = latest['rsi_fast']
            prev_rsi = previous['rsi_fast']
            
            # RSI oversold reversal (compra)
            oversold_reversal = (prev_rsi <= 25 and rsi > 25 and rsi > prev_rsi)
            
            # RSI overbought reversal (venta)
            overbought_reversal = (prev_rsi >= 75 and rsi < 75 and rsi < prev_rsi)
            
            if not (oversold_reversal or overbought_reversal):
                return False
            
            # Confirmación con precio vs Bollinger Bands
            if oversold_reversal:
                price_confirm = latest['bb_position'] < 0.2  # Cerca de banda inferior
            else:
                price_confirm = latest['bb_position'] > 0.8  # Cerca de banda superior
            
            # Volatilidad apropiada
            volatility_ok = latest['atr_pips'] >= self.volatility_min
            
            return price_confirm and volatility_ok
            
        except Exception as e:
            logger.error(f"Error detectando reversión RSI: {e}")
            return False
    
    def _create_rsi_reversal_signal(self, df: pd.DataFrame, latest: pd.Series, timeframe: str) -> Optional[Dict]:
        """Crear señal de reversión RSI"""
        try:
            rsi = latest['rsi_fast']
            signal_type = "BUY" if rsi <= 30 else "SELL"
            
            # Calcular confianza
            rsi_extreme = abs(50 - rsi) / 50 * 100  # Qué tan extremo es el RSI
            bb_position_strength = abs(0.5 - latest['bb_position']) * 100
            
            confidence = min(90, 55 + rsi_extreme * 0.3 + bb_position_strength * 0.2)
            
            # Calcular SL y TP conservadores
            atr_pips = latest['atr_pips']
            
            if signal_type == "BUY":
                entry_price = latest['close']
                stop_loss = entry_price - (atr_pips * 0.6) / 10000
                take_profit = entry_price + (atr_pips * 1.2) / 10000
            else:
                entry_price = latest['close']
                stop_loss = entry_price + (atr_pips * 0.6) / 10000
                take_profit = entry_price - (atr_pips * 1.2) / 10000
            
            return {
                'signal': signal_type,
                'confidence': confidence,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'timeframe': timeframe,
                'strategy': 'rsi_reversal',
                'reasons': [
                    f"RSI reversal from {rsi:.1f}",
                    f"BB position: {latest['bb_position']:.2f}",
                    f"ATR: {atr_pips:.1f} pips"
                ],
                'symbol': 'EURUSD',
                'risk_pips': atr_pips * 0.6,
                'reward_pips': atr_pips * 1.2
            }
            
        except Exception as e:
            logger.error(f"Error creando señal RSI reversal: {e}")
            return None
    
    def _detect_bb_bounce_signal(self, df: pd.DataFrame, latest: pd.Series, previous: pd.Series, timeframe: str) -> bool:
        """Detectar rebote en Bollinger Bands"""
        try:
            # Rebote desde banda inferior (compra)
            lower_bounce = (previous['close'] <= previous['bb_lower'] and 
                          latest['close'] > latest['bb_lower'] and
                          latest['close'] > previous['close'])
            
            # Rebote desde banda superior (venta)
            upper_bounce = (previous['close'] >= previous['bb_upper'] and 
                          latest['close'] < latest['bb_upper'] and
                          latest['close'] < previous['close'])
            
            if not (lower_bounce or upper_bounce):
                return False
            
            # Confirmación con momentum
            if lower_bounce:
                momentum_confirm = latest['momentum'] > 0.2
            else:
                momentum_confirm = latest['momentum'] < -0.2
            
            return momentum_confirm
            
        except Exception as e:
            logger.error(f"Error detectando rebote BB: {e}")
            return False
    
    def _create_bb_bounce_signal(self, df: pd.DataFrame, latest: pd.Series, timeframe: str) -> Optional[Dict]:
        """Crear señal de rebote BB"""
        try:
            # Determinar dirección
            if latest['close'] > latest['bb_lower'] and latest['momentum'] > 0:
                signal_type = "BUY"
                target_level = latest['bb_middle']
            else:
                signal_type = "SELL"
                target_level = latest['bb_middle']
            
            # Calcular confianza
            bb_distance = abs(latest['bb_position'] - 0.5) * 100
            momentum_strength = abs(latest['momentum']) * 10
            
            confidence = min(85, 50 + bb_distance * 0.4 + momentum_strength)
            
            # SL y TP basados en bandas
            entry_price = latest['close']
            bb_width = latest['bb_upper'] - latest['bb_lower']
            
            if signal_type == "BUY":
                stop_loss = latest['bb_lower'] - bb_width * 0.1
                take_profit = target_level
            else:
                stop_loss = latest['bb_upper'] + bb_width * 0.1
                take_profit = target_level
            
            risk_pips = abs(entry_price - stop_loss) * 10000
            reward_pips = abs(take_profit - entry_price) * 10000
            
            return {
                'signal': signal_type,
                'confidence': confidence,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'timeframe': timeframe,
                'strategy': 'bb_bounce',
                'reasons': [
                    f"BB bounce from {latest['bb_position']:.2f}",
                    f"Momentum: {latest['momentum']:.2f}",
                    f"Target: BB middle"
                ],
                'symbol': 'EURUSD',
                'risk_pips': risk_pips,
                'reward_pips': reward_pips
            }
            
        except Exception as e:
            logger.error(f"Error creando señal BB bounce: {e}")
            return None
    
    def _detect_momentum_breakout_signal(self, df: pd.DataFrame, latest: pd.Series, previous: pd.Series, timeframe: str) -> bool:
        """Detectar breakout de momentum"""
        try:
            # Momentum fuerte y creciente
            strong_momentum = abs(latest['momentum']) > 0.5
            increasing_momentum = abs(latest['momentum']) > abs(previous['momentum'])
            
            if not (strong_momentum and increasing_momentum):
                return False
            
            # Confirmación con EMAs
            ema_alignment = (latest['momentum'] > 0 and latest['emas_aligned_bull']) or \
                          (latest['momentum'] < 0 and latest['emas_aligned_bear'])
            
            # Volumen confirmatorio
            volume_confirm = latest['volume_ratio'] > 1.2
            
            return ema_alignment and volume_confirm
            
        except Exception as e:
            logger.error(f"Error detectando breakout momentum: {e}")
            return False
    
    def _create_momentum_breakout_signal(self, df: pd.DataFrame, latest: pd.Series, timeframe: str) -> Optional[Dict]:
        """Crear señal de breakout momentum"""
        try:
            signal_type = "BUY" if latest['momentum'] > 0 else "SELL"
            
            # Confianza basada en fuerza del momentum
            momentum_strength = min(40, abs(latest['momentum']) * 20)
            volume_strength = min(20, (latest['volume_ratio'] - 1) * 50)
            ema_strength = 15 if latest['emas_aligned_bull'] or latest['emas_aligned_bear'] else 0
            
            confidence = min(92, 55 + momentum_strength + volume_strength + ema_strength)
            
            # SL y TP agresivos para breakout
            atr_pips = latest['atr_pips']
            entry_price = latest['close']
            
            if signal_type == "BUY":
                stop_loss = entry_price - (atr_pips * 0.7) / 10000
                take_profit = entry_price + (atr_pips * 2.0) / 10000
            else:
                stop_loss = entry_price + (atr_pips * 0.7) / 10000
                take_profit = entry_price - (atr_pips * 2.0) / 10000
            
            return {
                'signal': signal_type,
                'confidence': confidence,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'timeframe': timeframe,
                'strategy': 'momentum_breakout',
                'reasons': [
                    f"Strong momentum: {latest['momentum']:.2f}",
                    f"Volume surge: {latest['volume_ratio']:.2f}x",
                    f"EMA alignment confirmed"
                ],
                'symbol': 'EURUSD',
                'risk_pips': atr_pips * 0.7,
                'reward_pips': atr_pips * 2.0
            }
            
        except Exception as e:
            logger.error(f"Error creando señal momentum breakout: {e}")
            return None
    
    async def _validate_scalping_signal(self, signal: Dict, df_m1: pd.DataFrame, df_m5: pd.DataFrame) -> bool:
        """Validar señal de scalping con filtros adicionales"""
        try:
            # Filtro 1: Relación riesgo/beneficio mínima
            risk_reward = signal['reward_pips'] / signal['risk_pips']
            if risk_reward < 1.5:  # Mínimo 1:1.5
                return False
            
            # Filtro 2: Coherencia entre timeframes
            m1_trend = self._get_short_term_trend(df_m1)
            m5_trend = self._get_short_term_trend(df_m5)
            
            signal_direction = 1 if signal['signal'] == 'BUY' else -1
            
            # Al menos uno de los timeframes debe estar alineado
            if not (m1_trend * signal_direction > 0 or m5_trend * signal_direction > 0):
                return False
            
            # Filtro 3: No operar contra tendencia fuerte en M5
            if abs(m5_trend) > 0.7 and m5_trend * signal_direction < 0:
                return False
            
            # Filtro 4: Spread actual
            current_spread = await self._get_current_spread()
            if current_spread > self.max_spread:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validando señal de scalping: {e}")
            return False
    
    def _get_short_term_trend(self, df: pd.DataFrame) -> float:
        """Obtener tendencia de corto plazo (-1 a 1)"""
        try:
            if len(df) < 10:
                return 0.0
            
            latest = df.iloc[-1]
            
            # Usar EMAs para determinar tendencia
            if 'ema_fast' in latest and 'ema_slow' in latest:
                ema_diff = (latest['ema_fast'] - latest['ema_slow']) / latest['close']
                return max(-1.0, min(1.0, ema_diff * 1000))  # Normalizar
            
            # Fallback: usar precio vs SMA
            sma_10 = df['close'].tail(10).mean()
            price_vs_sma = (latest['close'] - sma_10) / sma_10
            
            return max(-1.0, min(1.0, price_vs_sma * 100))
            
        except Exception as e:
            logger.error(f"Error calculando tendencia corto plazo: {e}")
            return 0.0
    
    def _filter_by_frequency_limits(self, opportunities: List[Dict]) -> List[Dict]:
        """Filtrar oportunidades por límites de frecuencia"""
        try:
            current_hour = datetime.now().hour
            current_count = self.hourly_trade_count.get(current_hour, 0)
            
            # Calcular cuántas oportunidades podemos tomar
            remaining_slots = max(0, self.max_trades_per_hour - current_count)
            
            if remaining_slots == 0:
                return []
            
            # Ordenar por confianza y tomar las mejores
            sorted_opportunities = sorted(opportunities, key=lambda x: x['confidence'], reverse=True)
            
            return sorted_opportunities[:remaining_slots]
            
        except Exception as e:
            logger.error(f"Error filtrando por frecuencia: {e}")
            return opportunities[:1]  # Fallback: solo la primera
    
    async def _get_current_spread(self) -> float:
        """Obtener spread actual en pips"""
        try:
            symbol_info = await self.mt5.get_symbol_info("EURUSD")
            if symbol_info:
                spread = symbol_info.get('spread', 20) / 10
                return spread
            return 2.0
            
        except Exception as e:
            logger.error(f"Error obteniendo spread: {e}")
            return 2.0
    
    def _get_current_session(self) -> str:
        """Obtener sesión actual del mercado"""
        hour = datetime.utcnow().hour
        
        if 13 <= hour <= 17:
            return 'overlap'
        elif 8 <= hour <= 17:
            return 'london'
        elif 13 <= hour <= 22:
            return 'new_york'
        else:
            return 'asian'
    
    def record_trade_execution(self, signal: Dict):
        """Registrar ejecución de trade para control de frecuencia"""
        try:
            self.last_trade_time = datetime.now()
            current_hour = self.last_trade_time.hour
            
            # Incrementar contador horario
            self.hourly_trade_count[current_hour] = self.hourly_trade_count.get(current_hour, 0) + 1
            
            # Limpiar contadores de horas pasadas
            current_time = datetime.now()
            hours_to_remove = []
            
            for hour, count in self.hourly_trade_count.items():
                hour_time = current_time.replace(hour=hour, minute=0, second=0, microsecond=0)
                if (current_time - hour_time).total_seconds() > 3600:  # Más de 1 hora
                    hours_to_remove.append(hour)
            
            for hour in hours_to_remove:
                del self.hourly_trade_count[hour]
            
            logger.info(f"📊 Scalping trade registrado. Trades esta hora: {self.hourly_trade_count.get(current_hour, 0)}")
            
        except Exception as e:
            logger.error(f"Error registrando ejecución de trade: {e}")
    
    def get_strategy_status(self) -> Dict:
        """Obtener estado actual de la estrategia"""
        try:
            current_hour = datetime.now().hour
            current_session = self._get_current_session()
            
            return {
                'strategy': 'Scalping',
                'active': current_session in ['london', 'new_york', 'overlap'],
                'current_session': current_session,
                'trades_this_hour': self.hourly_trade_count.get(current_hour, 0),
                'max_trades_per_hour': self.max_trades_per_hour,
                'last_trade_time': self.last_trade_time.strftime('%H:%M:%S') if self.last_trade_time else 'None',
                'target_pips': f"{self.min_pip_target}-{self.max_pip_target}",
                'stop_loss_pips': self.stop_loss_pips,
                'max_spread': self.max_spread
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de estrategia: {e}")
            return {'strategy': 'Scalping', 'error': str(e)}

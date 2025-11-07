"""
Motor de Trading Principal
Coordina el análisis de mercado y la ejecución de trades
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import MetaTrader5 as mt5

from .mt5_connector import MT5Connector
from ..analysis.market_analyzer import MarketAnalyzer

logger = logging.getLogger(__name__)

class TradingEngine:
    def __init__(self, mt5_connector: MT5Connector, market_analyzer: MarketAnalyzer):
        self.mt5 = mt5_connector
        self.analyzer = market_analyzer
        self.trading_active = False
        self.last_analysis_time = None
        self.daily_trades = 0
        self.daily_profit = 0.0
        self.max_daily_trades = 10
        self.analysis_interval = 300  # 5 minutos
        
        # Configuración de riesgo
        self.risk_percentage = float(os.getenv('RISK_PERCENTAGE', 2.0))
        self.max_daily_loss = float(os.getenv('MAX_DAILY_LOSS', 100.0))
        self.trade_amount = float(os.getenv('TRADE_AMOUNT', 0.1))
        self.stop_loss_pips = int(os.getenv('STOP_LOSS_PIPS', 20))
        self.take_profit_pips = int(os.getenv('TAKE_PROFIT_PIPS', 40))
        
        # Estadísticas del día
        self.daily_stats = {
            'trades_count': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'profit': 0.0,
            'signals_detected': 0,
            'last_reset': datetime.now().date()
        }
        
        # Task para análisis continuo
        self.analysis_task = None
    
    async def start_trading(self) -> Dict:
        """Iniciar trading automatizado"""
        try:
            if not self.mt5.is_connected():
                return {'success': False, 'error': 'No hay conexión con MT5'}
            
            # Verificar límites diarios
            if not self._check_daily_limits():
                return {'success': False, 'error': 'Límites diarios alcanzados'}
            
            self.trading_active = True
            
            # Iniciar análisis continuo
            if self.analysis_task is None or self.analysis_task.done():
                self.analysis_task = asyncio.create_task(self._continuous_analysis())
            
            logger.info("Trading automatizado iniciado")
            return {'success': True, 'message': 'Trading iniciado correctamente'}
            
        except Exception as e:
            logger.error(f"Error iniciando trading: {e}")
            return {'success': False, 'error': str(e)}
    
    async def stop_trading(self) -> Dict:
        """Pausar trading automatizado"""
        try:
            self.trading_active = False
            
            # Cancelar task de análisis
            if self.analysis_task and not self.analysis_task.done():
                self.analysis_task.cancel()
            
            logger.info("Trading automatizado pausado")
            return {'success': True, 'message': 'Trading pausado correctamente'}
            
        except Exception as e:
            logger.error(f"Error pausando trading: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _continuous_analysis(self):
        """Análisis continuo del mercado"""
        while self.trading_active:
            try:
                # Verificar límites diarios
                if not self._check_daily_limits():
                    logger.info("Límites diarios alcanzados, pausando trading")
                    self.trading_active = False
                    break
                
                # Realizar análisis
                await self._analyze_and_trade()
                
                # Esperar intervalo
                await asyncio.sleep(self.analysis_interval)
                
            except asyncio.CancelledError:
                logger.info("Análisis continuo cancelado")
                break
            except Exception as e:
                logger.error(f"Error en análisis continuo: {e}")
                await asyncio.sleep(60)  # Esperar 1 minuto antes de reintentar
    
    async def _analyze_and_trade(self):
        """Analizar mercado y ejecutar trades si es necesario"""
        try:
            # Obtener datos del mercado
            df = await self.mt5.get_rates(count=200)
            if df.empty:
                logger.warning("No se pudieron obtener datos del mercado")
                return
            
            # Calcular indicadores técnicos
            df = self.analyzer.calculate_technical_indicators(df)
            
            # Determinar si se debe operar
            should_trade, signal, trade_info = self.analyzer.should_trade(df)
            
            self.daily_stats['signals_detected'] += 1
            
            if should_trade and signal != 'HOLD':
                logger.info(f"Señal detectada: {signal} (Confianza: {trade_info['confidence']}%)")
                
                # Verificar que no hay posiciones abiertas del mismo tipo
                positions = await self.mt5.get_positions(self.mt5.symbol)
                
                # Filtrar posiciones del mismo tipo
                same_type_positions = [
                    pos for pos in positions 
                    if pos['type'].upper() == signal.upper()
                ]
                
                if same_type_positions:
                    logger.info(f"Ya existe posición {signal}, omitiendo nueva entrada")
                    return
                
                # Ejecutar trade
                await self._execute_trade(signal, trade_info)
            
            self.last_analysis_time = datetime.now()
            
        except Exception as e:
            logger.error(f"Error en análisis y trading: {e}")
    
    async def _execute_trade(self, signal: str, trade_info: Dict):
        """Ejecutar un trade"""
        try:
            # Obtener información de la cuenta
            account_info = await self.mt5.get_account_info()
            if not account_info:
                logger.error("No se pudo obtener información de la cuenta")
                return
            
            # Calcular tamaño de lote
            lot_size = self.mt5.calculate_lot_size(
                self.risk_percentage,
                self.stop_loss_pips,
                account_info['balance']
            )
            
            # Usar tamaño configurado si es menor
            lot_size = min(lot_size, self.trade_amount)
            
            # Calcular SL y TP en pips si no están en trade_info
            entry_price = trade_info.get('entry_price')
            stop_loss = trade_info.get('stop_loss')
            take_profit = trade_info.get('take_profit')
            
            # Si no hay SL/TP calculados, usar configuración por defecto
            if not stop_loss or not take_profit:
                symbol_info = await self.mt5.get_symbol_info()
                point = symbol_info.get('point', 0.00001)
                
                if signal == 'BUY':
                    stop_loss = entry_price - (self.stop_loss_pips * point)
                    take_profit = entry_price + (self.take_profit_pips * point)
                else:  # SELL
                    stop_loss = entry_price + (self.stop_loss_pips * point)
                    take_profit = entry_price - (self.take_profit_pips * point)
            
            # Ejecutar orden
            result = await self.mt5.send_order(
                action=signal,
                volume=lot_size,
                sl=stop_loss,
                tp=take_profit,
                comment=f"ForexBot-{signal}-{trade_info['confidence']:.0f}%"
            )
            
            if result['success']:
                self.daily_stats['trades_count'] += 1
                logger.info(f"Trade ejecutado: {signal} {lot_size} lotes - Orden: {result['order']}")
                
                # Log detallado del trade
                logger.info(f"Detalles del trade:")
                logger.info(f"  - Señal: {signal}")
                logger.info(f"  - Confianza: {trade_info['confidence']}%")
                logger.info(f"  - Volumen: {lot_size}")
                logger.info(f"  - Precio entrada: {entry_price}")
                logger.info(f"  - Stop Loss: {stop_loss}")
                logger.info(f"  - Take Profit: {take_profit}")
                logger.info(f"  - Razones: {', '.join(trade_info.get('reasons', []))}")
                
            else:
                logger.error(f"Error ejecutando trade: {result['error']}")
                
        except Exception as e:
            logger.error(f"Error ejecutando trade: {e}")
    
    def _check_daily_limits(self) -> bool:
        """Verificar límites diarios"""
        try:
            # Resetear estadísticas si es un nuevo día
            today = datetime.now().date()
            if self.daily_stats['last_reset'] != today:
                self._reset_daily_stats()
            
            # Verificar límite de trades
            if self.daily_stats['trades_count'] >= self.max_daily_trades:
                logger.warning(f"Límite diario de trades alcanzado: {self.max_daily_trades}")
                return False
            
            # Verificar límite de pérdidas
            if self.daily_stats['profit'] <= -self.max_daily_loss:
                logger.warning(f"Límite diario de pérdidas alcanzado: ${self.max_daily_loss}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verificando límites diarios: {e}")
            return False
    
    def _reset_daily_stats(self):
        """Resetear estadísticas diarias"""
        self.daily_stats = {
            'trades_count': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'profit': 0.0,
            'signals_detected': 0,
            'last_reset': datetime.now().date()
        }
        logger.info("Estadísticas diarias reseteadas")
    
    async def get_status(self) -> Dict:
        """Obtener estado del motor de trading"""
        try:
            # Actualizar estadísticas desde MT5
            await self._update_daily_stats()
            
            return {
                'trading_active': self.trading_active,
                'mt5_connected': self.mt5.is_connected(),
                'last_update': self.last_analysis_time.strftime('%H:%M:%S') if self.last_analysis_time else 'Nunca',
                'signals_today': self.daily_stats['signals_detected'],
                'trades_today': self.daily_stats['trades_count'],
                'profit_today': self.daily_stats['profit'],
                'winning_trades': self.daily_stats['winning_trades'],
                'losing_trades': self.daily_stats['losing_trades']
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado: {e}")
            return {}
    
    async def get_balance(self) -> Dict:
        """Obtener información del balance"""
        try:
            account_info = await self.mt5.get_account_info()
            if not account_info:
                return {}
            
            return {
                'balance': account_info['balance'],
                'equity': account_info['equity'],
                'floating_pl': account_info['profit'],
                'free_margin': account_info['free_margin'],
                'margin': account_info['margin'],
                'margin_level': account_info['margin_level'],
                'risk_per_trade': self.risk_percentage,
                'max_daily_loss': self.max_daily_loss
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo balance: {e}")
            return {}
    
    async def get_market_analysis(self) -> Dict:
        """Obtener análisis actual del mercado"""
        try:
            # Obtener datos del mercado
            df = await self.mt5.get_rates(count=200)
            if df.empty:
                return {}
            
            # Obtener resumen del análisis
            analysis = self.analyzer.get_market_summary(df)
            return analysis
            
        except Exception as e:
            logger.error(f"Error obteniendo análisis de mercado: {e}")
            return {}
    
    async def get_open_positions(self) -> List[Dict]:
        """Obtener posiciones abiertas"""
        try:
            return await self.mt5.get_positions()
        except Exception as e:
            logger.error(f"Error obteniendo posiciones: {e}")
            return []
    
    async def get_settings(self) -> Dict:
        """Obtener configuración actual"""
        return {
            'risk_percentage': self.risk_percentage,
            'trade_amount': self.trade_amount,
            'stop_loss_pips': self.stop_loss_pips,
            'take_profit_pips': self.take_profit_pips,
            'max_daily_loss': self.max_daily_loss,
            'timeframe': '15M',
            'min_confidence': self.analyzer.min_confidence,
            'auto_trading': self.trading_active,
            'notifications': True
        }
    
    async def get_trade_history(self) -> List[Dict]:
        """Obtener historial de trades"""
        try:
            return await self.mt5.get_history_deals(days=7)
        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")
            return []
    
    async def close_all_positions(self) -> Dict:
        """Cerrar todas las posiciones"""
        try:
            return await self.mt5.close_all_positions()
        except Exception as e:
            logger.error(f"Error cerrando posiciones: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _update_daily_stats(self):
        """Actualizar estadísticas diarias desde MT5"""
        try:
            # Obtener trades del día
            today_deals = await self.mt5.get_history_deals(days=1)
            
            if today_deals:
                # Filtrar solo deals de hoy
                today = datetime.now().date()
                today_deals = [
                    deal for deal in today_deals 
                    if deal['time'].date() == today
                ]
                
                # Calcular estadísticas
                self.daily_stats['trades_count'] = len(today_deals)
                self.daily_stats['profit'] = sum(deal['profit'] for deal in today_deals)
                self.daily_stats['winning_trades'] = len([d for d in today_deals if d['profit'] > 0])
                self.daily_stats['losing_trades'] = len([d for d in today_deals if d['profit'] < 0])
                
        except Exception as e:
            logger.error(f"Error actualizando estadísticas diarias: {e}")

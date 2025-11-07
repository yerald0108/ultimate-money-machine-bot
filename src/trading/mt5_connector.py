"""
Conector para MetaTrader 5
Maneja la conexión y operaciones con MT5
"""

import MetaTrader5 as mt5
import pandas as pd
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

class MT5Connector:
    def __init__(self):
        self.login = int(os.getenv('MT5_LOGIN', 0))
        self.password = os.getenv('MT5_PASSWORD', '')
        self.server = os.getenv('MT5_SERVER', '')
        self.connected = False
        self.symbol = "EURUSD"
        
    async def connect(self) -> Dict:
        """Conectar a MT5"""
        try:
            # Inicializar MT5
            if not mt5.initialize():
                error_msg = f"Error al inicializar MT5: {mt5.last_error()}"
                logger.error(error_msg)
                return {'success': False, 'error': error_msg}
            
            # Conectar a la cuenta
            if not mt5.login(self.login, password=self.password, server=self.server):
                error_msg = f"Error al conectar a MT5: {mt5.last_error()}"
                logger.error(error_msg)
                mt5.shutdown()
                return {'success': False, 'error': error_msg}
            
            # Verificar símbolo
            symbol_info = mt5.symbol_info(self.symbol)
            if symbol_info is None:
                error_msg = f"Símbolo {self.symbol} no encontrado"
                logger.error(error_msg)
                return {'success': False, 'error': error_msg}
            
            # Habilitar símbolo si es necesario
            if not symbol_info.visible:
                if not mt5.symbol_select(self.symbol, True):
                    error_msg = f"Error al habilitar símbolo {self.symbol}"
                    logger.error(error_msg)
                    return {'success': False, 'error': error_msg}
            
            self.connected = True
            logger.info(f"✅ MT5 conectado - Cuenta: {self.login}")
            
            return {'success': True, 'message': 'Conectado exitosamente'}
            
        except Exception as e:
            logger.error(f"Error en conexión MT5: {e}")
            return {'success': False, 'error': str(e)}
    
    async def disconnect(self):
        """Desconectar de MT5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            logger.info("Desconectado de MT5")
    
    def is_connected(self) -> bool:
        """Verificar si está conectado"""
        return self.connected and mt5.terminal_info() is not None
    
    async def get_account_info(self) -> Dict:
        """Obtener información de la cuenta"""
        if not self.is_connected():
            return {}
        
        try:
            account_info = mt5.account_info()
            if account_info is None:
                return {}
            
            return {
                'balance': account_info.balance,
                'equity': account_info.equity,
                'margin': account_info.margin,
                'free_margin': account_info.margin_free,
                'margin_level': account_info.margin_level,
                'profit': account_info.profit,
                'currency': account_info.currency,
                'leverage': account_info.leverage,
                'server': account_info.server,
                'name': account_info.name
            }
        except Exception as e:
            logger.error(f"Error obteniendo info de cuenta: {e}")
            return {}
    
    async def get_symbol_info(self, symbol: str = None) -> Dict:
        """Obtener información del símbolo"""
        if not self.is_connected():
            return {}
        
        symbol = symbol or self.symbol
        
        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return {}
            
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return {}
            
            return {
                'symbol': symbol,
                'bid': tick.bid,
                'ask': tick.ask,
                'spread': tick.ask - tick.bid,
                'point': symbol_info.point,
                'digits': symbol_info.digits,
                'trade_contract_size': symbol_info.trade_contract_size,
                'volume_min': symbol_info.volume_min,
                'volume_max': symbol_info.volume_max,
                'volume_step': symbol_info.volume_step,
                'margin_initial': symbol_info.margin_initial,
                'time': datetime.fromtimestamp(tick.time)
            }
        except Exception as e:
            logger.error(f"Error obteniendo info del símbolo: {e}")
            return {}
    
    async def get_rates(self, symbol=None, count=100, timeframe=None):
        """Obtener datos históricos"""
        try:
            if not self.connected:
                await self.connect()
            
            # Usar símbolo proporcionado o el por defecto
            target_symbol = symbol if symbol is not None else self.symbol
            
            # Manejar timeframe como string o constante MT5
            if timeframe is None:
                timeframe = mt5.TIMEFRAME_M15
            elif isinstance(timeframe, str):
                # Mapear string a constante MT5
                timeframe_map = {
                    "M1": mt5.TIMEFRAME_M1,
                    "M5": mt5.TIMEFRAME_M5,
                    "M15": mt5.TIMEFRAME_M15,
                    "M30": mt5.TIMEFRAME_M30,
                    "H1": mt5.TIMEFRAME_H1,
                    "H4": mt5.TIMEFRAME_H4,
                    "D1": mt5.TIMEFRAME_D1
                }
                timeframe = timeframe_map.get(timeframe, mt5.TIMEFRAME_M15)
            
            rates = mt5.copy_rates_from_pos(target_symbol, timeframe, 0, count)
            
            if rates is None or len(rates) == 0:
                logger.error("No se pudieron obtener datos históricos")
                return pd.DataFrame()
            
            # Convertir a DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            # Renombrar columnas para consistencia
            df.columns = ['open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume']
            
            logger.info(f"Datos históricos obtenidos: {len(df)} períodos")
            return df
            
        except Exception as e:
            logger.error(f"Error obteniendo datos históricos: {e}")
            return pd.DataFrame()
    
    async def get_rates_timeframe(self, timeframe_str: str, count: int = 100, symbol: str = None):
        """Obtener datos históricos para un timeframe específico"""
        try:
            if not self.connected:
                await self.connect()
            
            # Usar símbolo proporcionado o el por defecto
            target_symbol = symbol if symbol is not None else self.symbol
            
            # Mapear string a constante MT5
            timeframe_map = {
                "M1": mt5.TIMEFRAME_M1,
                "M5": mt5.TIMEFRAME_M5,
                "M15": mt5.TIMEFRAME_M15,
                "M30": mt5.TIMEFRAME_M30,
                "H1": mt5.TIMEFRAME_H1,
                "H4": mt5.TIMEFRAME_H4,
                "D1": mt5.TIMEFRAME_D1
            }
            
            timeframe = timeframe_map.get(timeframe_str, mt5.TIMEFRAME_M15)
            
            rates = mt5.copy_rates_from_pos(target_symbol, timeframe, 0, count)
            
            if rates is None or len(rates) == 0:
                logger.warning(f"No se pudieron obtener datos para {timeframe_str}")
                return pd.DataFrame()
            
            # Convertir a DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            # Renombrar columnas para consistencia
            df.columns = ['open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume']
            
            logger.debug(f"Datos {timeframe_str} obtenidos: {len(df)} períodos")
            return df
            
        except Exception as e:
            logger.error(f"Error obteniendo datos {timeframe_str}: {e}")
            return pd.DataFrame()
    
    async def send_order(self, action: str, volume: float, symbol: str = None,
                        sl: float = None, tp: float = None, 
                        comment: str = "ForexBot") -> Dict:
        """Enviar orden de trading"""
        if not self.is_connected():
            return {'success': False, 'error': 'No conectado a MT5'}
        
        symbol = symbol or self.symbol
        
        try:
            # Obtener información del símbolo
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return {'success': False, 'error': f'Símbolo {symbol} no encontrado'}
            
            # Obtener precio actual
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return {'success': False, 'error': 'No se pudo obtener precio actual'}
            
            # Determinar tipo de orden y precio
            if action.upper() == 'BUY':
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask
            elif action.upper() == 'SELL':
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
            else:
                return {'success': False, 'error': 'Acción inválida. Use BUY o SELL'}
            
            # Preparar request sin especificar filling mode (usar default del broker)
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
            }
            
            # Agregar SL y TP si se especifican
            if sl is not None:
                request["sl"] = sl
            if tp is not None:
                request["tp"] = tp
            
            # Enviar orden
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {
                    'success': False, 
                    'error': f'Error en orden: {result.comment}',
                    'retcode': result.retcode
                }
            
            return {
                'success': True,
                'order': result.order,
                'deal': result.deal,
                'volume': result.volume,
                'price': result.price,
                'comment': result.comment
            }
            
        except Exception as e:
            logger.error(f"Error enviando orden: {e}")
            return {'success': False, 'error': str(e)}
    
    async def modify_position(self, ticket: int, sl: float = None, tp: float = None) -> bool:
        """Modificar stop loss y/o take profit de una posición"""
        try:
            if not self.is_connected():
                return False
            
            # Obtener información de la posición
            positions = mt5.positions_get(ticket=ticket)
            if not positions:
                logger.error(f"Posición {ticket} no encontrada")
                return False
            
            position = positions[0]
            
            # Preparar request de modificación
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": position.symbol,
                "position": ticket,
                "sl": sl if sl is not None else position.sl,
                "tp": tp if tp is not None else position.tp,
                "magic": 234000,
                "comment": "Modify SL/TP",
            }
            
            # Enviar orden de modificación
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"✅ Posición {ticket} modificada exitosamente")
                return True
            else:
                logger.error(f"❌ Error modificando posición {ticket}: {result.comment}")
                return False
                
        except Exception as e:
            logger.error(f"Error modificando posición: {e}")
            return False

    async def close_position(self, ticket: int) -> bool:
        """Cerrar posición por ticket"""
        try:
            if not self.is_connected():
                return False
            
            # Obtener información de la posición
            positions = mt5.positions_get(ticket=ticket)
            if not positions:
                logger.error(f"Posición {ticket} no encontrada")
                return False
            
            position = positions[0]
            
            # Determinar acción opuesta
            if position.type == mt5.POSITION_TYPE_BUY:
                action = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(position.symbol).bid
            else:
                action = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(position.symbol).ask
            
            # Preparar request de cierre
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": action,
                "position": ticket,
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": "Close position",
                "type_time": mt5.ORDER_TIME_GTC,
            }
            
            # Enviar orden de cierre
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"✅ Posición {ticket} cerrada exitosamente")
                return True
            else:
                logger.error(f"❌ Error cerrando posición {ticket}: {result.comment}")
                return False
                
        except Exception as e:
            logger.error(f"Error cerrando posición: {e}")
            return False

    async def get_positions(self, symbol: str = None) -> List[Dict]:
        """Obtener posiciones abiertas"""
        if not self.is_connected():
            return []
        
        try:
            if symbol:
                positions = mt5.positions_get(symbol=symbol)
            else:
                positions = mt5.positions_get()
            
            if positions is None:
                return []
            
            position_list = []
            for pos in positions:
                position_list.append({
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': 'BUY' if pos.type == mt5.ORDER_TYPE_BUY else 'SELL',
                    'volume': pos.volume,
                    'open_price': pos.price_open,
                    'current_price': pos.price_current,
                    'profit': pos.profit,
                    'swap': pos.swap,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'open_time': datetime.fromtimestamp(pos.time),
                    'comment': pos.comment
                })
            
            return position_list
            
        except Exception as e:
            logger.error(f"Error obteniendo posiciones: {e}")
            return []
    
    async def modify_position(self, ticket: int, new_sl: float = None, new_tp: float = None) -> Dict:
        """Modificar SL/TP de una posición existente"""
        if not self.is_connected():
            return {'success': False, 'error': 'No conectado a MT5'}
        
        try:
            # Obtener información de la posición
            positions = mt5.positions_get(ticket=ticket)
            if not positions:
                return {'success': False, 'error': 'Posición no encontrada'}
            
            position = positions[0]
            
            # Preparar request de modificación
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": position.symbol,
                "position": ticket,
                "sl": new_sl if new_sl is not None else position.sl,
                "tp": new_tp if new_tp is not None else position.tp,
                "magic": 234000,
                "comment": "ForexBot Trailing Stop",
            }
            
            # Enviar orden de modificación
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {
                    'success': False,
                    'error': f'Error modificando posición: {result.comment}',
                    'retcode': result.retcode
                }
            
            logger.info(f"Posición {ticket} modificada - SL: {new_sl}, TP: {new_tp}")
            return {
                'success': True,
                'ticket': ticket,
                'new_sl': new_sl,
                'new_tp': new_tp,
                'order': result.order
            }
            
        except Exception as e:
            logger.error(f"Error modificando posición {ticket}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def close_position(self, ticket: int) -> Dict:
        """Cerrar posición específica"""
        if not self.is_connected():
            return {'success': False, 'error': 'No conectado a MT5'}
        
        try:
            # Obtener información de la posición
            positions = mt5.positions_get(ticket=ticket)
            if not positions:
                return {'success': False, 'error': 'Posición no encontrada'}
            
            position = positions[0]
            
            # Determinar tipo de orden de cierre
            if position.type == mt5.ORDER_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(position.symbol).bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(position.symbol).ask
            
            # Preparar request de cierre
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": order_type,
                "position": ticket,
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": "ForexBot Close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Enviar orden de cierre
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {
                    'success': False,
                    'error': f'Error cerrando posición: {result.comment}',
                    'retcode': result.retcode
                }
            
            return {
                'success': True,
                'deal': result.deal,
                'volume': result.volume,
                'price': result.price
            }
            
        except Exception as e:
            logger.error(f"Error cerrando posición: {e}")
            return {'success': False, 'error': str(e)}
    
    async def close_all_positions(self, symbol: str = None) -> Dict:
        """Cerrar todas las posiciones"""
        if not self.is_connected():
            return {'success': False, 'error': 'No conectado a MT5'}
        
        try:
            positions = await self.get_positions(symbol)
            
            if not positions:
                return {'success': True, 'closed_count': 0, 'total_pl': 0.0}
            
            closed_count = 0
            total_pl = 0.0
            errors = []
            
            for position in positions:
                result = await self.close_position(position['ticket'])
                if result['success']:
                    closed_count += 1
                    total_pl += position['profit']
                else:
                    errors.append(f"Ticket {position['ticket']}: {result['error']}")
            
            if errors:
                return {
                    'success': False,
                    'closed_count': closed_count,
                    'total_pl': total_pl,
                    'errors': errors
                }
            
            return {
                'success': True,
                'closed_count': closed_count,
                'total_pl': total_pl
            }
            
        except Exception as e:
            logger.error(f"Error cerrando todas las posiciones: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_history_deals(self, days: int = 7) -> List[Dict]:
        """Obtener historial de operaciones"""
        if not self.is_connected():
            return []
        
        try:
            # Calcular fechas
            date_to = datetime.now()
            date_from = date_to - timedelta(days=days)
            
            # Obtener deals
            deals = mt5.history_deals_get(date_from, date_to)
            
            if deals is None:
                return []
            
            deal_list = []
            for deal in deals:
                try:
                    deal_list.append({
                        'deal': deal.ticket,  # Usar ticket en lugar de deal.deal
                        'order': deal.order,
                        'symbol': deal.symbol,
                        'type': 'BUY' if deal.type == mt5.ORDER_TYPE_BUY else 'SELL',
                        'volume': deal.volume,
                        'price': deal.price,
                        'profit': deal.profit,
                        'swap': deal.swap,
                        'commission': deal.commission,
                        'time': datetime.fromtimestamp(deal.time),
                        'comment': deal.comment
                    })
                except AttributeError as e:
                    # Si hay problemas con atributos, usar valores por defecto
                    logger.warning(f"Deal con atributos faltantes: {e}")
                    deal_list.append({
                        'deal': getattr(deal, 'ticket', 0),
                        'order': getattr(deal, 'order', 0),
                        'symbol': getattr(deal, 'symbol', self.symbol),
                        'type': 'BUY' if getattr(deal, 'type', 0) == mt5.ORDER_TYPE_BUY else 'SELL',
                        'volume': getattr(deal, 'volume', 0.0),
                        'price': getattr(deal, 'price', 0.0),
                        'profit': getattr(deal, 'profit', 0.0),
                        'swap': getattr(deal, 'swap', 0.0),
                        'commission': getattr(deal, 'commission', 0.0),
                        'time': datetime.fromtimestamp(getattr(deal, 'time', 0)),
                        'comment': getattr(deal, 'comment', '')
                    })
            
            return deal_list
            
        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")
            return []
    
    def calculate_lot_size(self, risk_percentage: float, stop_loss_pips: int, 
                          balance: float) -> float:
        """Calcular tamaño de lote basado en gestión de riesgo"""
        try:
            # Obtener información del símbolo
            symbol_info = mt5.symbol_info(self.symbol)
            if symbol_info is None:
                return 0.01  # Lote mínimo por defecto
            
            # Calcular valor del pip
            pip_value = symbol_info.trade_contract_size * symbol_info.point
            
            # Calcular riesgo en dinero
            risk_amount = balance * (risk_percentage / 100)
            
            # Calcular tamaño de lote
            lot_size = risk_amount / (stop_loss_pips * pip_value)
            
            # Ajustar a los límites del símbolo
            lot_size = max(symbol_info.volume_min, lot_size)
            lot_size = min(symbol_info.volume_max, lot_size)
            
            # Redondear al step del volumen
            steps = round(lot_size / symbol_info.volume_step)
            lot_size = steps * symbol_info.volume_step
            
            return round(lot_size, 2)
            
        except Exception as e:
            logger.error(f"Error calculando tamaño de lote: {e}")
            return 0.01

"""
Handlers para optimización y configuración
"""

import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv, set_key
from datetime import datetime

class OptimizationHandlers:
    def __init__(self, trading_engine):
        self.trading_engine = trading_engine
    
    async def show_optimize_menu(self, query):
        """Mostrar menú de optimización"""
        optimize_text = """
🎯 *Optimización de Configuración*

Selecciona el tipo de optimización que deseas aplicar:

🎯 **Demo Optimizada**: Configuración agresiva para cuentas demo
   • Riesgo: 2.5% por trade
   • Pérdida máxima: $150/día
   • Trades: Hasta 12/día

🛡️ **Conservadora**: Para cuentas reales pequeñas
   • Riesgo: 1.0% por trade
   • Pérdida máxima: $50/día
   • Trades: Hasta 5/día

🚀 **Agresiva**: Para cuentas grandes
   • Riesgo: 3.0% por trade
   • Pérdida máxima: $300/día
   • Trades: Hasta 15/día
        """
        
        keyboard = [
            [InlineKeyboardButton("🎯 Demo Optimizada", callback_data="opt_demo")],
            [InlineKeyboardButton("🛡️ Conservadora", callback_data="opt_conservative")],
            [InlineKeyboardButton("🚀 Agresiva", callback_data="opt_aggressive")],
            [InlineKeyboardButton("📊 Ver Config Actual", callback_data="opt_current")],
            [InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            optimize_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_optimization(self, query, data):
        """Manejar optimizaciones"""
        if data == "opt_demo":
            config = {
                'RISK_PERCENTAGE': '2.5',
                'MAX_DAILY_LOSS': '150.0',
                'TRADE_AMOUNT': '0.15',
                'STOP_LOSS_PIPS': '18',
                'TAKE_PROFIT_PIPS': '45'
            }
            config_name = "Demo Optimizada"
        elif data == "opt_conservative":
            config = {
                'RISK_PERCENTAGE': '1.0',
                'MAX_DAILY_LOSS': '50.0',
                'TRADE_AMOUNT': '0.05',
                'STOP_LOSS_PIPS': '25',
                'TAKE_PROFIT_PIPS': '35'
            }
            config_name = "Conservadora"
        elif data == "opt_aggressive":
            config = {
                'RISK_PERCENTAGE': '3.0',
                'MAX_DAILY_LOSS': '300.0',
                'TRADE_AMOUNT': '0.25',
                'STOP_LOSS_PIPS': '15',
                'TAKE_PROFIT_PIPS': '50'
            }
            config_name = "Agresiva"
        elif data == "opt_current":
            await self.show_current_config(query)
            return
        
        # Aplicar configuración
        env_file = '.env'
        for key, value in config.items():
            set_key(env_file, key, value)
        
        result_text = f"""
✅ *Configuración {config_name} Aplicada*

Los siguientes parámetros han sido actualizados:

"""
        for key, value in config.items():
            result_text += f"• {key}: {value}\n"
        
        result_text += """
⚠️ **Importante**: Los cambios se aplicarán en el próximo análisis de mercado.

Para aplicar completamente, puedes reiniciar el bot si lo deseas.
        """
        
        keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            result_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def show_current_config(self, query):
        """Mostrar configuración actual"""
        load_dotenv()
        
        config_text = f"""
📊 *Configuración Actual*

💰 **Gestión de Riesgo:**
• Riesgo por Trade: {os.getenv('RISK_PERCENTAGE', '2.0')}%
• Pérdida Máxima Diaria: ${os.getenv('MAX_DAILY_LOSS', '100.0')}
• Tamaño de Trade: {os.getenv('TRADE_AMOUNT', '0.1')} lotes

📊 **Stops:**
• Stop Loss: {os.getenv('STOP_LOSS_PIPS', '20')} pips
• Take Profit: {os.getenv('TAKE_PROFIT_PIPS', '40')} pips

🤖 **Bot:**
• Análisis: Cada 3 minutos
• Confianza Mínima: 75%
• Máx. Posiciones: 3 simultáneas
        """
        
        keyboard = [
            [InlineKeyboardButton("🎯 Optimizar", callback_data="optimize")],
            [InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            config_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def show_settings(self, query):
        """Mostrar configuración del bot"""
        settings = await self.trading_engine.get_settings()
        
        settings_text = f"""
⚙️ *Configuración del Bot*

💰 *Gestión de Riesgo:*
📊 Riesgo por Trade: {settings['risk_percentage']}%
💵 Cantidad por Trade: {settings['trade_amount']}
🛡️ Stop Loss: {settings['stop_loss_pips']} pips
🎯 Take Profit: {settings['take_profit_pips']} pips
⚠️ Pérdida Máxima Diaria: ${settings['max_daily_loss']}

📊 *Análisis Técnico:*
🕒 Timeframe: {settings['timeframe']}
📈 Indicadores: RSI, MACD, Bollinger Bands
⚡ Confianza Mínima: {settings['min_confidence']}%

🤖 *Automatización:*
🔄 Trading Automático: {'Activado' if settings['auto_trading'] else 'Desactivado'}
📱 Notificaciones: {'Activadas' if settings['notifications'] else 'Desactivadas'}
        """
        
        keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            settings_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

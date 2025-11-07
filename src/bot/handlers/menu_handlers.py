"""
Handlers para menús y navegación del bot
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime

class MenuHandlers:
    def __init__(self, trading_engine):
        self.trading_engine = trading_engine
    
    def get_main_keyboard(self, trading_active=False):
        """Obtener teclado del menú principal organizado"""
        # Sección 1: Información Financiera
        keyboard = [
            [
                InlineKeyboardButton("💰 Balance y Posiciones", callback_data="balance")
            ]
        ]
        
        # Sección 2: Trading Automático (dinámico según estado)
        if trading_active:
            keyboard.append([
                InlineKeyboardButton("🤖 Estado Trading Auto", callback_data="auto_trading_status"),
                InlineKeyboardButton("⏹️ Detener Trading", callback_data="stop_auto_trading")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("🚀 Iniciar Trading Auto", callback_data="start_auto_trading")
            ])
        
        # Sección 3: Análisis y Datos
        keyboard.extend([
            [
                InlineKeyboardButton("📊 Dashboard", callback_data="dashboard_main"),
                InlineKeyboardButton("📈 Análisis de Mercado", callback_data="analysis")
            ],
            [
                InlineKeyboardButton("📋 Historial de Trades", callback_data="history")
            ]
        ])
        
        # Sección 4: Configuración y Herramientas
        keyboard.extend([
            [
                InlineKeyboardButton("⚙️ Configuración", callback_data="settings"),
                InlineKeyboardButton("🧪 Test Conexiones", callback_data="test_connections")
            ],
            [
                InlineKeyboardButton("🆘 Cerrar Todas las Posiciones", callback_data="close_all")
            ]
        ])
        
        return keyboard
    
    def get_trading_animation(self):
        """Obtener mensaje de animación aleatoria para trading activo"""
        import random
        
        animations = [
            "🔍 *Analizando EUR/USD, GBP/USD, USD/JPY...* ⚡",
            "📊 *Evaluando señales de trading...* 🎯",
            "💰 *Buscando oportunidades rentables...* 🚀",
            "⚡ *Procesando datos de mercado...* 📈",
            "🎯 *Calculando probabilidades de éxito...* 🧠",
            "🔥 *Escaneando 5 pares simultáneamente...* 💎",
            "🚀 *Detectando patrones de precio...* 📊",
            "💎 *Analizando volatilidad del mercado...* ⚡",
            "🧠 *Aplicando estrategias avanzadas...* 🎯",
            "📈 *Monitoreando momentum del mercado...* 🔍"
        ]
        
        return random.choice(animations)
    
    async def show_main_menu(self, query):
        """Mostrar menú principal inteligente y dinámico"""
        # Verificar si el trading automático está activo
        trading_active = False
        trading_status = "🔴 Inactivo"
        activity_message = ""
        
        try:
            # Usar la referencia directa al ultimate_machine
            if hasattr(self, 'ultimate_machine') and self.ultimate_machine:
                if self.ultimate_machine.running:
                    trading_active = True
                    trading_status = "🟢 Activo"
                    # Obtener animación aleatoria
                    animation = self.get_trading_animation()
                    activity_message = f"\n{animation}\n💡 *El bot está trabajando en segundo plano*"
        except:
            pass
        
        # Crear teclado dinámico según el estado
        keyboard = self.get_main_keyboard(trading_active)
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Mensaje dinámico según el estado
        if trading_active:
            main_text = f"""
🤖 *Ultimate Money Machine - TRABAJANDO*

🟢 *Estado:* Operativo y Generando Dinero
💱 *Mercados:* EUR/USD, GBP/USD, USD/JPY, AUD/USD, USD/CAD
🤖 *Trading Automático:* {trading_status}

{activity_message}

⚡ *Configuración Activa:*
• Análisis cada 15 segundos
• Confianza mínima: 75%
• Máximo 5 posiciones simultáneas
• Riesgo: 2-5% por trade

🎮 *Control desde aquí o deja que trabaje solo:*
            """
        else:
            main_text = f"""
🤖 *Ultimate Money Machine - LISTA*

📊 *Estado del Sistema:* Conectado y Listo
💱 *Mercados Disponibles:* 5 pares principales
🎯 *Objetivo:* Generar ganancias consistentes
🤖 *Trading Automático:* {trading_status}

💡 *¿Listo para generar dinero?*
Presiona "🚀 Iniciar Trading Auto" para comenzar

⚙️ *Configuración Optimizada:*
• Análisis inteligente multi-timeframe
• Estrategias probadas y rentables
• Gestión de riesgo avanzada
• Control total desde Telegram

Selecciona una opción del menú:
            """
        
        await query.edit_message_text(
            main_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def show_welcome_message(self, update):
        """Mostrar mensaje de bienvenida inteligente"""
        # Por defecto, el trading no está activo al iniciar
        keyboard = self.get_main_keyboard(trading_active=False)
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = """
🚀 *¡Bienvenido a Ultimate Money Machine!*

🤖 *Tu Bot de Trading Automático Avanzado*

✅ *Sistema Inicializado Correctamente*
🔗 *Conectado a MetaTrader 5*
💰 *Listo para Generar Ganancias*

🎯 *Capacidades del Bot:*
• Trading automático en 5 pares principales
• Análisis inteligente multi-timeframe
• Estrategias probadas y rentables
• Gestión de riesgo avanzada
• Control total desde Telegram

💡 *Para comenzar a generar dinero:*
Presiona "🚀 Iniciar Trading Auto"

🎮 *Control Total:*
Puedes iniciar, detener y monitorear el trading desde aquí

Selecciona una opción del menú:
        """
        
        await update.message.reply_text(
            welcome_text, 
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

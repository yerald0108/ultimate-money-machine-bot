# 🤖 Forex Trading Bot EUR/USD

Bot de trading automatizado para Telegram con integración MetaTrader 5, especializado en el par EUR/USD.

## 🚀 Características

- **Trading Automatizado 24/5**: Opera automáticamente basado en análisis técnico
- **Análisis Técnico Avanzado**: RSI, MACD, Bollinger Bands, Stochastic, Williams %R, ADX
- **Gestión de Riesgo Integrada**: Stop Loss automático, límites de pérdida diaria
- **Interfaz Telegram**: Control completo desde Telegram con navegación por botones
- **Conexión MT5**: Integración directa con MetaTrader 5
- **Monitoreo en Tiempo Real**: Análisis continuo cada 5 minutos

## 📊 Indicadores Técnicos

- **RSI (14)**: Identificación de sobrecompra/sobreventa
- **MACD**: Cruces de señal para tendencias
- **Bollinger Bands**: Niveles de soporte y resistencia dinámicos
- **Stochastic**: Confirmación de señales de entrada
- **Williams %R**: Indicador de momentum
- **ADX**: Fuerza de tendencia
- **SMA/EMA**: Medias móviles para análisis de tendencia

## ⚙️ Configuración

### 1. Configurar Variables de Entorno

Edita el archivo `.env` con tus credenciales:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=tu_token_de_bot_aqui
TELEGRAM_CHAT_ID=tu_chat_id_aqui

# MT5 Configuration
MT5_LOGIN=tu_login_mt5
MT5_PASSWORD=tu_password_mt5
MT5_SERVER=tu_servidor_mt5

# Trading Configuration
RISK_PERCENTAGE=2.0
MAX_DAILY_LOSS=100.0
TRADE_AMOUNT=0.1
STOP_LOSS_PIPS=20
TAKE_PROFIT_PIPS=40
```

### 2. Crear Bot de Telegram

1. Habla con [@BotFather](https://t.me/botfather) en Telegram
2. Crea un nuevo bot con `/newbot`
3. Copia el token y ponlo en `TELEGRAM_BOT_TOKEN`
4. Para obtener tu CHAT_ID, envía un mensaje a tu bot y visita:
   `https://api.telegram.org/bot<TU_TOKEN>/getUpdates`

### 3. Configurar MT5

1. Abre una cuenta demo en tu broker MT5
2. Anota las credenciales de login, password y servidor
3. Asegúrate de que MT5 esté instalado en tu sistema

## 🚀 Instalación y Uso

### 1. Activar Entorno Virtual

```bash
# Windows
.\forex_bot_env\Scripts\Activate.ps1

# Linux/Mac
source forex_bot_env/bin/activate
```

### 2. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 3. Ejecutar el Bot

```bash
python main.py
```

## 📱 Comandos del Bot

### Menú Principal

- **📊 Estado del Bot**: Ver estado actual y estadísticas
- **💰 Balance**: Información de la cuenta y balance
- **📈 Análisis EUR/USD**: Análisis técnico en tiempo real
- **🔍 Posiciones Abiertas**: Ver trades activos
- **▶️ Iniciar Trading**: Activar trading automático
- **⏸️ Pausar Trading**: Pausar operaciones automáticas
- **⚙️ Configuración**: Ver configuración actual
- **📋 Historial**: Historial de trades recientes
- **🆘 Cerrar Todo**: Cerrar todas las posiciones (emergencia)
- **ℹ️ Ayuda**: Información y ayuda

## 🛡️ Gestión de Riesgo

### Características de Seguridad

- **Stop Loss Automático**: Todas las operaciones tienen SL
- **Límite de Riesgo por Trade**: Máximo 2% del balance por defecto
- **Límite de Pérdida Diaria**: Máximo $100 por día por defecto
- **Límite de Trades Diarios**: Máximo 10 trades por día
- **Análisis de Confianza**: Solo opera con señales de alta confianza (>70%)

### Cálculo Automático de Lotes

El bot calcula automáticamente el tamaño de lote basado en:
- Porcentaje de riesgo configurado
- Balance actual de la cuenta
- Stop Loss en pips
- Límites del símbolo

## 📊 Estrategia de Trading

### Generación de Señales

El bot genera señales BUY/SELL basado en:

1. **Análisis Multi-Indicador**: Consenso entre múltiples indicadores
2. **Filtro de Tendencia**: Solo opera a favor de la tendencia principal
3. **Niveles de Confianza**: Requiere mínimo 70% de confianza
4. **Confirmación Cruzada**: Múltiples señales deben coincidir

### Criterios de Entrada

**Señal BUY**:
- RSI < 30 (sobreventa)
- MACD cruce alcista
- Precio en banda inferior de Bollinger
- Stochastic < 20 con cruce alcista
- Tendencia general alcista

**Señal SELL**:
- RSI > 70 (sobrecompra)
- MACD cruce bajista
- Precio en banda superior de Bollinger
- Stochastic > 80 con cruce bajista
- Tendencia general bajista

## 📁 Estructura del Proyecto

```
Bot-Trading/
├── main.py                 # Archivo principal
├── requirements.txt        # Dependencias
├── .env                   # Variables de entorno
├── README.md              # Este archivo
├── src/
│   ├── bot/
│   │   ├── __init__.py
│   │   └── telegram_bot.py    # Bot de Telegram
│   ├── trading/
│   │   ├── __init__.py
│   │   ├── mt5_connector.py   # Conexión MT5
│   │   └── trading_engine.py  # Motor de trading
│   ├── analysis/
│   │   ├── __init__.py
│   │   └── market_analyzer.py # Análisis técnico
│   └── utils/
│       └── __init__.py
├── data/                  # Datos del mercado
├── logs/                  # Archivos de log
└── forex_bot_env/        # Entorno virtual
```

## 🔧 Configuración Avanzada

### Parámetros de Trading

- `RISK_PERCENTAGE`: Porcentaje de riesgo por trade (1-5%)
- `MAX_DAILY_LOSS`: Pérdida máxima diaria en USD
- `TRADE_AMOUNT`: Tamaño fijo de lote (si es menor que el calculado)
- `STOP_LOSS_PIPS`: Stop Loss en pips
- `TAKE_PROFIT_PIPS`: Take Profit en pips

### Parámetros de Análisis

- Timeframe: 15 minutos (configurable en código)
- Períodos de análisis: 200 velas
- Confianza mínima: 70%
- Intervalo de análisis: 5 minutos

## 📊 Monitoreo y Logs

### Archivos de Log

- `logs/bot.log`: Log principal del bot
- Logs en consola con timestamps
- Información detallada de cada trade

### Métricas Monitoreadas

- Número de señales detectadas
- Trades ejecutados por día
- Ratio de trades ganadores/perdedores
- P&L diario y acumulado
- Estado de conexión MT5

## ⚠️ Advertencias Importantes

1. **Siempre usar cuenta demo primero**
2. **El trading conlleva riesgos de pérdida**
3. **Nunca invertir más de lo que puedes permitirte perder**
4. **Monitorear regularmente el rendimiento**
5. **Mantener MT5 abierto y conectado**
6. **Verificar conexión a internet estable**

## 🆘 Solución de Problemas

### Error de Conexión MT5

1. Verificar que MT5 esté abierto
2. Comprobar credenciales en `.env`
3. Verificar conexión a internet
4. Reiniciar MT5 si es necesario

### Bot no responde en Telegram

1. Verificar token del bot
2. Comprobar que el bot esté iniciado (`/start`)
3. Verificar conexión a internet
4. Revisar logs para errores

### No se ejecutan trades

1. Verificar que el trading esté activado
2. Comprobar límites diarios
3. Verificar confianza de señales
4. Revisar balance de la cuenta

## 📞 Soporte

Para soporte técnico o preguntas:
- Revisar logs en `logs/bot.log`
- Verificar configuración en `.env`
- Comprobar estado en el menú del bot

## 📄 Licencia

Este proyecto es para uso personal y educativo. El trading automatizado conlleva riesgos financieros significativos.

---

**⚠️ DISCLAIMER**: Este bot es una herramienta de trading automatizado. El trading de Forex conlleva un alto riesgo de pérdida financiera. Nunca inviertas dinero que no puedas permitirte perder. Siempre prueba con cuentas demo antes de usar dinero real.

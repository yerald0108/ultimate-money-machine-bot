# 🚀 INSTRUCCIONES DE CONFIGURACIÓN E INICIO

## 📋 Pasos para Configurar el Bot

### 1. ✅ Verificar Instalación

El bot ya está instalado con todas las dependencias. Estructura creada:

```
Bot-Trading/
├── 📄 main.py              # Archivo principal
├── 📄 .env                 # Configuración (EDITAR ESTE ARCHIVO)
├── 📄 .env.example         # Ejemplo de configuración
├── 📄 requirements.txt     # Dependencias instaladas ✅
├── 📄 setup.py            # Script de verificación
├── 📄 test_connection.py  # Script de pruebas
├── 📄 start_bot.bat       # Iniciador automático
├── 📁 src/                # Código fuente del bot
├── 📁 logs/               # Archivos de log
├── 📁 data/               # Datos del mercado
└── 📁 forex_bot_env/      # Entorno virtual ✅
```

### 2. 🤖 Crear Bot de Telegram

1. **Abrir Telegram** y buscar `@BotFather`
2. **Enviar** `/newbot`
3. **Seguir instrucciones**:
   - Nombre del bot: `Mi Forex Bot`
   - Username: `mi_forex_bot` (debe terminar en 'bot')
4. **Copiar el TOKEN** que te da BotFather

### 3. 🆔 Obtener Chat ID

1. **Enviar** `/start` a tu bot recién creado
2. **Abrir navegador** y visitar:
   ```
   https://api.telegram.org/bot<TU_TOKEN>/getUpdates
   ```
   (Reemplaza `<TU_TOKEN>` con el token de tu bot)
3. **Buscar** en el JSON: `"chat":{"id":123456789`
4. **Copiar** ese número (tu Chat ID)

### 4. 🏦 Configurar Cuenta MT5 Demo

1. **Descargar MT5** desde el sitio de tu broker preferido
2. **Abrir cuenta DEMO** (¡NUNCA uses cuenta real al principio!)
3. **Anotar credenciales**:
   - Login (número de cuenta)
   - Password
   - Server (nombre del servidor)

### 5. ⚙️ Editar Archivo .env

**Abrir** el archivo `.env` y reemplazar:

```env
# TELEGRAM
TELEGRAM_BOT_TOKEN=TU_TOKEN_AQUI
TELEGRAM_CHAT_ID=TU_CHAT_ID_AQUI

# MT5 (CUENTA DEMO)
MT5_LOGIN=12345678
MT5_PASSWORD=tu_password
MT5_SERVER=Demo-Server-Name

# CONFIGURACIÓN DE RIESGO (CONSERVADORA)
RISK_PERCENTAGE=1.0
MAX_DAILY_LOSS=50.0
TRADE_AMOUNT=0.01
STOP_LOSS_PIPS=20
TAKE_PROFIT_PIPS=40
```

## 🧪 Verificar Configuración

### Opción 1: Script Automático
```bash
python setup.py
```

### Opción 2: Pruebas Completas
```bash
python test_connection.py
```

### Opción 3: Iniciador Automático (Windows)
```bash
start_bot.bat
```

## 🚀 Iniciar el Bot

### Método 1: Comando Directo
```bash
# Activar entorno virtual
forex_bot_env\Scripts\activate

# Iniciar bot
python main.py
```

### Método 2: Script Automático
```bash
start_bot.bat
```

## 📱 Usar el Bot

1. **Abrir Telegram** y buscar tu bot
2. **Enviar** `/start`
3. **Usar el menú** con botones:
   - 📊 **Estado del Bot**: Ver estadísticas
   - 💰 **Balance**: Info de cuenta
   - 📈 **Análisis EUR/USD**: Análisis técnico
   - ▶️ **Iniciar Trading**: Activar bot
   - ⏸️ **Pausar Trading**: Pausar operaciones

## ⚠️ CONFIGURACIÓN DE SEGURIDAD

### 🛡️ Configuración Inicial Recomendada

```env
RISK_PERCENTAGE=1.0          # Solo 1% de riesgo por trade
MAX_DAILY_LOSS=50.0         # Máximo $50 de pérdida por día
TRADE_AMOUNT=0.01           # Lotes muy pequeños
STOP_LOSS_PIPS=20           # Stop loss de 20 pips
TAKE_PROFIT_PIPS=40         # Take profit de 40 pips
```

### 📊 Incrementar Gradualmente

Solo después de **al menos 1 semana** de pruebas exitosas:

```env
RISK_PERCENTAGE=2.0          # Incrementar a 2%
MAX_DAILY_LOSS=100.0        # Incrementar límite
TRADE_AMOUNT=0.1            # Lotes más grandes
```

## 🔧 Solución de Problemas

### ❌ Error: "No conectado a MT5"
- Verificar que MT5 esté abierto
- Comprobar credenciales en `.env`
- Verificar conexión a internet

### ❌ Error: "Token inválido"
- Verificar token en `.env`
- Asegurarse de que no hay espacios extra

### ❌ Error: "Símbolo no encontrado"
- Verificar que EURUSD esté disponible en tu broker
- Algunos brokers usan "EURUSDm" o "EURUSD.m"

### ❌ Bot no responde
- Enviar `/start` al bot
- Verificar que el bot esté ejecutándose
- Revisar logs en `logs/bot.log`

## 📊 Monitoreo

### 📈 Métricas Importantes
- **Win Rate**: % de trades ganadores
- **Profit Factor**: Ganancias/Pérdidas
- **Drawdown**: Pérdida máxima
- **Trades por día**: Frecuencia de operaciones

### 📋 Logs
- **Archivo**: `logs/bot.log`
- **Consola**: Información en tiempo real
- **Telegram**: Notificaciones del bot

## 🎯 Objetivos Realistas

### 📅 Primera Semana
- ✅ Bot funcionando sin errores
- ✅ Conexiones estables
- ✅ Máximo 5-10 trades
- 🎯 Objetivo: No perder dinero

### 📅 Primer Mes
- ✅ Win rate > 50%
- ✅ Profit factor > 1.2
- ✅ Drawdown < 10%
- 🎯 Objetivo: Pequeñas ganancias consistentes

### 📅 Después de 3 Meses
- ✅ Sistema optimizado
- ✅ Configuración ajustada
- ✅ Resultados consistentes
- 🎯 Objetivo: Considerar cuenta real (con mucho cuidado)

## 🆘 Controles de Emergencia

### ⏸️ Pausar Trading
- Botón "Pausar Trading" en Telegram
- Detiene nuevas operaciones
- Mantiene posiciones abiertas

### 🆘 Cerrar Todo
- Botón "Cerrar Todo" en Telegram
- Cierra todas las posiciones inmediatamente
- Usar solo en emergencias

### 🔴 Detener Completamente
- `Ctrl+C` en la consola
- Cierra el bot completamente

## 🚀 **Pasos Simplificados - Todo Integrado en Telegram**

1. **Configurar credenciales** en el archivo `.env` ✅
2. **Crear bot de Telegram** con @BotFather ✅
3. **Abrir cuenta demo MT5** ✅
4. **Iniciar el bot**: `python main.py` ✅
5. **¡Todo lo demás desde Telegram!** 🎉

### 📱 **Nuevas Funciones Integradas en el Bot:**

- **🧪 Test Conexiones**: Verificar MT5, Telegram y análisis
- **🎯 Optimizar Config**: Cambiar configuración (Demo/Conservadora/Agresiva)
- **📊 Monitor Rendimiento**: Ver métricas en tiempo real
- **⚙️ Configuración**: Ver parámetros actuales

**¡Ya no necesitas scripts separados! Todo está en el bot de Telegram.**

## 📞 Soporte

Si tienes problemas:

1. **Revisar logs**: `logs/bot.log`
2. **Ejecutar pruebas**: `python test_connection.py`
3. **Verificar configuración**: `python setup.py`
4. **Consultar README.md**: Documentación completa

---

## ⚠️ RECORDATORIOS IMPORTANTES

- 🔴 **SIEMPRE usar cuenta demo primero**
- 🔴 **NUNCA invertir más de lo que puedes perder**
- 🔴 **El trading conlleva riesgos**
- 🔴 **Monitorear regularmente el bot**
- 🔴 **Mantener configuración conservadora**

¡Buena suerte con tu bot de trading! 🚀📈

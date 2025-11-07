# 🚀 Guía de Despliegue - Ultimate Money Machine Bot

## 📋 Requisitos Previos

### 1. **Crear Bot de Telegram**
1. Habla con [@BotFather](https://t.me/botfather) en Telegram
2. Usa el comando `/newbot`
3. Elige un nombre y username para tu bot
4. **Guarda el TOKEN** que te da BotFather

### 2. **Cuenta de MetaTrader 5**
- Login de tu cuenta MT5
- Contraseña de tu cuenta MT5
- Servidor (ej: MetaQuotes-Demo)

## 🚀 OPCIÓN 1: Railway (RECOMENDADO)

### **Ventajas:**
- ✅ 500 horas gratis/mes
- ✅ Perfecto para bots 24/7
- ✅ Fácil configuración
- ✅ Variables de entorno seguras

### **Pasos:**

#### **1. Crear cuenta en Railway**
- Ve a [railway.app](https://railway.app)
- Regístrate con GitHub

#### **2. Subir código a GitHub**
```bash
git init
git add .
git commit -m "Initial commit - Ultimate Money Machine Bot"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/bot-trading.git
git push -u origin main
```

#### **3. Desplegar en Railway**
1. En Railway: "New Project" → "Deploy from GitHub repo"
2. Selecciona tu repositorio
3. Railway detectará automáticamente Python

#### **4. Configurar Variables de Entorno**
En Railway → Settings → Variables:
```
TELEGRAM_BOT_TOKEN=tu_token_aqui
MT5_LOGIN=tu_login_mt5
MT5_PASSWORD=tu_password_mt5
MT5_SERVER=MetaQuotes-Demo
TRADING_ENABLED=true
MAX_RISK_PERCENTAGE=0.05
MAX_SIMULTANEOUS_POSITIONS=5
MIN_CONFIDENCE=75
LOG_LEVEL=INFO
```

#### **5. Desplegar**
- Railway desplegará automáticamente
- El bot estará disponible 24/7

---

## 🚀 OPCIÓN 2: Render

### **Ventajas:**
- ✅ 750 horas gratis/mes
- ✅ SSL automático
- ✅ Fácil configuración

### **Pasos:**

#### **1. Crear cuenta en Render**
- Ve a [render.com](https://render.com)
- Regístrate con GitHub

#### **2. Crear Web Service**
1. "New" → "Web Service"
2. Conecta tu repositorio GitHub
3. Configuración:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`

#### **3. Variables de Entorno**
Igual que Railway, agregar todas las variables.

---

## 🚀 OPCIÓN 3: Heroku

### **Limitaciones:**
- ⚠️ Solo 550 horas gratis/mes
- ⚠️ Se duerme después de 30 min inactivo

### **Pasos:**

#### **1. Instalar Heroku CLI**
- Descargar de [heroku.com](https://heroku.com)

#### **2. Desplegar**
```bash
heroku login
heroku create tu-bot-trading
git push heroku main
```

#### **3. Configurar Variables**
```bash
heroku config:set TELEGRAM_BOT_TOKEN=tu_token
heroku config:set MT5_LOGIN=tu_login
heroku config:set MT5_PASSWORD=tu_password
# ... resto de variables
```

---

## 🔧 Configuración Adicional

### **Variables de Entorno Completas:**
```
# OBLIGATORIAS
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
MT5_LOGIN=12345678
MT5_PASSWORD=tu_password
MT5_SERVER=MetaQuotes-Demo

# OPCIONALES
TRADING_ENABLED=true
MAX_RISK_PERCENTAGE=0.05
MAX_SIMULTANEOUS_POSITIONS=5
MIN_CONFIDENCE=75
LOG_LEVEL=INFO
```

### **Archivos Importantes:**
- `requirements.txt` - Dependencias Python
- `Procfile` - Comando de inicio
- `runtime.txt` - Versión de Python
- `railway.json` - Configuración Railway

## ✅ Verificación

### **1. Comprobar que el bot funciona:**
1. Busca tu bot en Telegram
2. Envía `/start`
3. Deberías ver el menú principal

### **2. Logs del servidor:**
- **Railway:** Dashboard → Logs
- **Render:** Dashboard → Logs
- **Heroku:** `heroku logs --tail`

## 🛡️ Seguridad

### **NUNCA subas a GitHub:**
- ❌ Archivos `.env` con tokens reales
- ❌ Credenciales de MT5
- ❌ Tokens de Telegram

### **✅ Usa siempre:**
- Variables de entorno del servidor
- Archivos `.env.example` sin datos reales
- `.gitignore` para excluir archivos sensibles

## 🆘 Solución de Problemas

### **Bot no responde:**
1. Verificar variables de entorno
2. Revisar logs del servidor
3. Comprobar que MT5 esté disponible

### **Errores de conexión MT5:**
- Verificar credenciales
- Comprobar que el servidor MT5 esté activo
- Revisar que la cuenta permita trading automático

### **Bot se desconecta:**
- **Railway/Render:** Debería mantenerse activo
- **Heroku:** Necesita tráfico cada 30 min o plan pago

## 💡 Recomendaciones

### **Para Producción:**
1. **Usa Railway** - Mejor para bots 24/7
2. **Monitorea logs** regularmente
3. **Haz backups** de configuración
4. **Prueba primero** en cuenta demo
5. **Configura alertas** de errores

### **Optimización:**
- Ajusta `MIN_CONFIDENCE` según resultados
- Monitorea `MAX_RISK_PERCENTAGE`
- Revisa logs de trading diariamente

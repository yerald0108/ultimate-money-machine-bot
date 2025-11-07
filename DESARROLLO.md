# 🔄 Desarrollo con Recarga Automática

## 🚀 Inicio Rápido

### Opción 1: Script Batch (Recomendado)
```bash
# Doble clic en el archivo o ejecutar en terminal
dev.bat
```

### Opción 2: Script Watchdog (Más Confiable)
```bash
python dev_watch.py
```

### Opción 3: Script Hupper (Alternativo)
```bash
python dev.py
```

### Opción 4: Comando directo con hupper
```bash
hupper -m main
```

## ⚠️ Problema con Hupper Solucionado

Si `hupper -m main` no responde, usa las alternativas:
- **dev.bat** (Recomendado)
- **python dev_watch.py** (Más estable)
- **python dev.py** (Con fallback)

## 📝 Características

### ✅ Recarga Automática
- **Archivos monitoreados**: `main.py`, `src/`, `.env`
- **Recarga instantánea**: Al guardar cualquier archivo Python
- **Sin pérdida de estado**: Reinicio limpio del bot

### 🎯 Beneficios
- **No más reinicio manual**: Los cambios se aplican automáticamente
- **Desarrollo más rápido**: Prueba cambios instantáneamente
- **Menos errores**: No olvidas reiniciar el bot

## 🛠️ Comandos Disponibles

### Desarrollo (con recarga automática)
```bash
python dev.py          # Recarga automática
dev.bat               # Versión Windows
```

### Producción (sin recarga)
```bash
python main.py --no-reload    # Sin recarga automática
python main.py               # Con recarga automática (por defecto)
```

## 📊 Logs de Desarrollo

Cuando uses la recarga automática verás:
```
🔄 Bot iniciado con recarga automática
📝 Los cambios en el código recargarán automáticamente el bot
⏹️  Presiona Ctrl+C para detener

2025-11-05 13:25:12 - INFO - Bot listo | Capacidades: Multi-Timeframe, Machine Learning
[Cambio detectado en src/bot/handlers/trading_handlers.py]
🔄 Recargando bot...
2025-11-05 13:25:45 - INFO - Bot reiniciado automáticamente
```

## 🎉 ¡Desarrollo Mejorado!

Ahora puedes:
1. **Editar código** en cualquier archivo
2. **Guardar** el archivo (Ctrl+S)
3. **Ver cambios** automáticamente sin reiniciar
4. **Probar** inmediatamente en Telegram

## ⚠️ Notas Importantes

- **MT5**: La conexión se mantiene estable durante recargas
- **Telegram**: El bot se reconecta automáticamente
- **Estado**: Se reinicia limpio en cada recarga
- **Logs**: Continúan en la misma sesión

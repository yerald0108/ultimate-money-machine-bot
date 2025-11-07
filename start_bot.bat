@echo off
echo ================================
echo   Forex Trading Bot EUR/USD
echo ================================
echo.

REM Activar entorno virtual
call forex_bot_env\Scripts\activate.bat

REM Verificar configuración
echo Verificando configuración...
python setup.py

echo.
echo ¿Deseas iniciar el bot? (S/N)
set /p choice=

if /i "%choice%"=="S" (
    echo.
    echo Iniciando bot...
    python main.py
) else (
    echo Bot no iniciado.
)

pause

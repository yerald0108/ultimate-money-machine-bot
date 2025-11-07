#!/usr/bin/env python3
"""
Monitor de Rendimiento en Tiempo Real
Muestra métricas de performance y rentabilidad del bot
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.trading.mt5_connector import MT5Connector

class PerformanceMonitor:
    def __init__(self):
        self.mt5 = MT5Connector()
        
    async def connect(self):
        """Conectar a MT5"""
        return await self.mt5.connect()
    
    async def get_daily_performance(self):
        """Obtener rendimiento diario"""
        try:
            # Obtener deals del día
            deals = await self.mt5.get_history_deals(days=1)
            
            if not deals:
                return {
                    'total_trades': 0,
                    'profit': 0.0,
                    'win_rate': 0.0,
                    'avg_profit': 0.0,
                    'best_trade': 0.0,
                    'worst_trade': 0.0
                }
            
            # Filtrar solo deals de hoy
            today = datetime.now().date()
            today_deals = [deal for deal in deals if deal['time'].date() == today]
            
            if not today_deals:
                return {
                    'total_trades': 0,
                    'profit': 0.0,
                    'win_rate': 0.0,
                    'avg_profit': 0.0,
                    'best_trade': 0.0,
                    'worst_trade': 0.0
                }
            
            # Calcular métricas
            total_trades = len(today_deals)
            total_profit = sum(deal['profit'] for deal in today_deals)
            winning_trades = len([deal for deal in today_deals if deal['profit'] > 0])
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            avg_profit = total_profit / total_trades if total_trades > 0 else 0
            
            profits = [deal['profit'] for deal in today_deals]
            best_trade = max(profits) if profits else 0
            worst_trade = min(profits) if profits else 0
            
            return {
                'total_trades': total_trades,
                'profit': total_profit,
                'win_rate': win_rate,
                'avg_profit': avg_profit,
                'best_trade': best_trade,
                'worst_trade': worst_trade,
                'winning_trades': winning_trades,
                'losing_trades': total_trades - winning_trades
            }
            
        except Exception as e:
            print(f"Error obteniendo rendimiento diario: {e}")
            return {}
    
    async def get_weekly_performance(self):
        """Obtener rendimiento semanal"""
        try:
            deals = await self.mt5.get_history_deals(days=7)
            
            if not deals:
                return {}
            
            # Agrupar por día
            daily_profits = {}
            for deal in deals:
                day = deal['time'].date()
                if day not in daily_profits:
                    daily_profits[day] = 0
                daily_profits[day] += deal['profit']
            
            # Calcular métricas semanales
            total_profit = sum(daily_profits.values())
            profitable_days = len([profit for profit in daily_profits.values() if profit > 0])
            total_days = len(daily_profits)
            
            return {
                'total_profit': total_profit,
                'profitable_days': profitable_days,
                'total_days': total_days,
                'daily_profits': daily_profits,
                'avg_daily_profit': total_profit / total_days if total_days > 0 else 0
            }
            
        except Exception as e:
            print(f"Error obteniendo rendimiento semanal: {e}")
            return {}
    
    async def get_account_status(self):
        """Obtener estado de la cuenta"""
        try:
            account_info = await self.mt5.get_account_info()
            positions = await self.mt5.get_positions()
            
            return {
                'balance': account_info.get('balance', 0),
                'equity': account_info.get('equity', 0),
                'margin': account_info.get('margin', 0),
                'free_margin': account_info.get('free_margin', 0),
                'margin_level': account_info.get('margin_level', 0),
                'open_positions': len(positions),
                'floating_pl': sum(pos.get('profit', 0) for pos in positions)
            }
            
        except Exception as e:
            print(f"Error obteniendo estado de cuenta: {e}")
            return {}
    
    def display_performance(self, daily_perf, weekly_perf, account_status):
        """Mostrar rendimiento en consola"""
        
        # Limpiar pantalla
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("🤖 FOREX TRADING BOT - MONITOR DE RENDIMIENTO")
        print("=" * 60)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Estado de cuenta
        print("💰 ESTADO DE CUENTA")
        print("-" * 30)
        if account_status:
            print(f"Balance:      ${account_status['balance']:,.2f}")
            print(f"Equity:       ${account_status['equity']:,.2f}")
            print(f"Margen Libre: ${account_status['free_margin']:,.2f}")
            print(f"Nivel Margen: {account_status['margin_level']:.1f}%")
            print(f"Posiciones:   {account_status['open_positions']}")
            
            if account_status['floating_pl'] != 0:
                pl_emoji = "📈" if account_status['floating_pl'] > 0 else "📉"
                print(f"P&L Flotante: {pl_emoji} ${account_status['floating_pl']:,.2f}")
        print()
        
        # Rendimiento diario
        print("📊 RENDIMIENTO HOY")
        print("-" * 30)
        if daily_perf and daily_perf['total_trades'] > 0:
            profit_emoji = "💚" if daily_perf['profit'] > 0 else "❌" if daily_perf['profit'] < 0 else "⚪"
            
            print(f"Trades:       {daily_perf['total_trades']}")
            print(f"Ganadores:    {daily_perf['winning_trades']} ({daily_perf['win_rate']:.1f}%)")
            print(f"Perdedores:   {daily_perf['losing_trades']}")
            print(f"Profit Total: {profit_emoji} ${daily_perf['profit']:,.2f}")
            print(f"Profit Prom:  ${daily_perf['avg_profit']:,.2f}")
            print(f"Mejor Trade:  💎 ${daily_perf['best_trade']:,.2f}")
            print(f"Peor Trade:   💔 ${daily_perf['worst_trade']:,.2f}")
        else:
            print("Sin trades hoy")
        print()
        
        # Rendimiento semanal
        print("📈 RENDIMIENTO SEMANAL")
        print("-" * 30)
        if weekly_perf and weekly_perf.get('total_days', 0) > 0:
            weekly_emoji = "🟢" if weekly_perf['total_profit'] > 0 else "🔴" if weekly_perf['total_profit'] < 0 else "🟡"
            
            print(f"Profit Total: {weekly_emoji} ${weekly_perf['total_profit']:,.2f}")
            print(f"Días Profit:  {weekly_perf['profitable_days']}/{weekly_perf['total_days']}")
            print(f"Profit Diario: ${weekly_perf['avg_daily_profit']:,.2f}")
            
            # Mostrar últimos 5 días
            print("\n📅 Últimos 5 días:")
            recent_days = sorted(weekly_perf['daily_profits'].items(), reverse=True)[:5]
            for day, profit in recent_days:
                day_emoji = "💚" if profit > 0 else "❌" if profit < 0 else "⚪"
                print(f"  {day}: {day_emoji} ${profit:,.2f}")
        else:
            print("Sin datos semanales")
        print()
        
        # Métricas de rendimiento
        if daily_perf and daily_perf['total_trades'] > 0:
            print("🎯 MÉTRICAS DE RENDIMIENTO")
            print("-" * 30)
            
            # Calcular ROI diario aproximado
            if account_status and account_status['balance'] > 0:
                daily_roi = (daily_perf['profit'] / account_status['balance']) * 100
                print(f"ROI Diario:   {daily_roi:+.2f}%")
            
            # Profit Factor aproximado
            winning_profit = sum(deal['profit'] for deal in [] if deal.get('profit', 0) > 0)  # Simplificado
            losing_profit = abs(sum(deal['profit'] for deal in [] if deal.get('profit', 0) < 0))  # Simplificado
            
            if daily_perf['win_rate'] > 60:
                performance = "🔥 EXCELENTE"
            elif daily_perf['win_rate'] > 50:
                performance = "✅ BUENO"
            elif daily_perf['win_rate'] > 40:
                performance = "⚠️ REGULAR"
            else:
                performance = "❌ MEJORAR"
            
            print(f"Rendimiento:  {performance}")
            print(f"Win Rate:     {daily_perf['win_rate']:.1f}%")
        
        print()
        print("🔄 Actualizando cada 30 segundos... (Ctrl+C para salir)")
    
    async def run_monitor(self):
        """Ejecutar monitor en tiempo real"""
        
        if not await self.connect():
            print("❌ Error: No se pudo conectar a MT5")
            return
        
        print("✅ Conectado a MT5. Iniciando monitor...")
        
        try:
            while True:
                # Obtener datos
                daily_perf = await self.get_daily_performance()
                weekly_perf = await self.get_weekly_performance()
                account_status = await self.get_account_status()
                
                # Mostrar en pantalla
                self.display_performance(daily_perf, weekly_perf, account_status)
                
                # Esperar 30 segundos
                await asyncio.sleep(30)
                
        except KeyboardInterrupt:
            print("\n👋 Monitor detenido por el usuario")
        except Exception as e:
            print(f"\n❌ Error en monitor: {e}")
        finally:
            await self.mt5.disconnect()

async def main():
    """Función principal"""
    load_dotenv()
    
    # Verificar variables de entorno
    required_vars = ['MT5_LOGIN', 'MT5_PASSWORD', 'MT5_SERVER']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Variables de entorno faltantes:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n📝 Configura el archivo .env antes de continuar")
        return
    
    monitor = PerformanceMonitor()
    await monitor.run_monitor()

if __name__ == "__main__":
    asyncio.run(main())

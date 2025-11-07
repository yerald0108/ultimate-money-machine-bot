#!/usr/bin/env python3
"""
Script de desarrollo con recarga automática usando watchdog
Alternativa más confiable a hupper para el bot de trading
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class BotReloader(FileSystemEventHandler):
    """Manejador de eventos para recargar el bot cuando hay cambios"""
    
    def __init__(self):
        self.process = None
        self.restart_needed = False
        self.last_restart = 0
        self.restart_delay = 2  # Segundos entre reinicios
        
    def start_bot(self):
        """Iniciar el bot"""
        if self.process:
            self.stop_bot()
            
        print("🚀 Iniciando bot...")
        self.process = subprocess.Popen([
            sys.executable, 'main.py', '--no-reload'
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        self.last_restart = time.time()
        print("✅ Bot iniciado")
        
    def stop_bot(self):
        """Detener el bot"""
        if self.process:
            print("🛑 Deteniendo bot...")
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("⚠️  Forzando cierre del bot...")
                self.process.kill()
                self.process.wait()
            finally:
                self.process = None
                print("✅ Bot detenido")
    
    def restart_bot(self):
        """Reiniciar el bot si es necesario"""
        current_time = time.time()
        if current_time - self.last_restart < self.restart_delay:
            return
            
        if self.restart_needed:
            print("🔄 Recargando bot por cambios en el código...")
            self.start_bot()
            self.restart_needed = False
    
    def on_modified(self, event):
        """Manejar evento de archivo modificado"""
        if event.is_directory:
            return
            
        # Solo recargar para archivos Python y .env
        if event.src_path.endswith(('.py', '.env')):
            # Ignorar archivos temporales y __pycache__
            if '__pycache__' in event.src_path or event.src_path.endswith('.pyc'):
                return
                
            print(f"📝 Cambio detectado: {os.path.basename(event.src_path)}")
            self.restart_needed = True
            
            # Reiniciar después de un pequeño delay
            time.sleep(0.5)
            self.restart_bot()

def main():
    """Función principal"""
    print("🔄 Bot de Trading - Modo Desarrollo")
    print("📝 Recarga automática activada")
    print("⏹️  Presiona Ctrl+C para detener")
    print("=" * 50)
    
    # Crear el reloader
    reloader = BotReloader()
    
    # Configurar el observer
    observer = Observer()
    
    # Monitorear el directorio actual y src/
    observer.schedule(reloader, '.', recursive=False)  # main.py, .env
    observer.schedule(reloader, 'src', recursive=True)  # Todo src/
    
    try:
        # Iniciar el observer
        observer.start()
        
        # Iniciar el bot por primera vez
        reloader.start_bot()
        
        # Mantener el script corriendo
        while True:
            time.sleep(1)
            
            # Verificar si el bot sigue corriendo
            if reloader.process and reloader.process.poll() is not None:
                print("⚠️  Bot se detuvo inesperadamente")
                reloader.process = None
                time.sleep(2)
                reloader.start_bot()
                
    except KeyboardInterrupt:
        print("\n⏹️  Deteniendo desarrollo...")
        
    finally:
        # Cleanup
        observer.stop()
        reloader.stop_bot()
        observer.join()
        print("👋 Desarrollo finalizado")

if __name__ == "__main__":
    main()

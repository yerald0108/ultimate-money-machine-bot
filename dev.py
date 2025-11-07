#!/usr/bin/env python3
"""
Script de desarrollo con recarga automática
Usa hupper para recargar el bot automáticamente cuando hay cambios
"""

import os
import sys
import subprocess

def main():
    """Ejecutar el bot con recarga automática"""
    try:
        import hupper
        
        print("🔄 Bot iniciado con recarga automática")
        print("📝 Los cambios en el código recargarán automáticamente el bot")
        print("⏹️  Presiona Ctrl+C para detener")
        print("=" * 50)
        
        # Configurar hupper para llamar main_wrapper
        reloader = hupper.start_reloader('main.main_wrapper')
        
        # Monitorear directorios y archivos específicos
        reloader.watch_files([
            'main.py',
            'src/',
            '.env'
        ])
        
    except ImportError:
        print("❌ Hupper no está instalado")
        print("📦 Instala con: pip install hupper")
        print("🔄 Ejecutando sin recarga automática...")
        print("=" * 50)
        
        # Fallback: ejecutar sin hupper
        try:
            subprocess.run([sys.executable, 'main.py', '--no-reload'])
        except KeyboardInterrupt:
            print("\n⏹️  Bot detenido por el usuario")
            
    except Exception as e:
        print(f"❌ Error iniciando el reloader: {e}")
        print("🔄 Intentando ejecutar sin recarga automática...")
        
        # Fallback: ejecutar sin hupper
        try:
            subprocess.run([sys.executable, 'main.py', '--no-reload'])
        except KeyboardInterrupt:
            print("\n⏹️  Bot detenido por el usuario")

if __name__ == "__main__":
    main()

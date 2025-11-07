"""
Script de verificación para despliegue
Verifica que todo esté configurado correctamente antes del despliegue
"""
import os
import sys
from pathlib import Path

def check_files():
    """Verificar archivos necesarios"""
    required_files = [
        'main.py',
        'requirements.txt',
        'Procfile',
        'runtime.txt',
        '.gitignore',
        'start_production.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Archivos faltantes: {', '.join(missing_files)}")
        return False
    
    print("✅ Todos los archivos necesarios están presentes")
    return True

def check_environment_template():
    """Verificar que existe template de variables de entorno"""
    if Path('.env.example').exists():
        print("✅ Archivo .env.example encontrado")
        return True
    else:
        print("⚠️ Considera crear .env.example con variables de ejemplo")
        return True

def check_gitignore():
    """Verificar .gitignore"""
    if Path('.gitignore').exists():
        with open('.gitignore', 'r') as f:
            content = f.read()
            if '.env' in content:
                print("✅ .gitignore protege archivos .env")
                return True
    
    print("⚠️ Asegúrate de que .gitignore proteja archivos sensibles")
    return True

def check_requirements():
    """Verificar requirements.txt"""
    if Path('requirements.txt').exists():
        with open('requirements.txt', 'r') as f:
            content = f.read()
            required_packages = [
                'python-telegram-bot',
                'MetaTrader5',
                'pandas',
                'numpy'
            ]
            
            missing_packages = []
            for package in required_packages:
                if package not in content:
                    missing_packages.append(package)
            
            if missing_packages:
                print(f"❌ Paquetes faltantes en requirements.txt: {', '.join(missing_packages)}")
                return False
            
            print("✅ requirements.txt contiene paquetes necesarios")
            return True
    
    print("❌ requirements.txt no encontrado")
    return False

def main():
    """Ejecutar todas las verificaciones"""
    print("🔍 VERIFICANDO CONFIGURACIÓN PARA DESPLIEGUE")
    print("=" * 50)
    
    checks = [
        check_files(),
        check_environment_template(),
        check_gitignore(),
        check_requirements()
    ]
    
    print("=" * 50)
    
    if all(checks):
        print("🎉 ¡TODO LISTO PARA DESPLEGAR!")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Crear bot en @BotFather")
        print("2. Obtener credenciales MT5")
        print("3. Subir código a GitHub")
        print("4. Desplegar en Railway/Render/Heroku")
        print("5. Configurar variables de entorno")
        print("\n📖 Ver DEPLOYMENT.md para instrucciones detalladas")
        return True
    else:
        print("❌ Hay problemas que resolver antes del despliegue")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

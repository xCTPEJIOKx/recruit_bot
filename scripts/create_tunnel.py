#!/usr/bin/env python3
"""
Утилита для создания публичного URL через ngrok
Для Avito API OAuth
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pyngrok import ngrok, conf
from common import settings


async def create_tunnel():
    """Создание туннеля ngrok"""
    print("=" * 60)
    print("🌐 Создание публичного URL для Avito API OAuth")
    print("=" * 60)
    print()
    
    # Порт оркестратора
    port = settings.orchestrator_port
    
    print(f"📡 Локальный порт: {port}")
    print()
    
    # Создаём туннель
    try:
        public_url = ngrok.connect(port)
        
        print("✅ Туннель создан!")
        print()
        print("📋 Используйте этот Redirect URI в Avito API:")
        print("-" * 60)
        print(public_url)
        print("-" * 60)
        print()
        print("📝 Добавьте в .env:")
        print(f"AVITO_REDIRECT_URI={public_url}/avito/callback")
        print()
        print("🔗 URL для авторизации (после настройки Client ID):")
        print(f"{public_url}/avito/oauth/start")
        print()
        print("⏹️  Нажмите Ctrl+C для остановки туннеля")
        print()
        
        # Держим туннель активным
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Туннель остановлен")
        ngrok.disconnect()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print()
        print("💡 Попробуйте зарегистрироваться на https://ngrok.com")
        print("   и добавьте auth token:")
        print("   ngrok.set_auth_token('ВАШ_ТОКЕН')")


if __name__ == "__main__":
    asyncio.run(create_tunnel())

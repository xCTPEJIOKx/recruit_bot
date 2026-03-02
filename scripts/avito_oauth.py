#!/usr/bin/env python3
"""
Avito OAuth Token Generator - Упрощённая версия
Без callback URL - только ручной ввод кода
"""
import requests

# === ВАШИ ДАННЫЕ ===
CLIENT_ID = "qmB3BChDn0kBUXWXCnWd"
CLIENT_SECRET = "6T71mhP5hELXL-WFvHtBMuuvNSA8KLxrIIUB9WHA"
# ===================

def main():
    print("🔐 Avito OAuth Token Generator")
    print("=" * 60)
    
    # Генерируем URL для авторизации
    auth_url = (
        f"https://www.avito.ru/authorize?"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri=https://localhost&"
        f"response_type=code&"
        f"scope=messaging"
    )
    
    print("\n📋 Инструкция:")
    print("1. Откройте ссылку в браузере:")
    print(f"   {auth_url}")
    print("\n2. Войдите в аккаунт Avito")
    print("3. Нажмите 'Разрешить'")
    print("4. Скопируйте 'code' из адресной строки")
    print("   (страница покажет ошибку — это нормально)")
    
    code = input("\n✏️  Введите code из URL: ").strip()
    
    if not code:
        print("❌ Код не введён")
        return
    
    # Обмениваем код на токен
    print("\n🔄 Получение токена...")
    
    token_url = "https://api.avito.ru/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "https://localhost"
    }
    
    response = requests.post(token_url, data=data)
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get('access_token', '')
        refresh_token = token_data.get('refresh_token', '')
        
        print("\n✅ УСПЕШНО! Токены получены:")
        print("=" * 60)
        print(f"\n📝 Добавьте в .env файл:\n")
        print(f"AVITO_ACCESS_TOKEN={access_token}")
        print(f"AVITO_REFRESH_TOKEN={refresh_token}")
        
        # Автоматически добавляем в .env
        try:
            with open('.env', 'a') as f:
                f.write(f"\nAVITO_ACCESS_TOKEN={access_token}\n")
                f.write(f"AVITO_REFRESH_TOKEN={refresh_token}\n")
            print("\n✅ Токены сохранены в .env!")
        except Exception as e:
            print(f"\n⚠️  Не удалось сохранить в .env: {e}")
            print("   Добавьте вручную!")
            
    else:
        print(f"\n❌ Ошибка: {response.status_code}")
        print(f"Ответ сервера: {response.text}")

if __name__ == "__main__":
    main()

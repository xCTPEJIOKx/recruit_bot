#!/usr/bin/env python3
"""
Avito Session Saver - вход и сохранение сессии
Использует XVFB для headless браузера с возможностью решения капчи
"""
import asyncio
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright
from common.config import settings


async def save_avito_session():
    """Вход в Avito и сохранение сессии"""
    
    login = settings.avito_login
    password = settings.avito_password
    
    if not login or not password:
        print("❌ AVITO_LOGIN и AVITO_PASSWORD не настроены в .env")
        return False
    
    print("="*60)
    print("🔐 Avito Session Saver")
    print("="*60)
    print(f"\nЛогин: {login}")
    print(f"Пароль: {'*' * len(password)}")
    print("\n⚠️ ВАЖНО: Сейчас откроется браузер.")
    print("   Если появится КАПЧА - решите её вручную.")
    print("   После успешного входа сессия сохранится.\n")
    
    # Автоматическое продолжение для не-TTY среды
    print("🚀 Запуск браузера...\n")
    
    try:
        playwright = await async_playwright().start()
        
        # Запускаем браузер в НЕ-headless режиме для решения капчи
        browser = await playwright.chromium.launch(
            headless=False,  # ВАЖНО: видимый браузер
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--window-size=1920,1080'
            ]
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        print("🌐 Открыт браузер. Выполните вход на Avito...")
        
        # Переход на Avito
        await page.goto("https://www.avito.ru", wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        # Ждём пока пользователь войдёт
        print("\n📝 Инструкция:")
        print("   1. Если видите кнопку 'Войти' - нажмите на неё")
        print("   2. Введите логин и пароль")
        print("   3. Если есть КАПЧА - решите её")
        print("   4. После успешного входа подождите 5 секунд")
        print("\n   Я автоматически проверю вход и сохраню сессию...\n")
        
        # Ждём входа пользователя
        while True:
            try:
                # Проверяем, вошёл ли пользователь
                profile_link = await page.query_selector('a[href="/user_profile"]')
                if profile_link:
                    print("\n✅ Вход выполнен!")
                    break
                
                # Проверяем, на странице ли логина
                current_url = page.url
                if "login" in current_url or "auth" in current_url:
                    print("⏳ Ожидание входа... (текущий URL: /login)")
                else:
                    print(f"⏳ Ожидание входа... (текущий URL: {current_url[:50]})")
                
                await asyncio.sleep(3)
                
            except Exception as e:
                await asyncio.sleep(3)
        
        # Сохранение cookies
        cookies = await context.cookies()
        
        # Фильтруем только avito cookies
        avito_cookies = [c for c in cookies if "avito" in c.get("domain", "")]
        
        session_file = Path("/tmp/avito_session.json")
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(avito_cookies, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Сессия сохранена в {session_file}")
        print(f"   Количество cookies: {len(avito_cookies)}")
        
        # Показываем ключевые cookies
        auth_cookies = [c for c in avito_cookies if any(k in c['name'].lower() for k in ['sid', 'auth', 'token'])]
        if auth_cookies:
            print("\n🔑 Ключевые cookies:")
            for c in auth_cookies[:3]:
                value = c['value'][:30] + "..." if len(c['value']) > 30 else c['value']
                print(f"   - {c['name']}: {value}")
        
        await browser.close()
        
        print("\n" + "="*60)
        print("✅ ГОТОВО!")
        print("="*60)
        print("\nТеперь запустите Avito Browser Agent:")
        print("   python scripts/run_avito_browser.py")
        print("\nИли обновите run.py для автоматического запуска")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(save_avito_session())

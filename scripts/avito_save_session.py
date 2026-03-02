#!/usr/bin/env python3
"""
Avito Session Saver — Надёжное сохранение сессии
ИНСТРУКЦИЯ:
1. Запустите скрипт
2. Откроется браузер
3. Войдите в Avito
4. Нажмите ENTER в терминале когда войдёте
5. Сессия сохранится
"""
import asyncio
import json
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright

async def save_session():
    print("="*60)
    print("🔐 Avito Session Saver")
    print("="*60)
    print()
    print("📋 ИНСТРУКЦИЯ:")
    print("   1. Сейчас откроется браузер")
    print("   2. Перейдите на https://www.avito.ru")
    print("   3. Войдите в аккаунт (+79538765405)")
    print("   4. Когда увидите профиль — нажмите ENTER в терминале")
    print()
    
    # Ждём подтверждения
    input("   → Нажмите ENTER для открытия браузера...")
    
    try:
        playwright = await async_playwright().start()
        
        browser = await playwright.chromium.launch(
            headless=False,  # Видимый браузер!
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
        
        print("🌐 Открываю Avito...")
        await page.goto("https://www.avito.ru", wait_until="domcontentloaded")
        
        print()
        print("✅ Браузер открыт")
        print("   → Войдите в аккаунт Avito")
        print("   → После успешного входа нажмите ENTER")
        print()
        
        # Ждём пока пользователь войдёт
        input("   → Нажмите ENTER когда войдёте в аккаунт...")
        
        # Проверяем что вошли
        print("\n🔍 Проверка входа...")
        try:
            profile_link = await page.query_selector('a[href="/user_profile"]')
            if profile_link:
                print("✅ Вход подтверждён!")
            else:
                print("⚠️ Возможно вы ещё не вошли, но продолжаю...")
        except:
            print("⚠️ Не удалось проверить, но продолжаю...")
        
        # Сохраняем cookies
        print("\n💾 Сохранение сессии...")
        cookies = await context.cookies()
        avito_cookies = [c for c in cookies if "avito" in c.get("domain", "")]
        
        session_file = Path("/tmp/avito_session.json")
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(avito_cookies, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Сохранено {len(avito_cookies)} cookies")
        print(f"📁 Файл: {session_file}")
        
        # Показываем ключевые cookies
        auth_cookies = [c for c in avito_cookies if c['name'] in ['sessid', 'u', 'srv_id']]
        if auth_cookies:
            print("\n🔑 Ключевые cookies:")
            for c in auth_cookies:
                value = c['value'][:30] + "..." if len(c['value']) > 30 else c['value']
                print(f"   - {c['name']}: {value}")
        
        await browser.close()
        
        print("\n" + "="*60)
        print("✅ ГОТОВО!")
        print("="*60)
        print("\nТеперь перезапустите систему:")
        print("   pkill -f 'python run.py'")
        print("   python run.py")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(save_session())
    sys.exit(0 if success else 1)

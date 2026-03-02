#!/usr/bin/env python3
"""
Avito Auto Login - автоматический вход с сохранением сессии
Использует XVFB для работы без дисплея
"""
import asyncio
import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright
from common.config import settings


async def avito_auto_login():
    """Автоматический вход в Avito"""
    
    login = settings.avito_login
    password = settings.avito_password
    
    if not login or not password:
        print("❌ AVITO_LOGIN или AVITO_PASSWORD не настроены")
        return False
    
    print("="*60)
    print("🔐 Avito Auto Login")
    print("="*60)
    print(f"Логин: {login}")
    print(f"Пароль: {'*' * len(password)}")
    print()
    
    # Запускаем XVFB
    print("🖥️  Запуск виртуального дисплея XVFB...")
    xvfb = subprocess.Popen(
        ['Xvfb', ':99', '-screen', '0', '1920x1080x24'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    os.environ['DISPLAY'] = ':99'
    await asyncio.sleep(2)
    
    try:
        playwright = await async_playwright().start()
        
        # Запускаем браузер с реалистичными параметрами
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--window-size=1920,1080'
            ]
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="ru-RU",
            timezone_id="Europe/Moscow"
        )
        
        page = await context.new_page()
        
        # Скрываем признаки автоматизации
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
            Object.defineProperty(navigator, 'languages', {get: () => ['ru-RU', 'ru', 'en']});
        """)
        
        print("🌐 Переход на Avito...")
        await page.goto("https://www.avito.ru", wait_until="networkidle")
        await asyncio.sleep(3)
        
        # Проверяем, вошли ли уже
        profile_link = await page.query_selector('a[href="/user_profile"]')
        if profile_link:
            print("✅ Уже вошли в аккаунт!")
        else:
            print("🔑 Выполняем вход...")
            
            # Переход на страницу входа
            await page.goto("https://www.avito.ru/profile", wait_until="networkidle")
            await asyncio.sleep(3)
            
            # Ищем кнопку входа
            login_btn = await page.query_selector('a[href*="login"], button:has-text("Войти"), a:has-text("Войти")')
            if login_btn:
                await login_btn.click()
                await asyncio.sleep(3)
            
            # Ввод логина
            print("  → Ввод логина...")
            login_input = await page.query_selector('input[type="text"], input[type="tel"], input[name="phone"]')
            if login_input:
                await login_input.fill(login)
                await asyncio.sleep(1)
                
                # Кнопка продолжения
                continue_btn = await page.query_selector('button:has-text("Продолжить"), button[type="submit"]')
                if continue_btn:
                    await continue_btn.click()
                    await asyncio.sleep(3)
            
            # Ввод пароля
            print("  → Ввод пароля...")
            password_input = await page.query_selector('input[type="password"]')
            if password_input:
                await password_input.fill(password)
                await asyncio.sleep(1)
                
                # Кнопка входа
                submit_btn = await page.query_selector('button:has-text("Войти"), button[type="submit"]')
                if submit_btn:
                    await submit_btn.click()
                    await asyncio.sleep(5)
            
            # Проверка входа
            await page.goto("https://www.avito.ru/profile", wait_until="networkidle")
            await asyncio.sleep(3)
            
            profile_link = await page.query_selector('a[href="/user_profile"]')
            if profile_link:
                print("✅ Успешный вход!")
            else:
                print("⚠️ Возможно требуется капча. Делаем скриншот...")
                await page.screenshot(path="/tmp/avito_captcha.png")
                print("📸 Скриншот: /tmp/avito_captcha.png")
        
        # Сохранение cookies
        print("\n💾 Сохранение сессии...")
        cookies = await context.cookies()
        avito_cookies = [c for c in cookies if "avito" in c.get("domain", "")]
        
        session_file = Path("/tmp/avito_session.json")
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(avito_cookies, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Сохранено {len(avito_cookies)} cookies")
        
        # Показываем ключевые
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
        print(f"\nСессия сохранена в: {session_file}")
        print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nТеперь запустите Avito агента:")
        print("   python scripts/run_avito_browser.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Останавливаем XVFB
        xvfb.terminate()
        print("\n👋 XVFB остановлен")


if __name__ == "__main__":
    success = asyncio.run(avito_auto_login())
    sys.exit(0 if success else 1)

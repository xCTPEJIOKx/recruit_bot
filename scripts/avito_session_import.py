#!/usr/bin/env python3
"""
Avito Session Importer - импорт cookies из вашего браузера

ИНСТРУКЦИЯ:
1. Откройте Chrome/Firefox на своём компьютере
2. Войдите на https://www.avito.ru
3. Откройте DevTools (F12) → Application → Cookies → https://www.avito.ru
4. Скопируйте все cookies в формате JSON
5. Вставьте в этот скрипт или сохраните в /tmp/avito_session.json
"""
import json
import sys
from pathlib import Path

def main():
    print("="*60)
    print("🍪 Avito Session Importer")
    print("="*60)
    print("\n📋 Инструкция по получению cookies:")
    print()
    print("1. Откройте Chrome или Firefox")
    print("2. Войдите на https://www.avito.ru")
    print("3. Нажмите F12 (DevTools)")
    print("4. Перейдите во вкладку 'Application' (Chrome) или 'Storage' (Firefox)")
    print("5. Раскройте 'Cookies' → 'https://www.avito.ru'")
    print("6. Выделите все cookies (Ctrl+A)")
    print("7. Скопируйте (Ctrl+C)")
    print("8. Вставьте в консоль ниже или сохраните в файл")
    print()
    
    # Проверяем, есть ли файл с cookies
    session_file = Path("/tmp/avito_session.json")
    
    if len(sys.argv) > 1:
        # Cookies переданы как аргумент
        cookies_json = " ".join(sys.argv[1:])
    else:
        # Пробуем прочитать из stdin или файла
        print("📥 Вставьте cookies JSON (или путь к файлу):")
        cookies_json = input("> ").strip()
    
    # Если это путь к файлу
    if cookies_json.endswith(".json") and Path(cookies_json).exists():
        with open(cookies_json, 'r') as f:
            cookies = json.load(f)
    else:
        # Парсим JSON
        try:
            cookies = json.loads(cookies_json)
        except json.JSONDecodeError as e:
            print(f"\n❌ Ошибка парсинга JSON: {e}")
            print("Убедитесь, что скопировали корректный JSON")
            return False
    
    # Фильтруем cookies для avito.ru
    avito_cookies = []
    for cookie in cookies:
        if isinstance(cookie, dict):
            domain = cookie.get('domain', '')
            if 'avito' in domain.lower() or cookie.get('name', '').startswith('avito'):
                # Нормализуем формат
                avito_cookie = {
                    'name': cookie.get('name', ''),
                    'value': cookie.get('value', ''),
                    'domain': cookie.get('domain', '.avito.ru'),
                    'path': cookie.get('path', '/'),
                    'expires': cookie.get('expirationDate', cookie.get('expires', None)),
                    'httpOnly': cookie.get('httpOnly', True),
                    'secure': cookie.get('secure', True)
                }
                avito_cookies.append(avito_cookie)
    
    if not avito_cookies:
        print("\n❌ Cookies для Avito не найдены")
        print("Убедитесь, что скопировали cookies для https://www.avito.ru")
        return False
    
    # Сохраняем
    with open(session_file, 'w', encoding='utf-8') as f:
        json.dump(avito_cookies, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Сохранено {len(avito_cookies)} cookies в {session_file}")
    
    # Показываем ключевые cookies
    auth_cookies = [c for c in avito_cookies if any(k in c['name'].lower() for k in ['sid', 'auth', 'token', 'session'])]
    if auth_cookies:
        print("\n🔑 Ключевые cookies:")
        for c in auth_cookies[:5]:
            value = c['value'][:30] + "..." if len(c['value']) > 30 else c['value']
            print(f"   - {c['name']}: {value}")
    
    print("\n" + "="*60)
    print("✅ ГОТОВО!")
    print("="*60)
    print("\nТеперь перезапустите Avito агента:")
    print("   pkill -f avito_browser_agent")
    print("   python scripts/run_avito_browser.py")
    print("\nИли перезапустите всю систему:")
    print("   pkill -f 'python run.py'")
    print("   python run.py")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

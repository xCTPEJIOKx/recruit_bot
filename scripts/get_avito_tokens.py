#!/usr/bin/env python3
"""
Avito OAuth Token Getter - Authorization Code Flow
Использует правильный Redirect URI
"""
import aiohttp
import asyncio
import sys
import os
import base64
import webbrowser
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading

project_root = Path(__file__).parent.parent

# Ручная загрузка .env
with open(project_root / '.env', 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key] = value

CLIENT_ID = os.environ.get('AVITO_CLIENT_ID', '')
CLIENT_SECRET = os.environ.get('AVITO_CLIENT_SECRET', '')

# Cloudflare Tunnel URL
REDIRECT_URI = "https://solve-benchmark-mothers-canberra.trycloudflare.com/api/avito/callback"

if not CLIENT_ID or not CLIENT_SECRET:
    print("❌ AVITO_CLIENT_ID или AVITO_CLIENT_SECRET не настроены")
    sys.exit(1)

# Глобальная переменная для auth code
auth_code = None
code_received = threading.Event()

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        if 'code' in params:
            auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'''
                <html><head><title>Avito OAuth</title>
                <style>body{font-family:Arial;display:flex;justify-content:center;align-items:center;height:100vh;background:linear-gradient(135deg,#00aaff,#00d9ff);color:white}</style>
                </head><body><div style="text-align:center;padding:40px;background:rgba(255,255,255,0.1);border-radius:20px">
                <h1>✅ Avito OAuth</h1><p>Авторизация успешна!</p><p>Вернитесь в терминал для получения токенов.</p>
                </div></body></html>
            ''')
            code_received.set()
        else:
            self.send_response(400)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress logging

async def get_authorization_url():
    """Генерация URL для авторизации"""
    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': 'autorus_listing messages'
    }
    query = '&'.join([f"{k}={v}" for k, v in params.items()])
    return f"https://api.avito.ru/oauth/authorize?{query}"

async def exchange_code_for_token(code: str):
    """Обмен code на токен"""
    url = "https://api.avito.ru/oauth/token"
    
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data, headers=headers) as response:
            result = await response.json()
            
            if response.status == 200:
                return result
            else:
                print(f"❌ Ошибка: {result}")
                return None

async def main():
    print("="*60)
    print("🔑 Avito OAuth Token Getter")
    print("="*60)
    print(f"Client ID: {CLIENT_ID[:10]}...")
    print(f"Redirect URI: {REDIRECT_URI}")
    print()
    
    # Запускаем локальный сервер для callback
    print("📡 Запуск сервера для приёма callback...")
    server = HTTPServer(('127.0.0.1', 8000), CallbackHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    # Генерируем URL авторизации
    auth_url = await get_authorization_url()
    
    print(f"\n📱 ИНСТРУКЦИЯ:")
    print(f"   1. Откройте в браузере:")
    print(f"      {auth_url}")
    print(f"   2. Войдите в аккаунт Avito")
    print(f"   3. Подтвердите доступ к приложению")
    print(f"   4. Токены будут получены автоматически")
    print()
    
    # Открываем браузер
    try:
        webbrowser.open(auth_url)
        print("🌐 Браузер открыт")
    except:
        pass
    
    # Ждём code
    print("\n⏳ Ожидание авторизации...")
    if code_received.wait(timeout=300):  # 5 минут
        print(f"✅ Authorization code получен: {auth_code[:20]}...")
        
        # Обмениваем code на токен
        print("\n📡 Обмен code на токен...")
        result = await exchange_code_for_token(auth_code)
        
        if result:
            access_token = result.get("access_token", "")
            refresh_token = result.get("refresh_token", "")
            expires_in = result.get("expires_in", 86400)
            
            print("\n" + "="*60)
            print("✅ ТОКЕНЫ ПОЛУЧЕНЫ!")
            print("="*60)
            print(f"\nAccess Token: {access_token[:50]}...")
            print(f"Refresh Token: {refresh_token[:50]}...")
            print(f"Срок действия: {expires_in // 3600} ч")
            
            # Сохраняем в .env
            env_file = project_root / '.env'
            try:
                with open(env_file, 'r') as f:
                    content = f.read()
                
                import re
                if 'AVITO_ACCESS_TOKEN=' in content:
                    content = re.sub(r'AVITO_ACCESS_TOKEN=.*', f'AVITO_ACCESS_TOKEN={access_token}', content)
                else:
                    content += f'\nAVITO_ACCESS_TOKEN={access_token}'
                
                if 'AVITO_REFRESH_TOKEN=' in content:
                    content = re.sub(r'AVITO_REFRESH_TOKEN=.*', f'AVITO_REFRESH_TOKEN={refresh_token}', content)
                else:
                    content += f'\nAVITO_REFRESH_TOKEN={refresh_token}'
                
                with open(env_file, 'w') as f:
                    f.write(content)
                
                print(f"\n✅ Токены сохранены в {env_file}")
            except Exception as e:
                print(f"\n⚠️ Не удалось сохранить: {e}")
                print(f"\nСохраните вручную:")
                print(f"AVITO_ACCESS_TOKEN={access_token}")
                print(f"AVITO_REFRESH_TOKEN={refresh_token}")
            
            return True
    else:
        print("❌ Превышено время ожидания")
    
    return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

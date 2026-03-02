"""
Web Dashboard для системы рекрутинга
"""
from .app import app

# Avito OAuth routes
from fastapi import APIRouter, Query
from urllib.parse import urlencode
import aiohttp

router = APIRouter()

@router.get("/avito/oauth/start")
async def avito_oauth_start():
    """Начало OAuth авторизации Avito"""
    from common import settings
    
    if not settings.avito_client_id:
        return {"error": "AVITO_CLIENT_ID не настроен"}
    
    redirect_uri = settings.avito_redirect_uri or "https://manufacturers-ships-shopping-tribe.trycloudflare.com/avito/callback"
    
    params = {
        'response_type': 'code',
        'client_id': settings.avito_client_id,
        'redirect_uri': redirect_uri,
        'scope': 'vacancies responses',
    }
    
    auth_url = f"https://api.avito.ru/oauth/authorize?{urlencode(params)}"
    
    return {
        "authorization_url": auth_url,
        "instruction": "Перейдите по этой ссылке для авторизации в Avito API"
    }


@router.get("/avito/callback")
async def avito_callback(code: str = Query(...)):
    """Callback от Avito OAuth"""
    from common import settings
    
    # Обмен кода на токен
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': settings.avito_client_id,
        'client_secret': settings.avito_client_secret,
        'redirect_uri': settings.avito_redirect_uri or "https://manufacturers-ships-shopping-tribe.trycloudflare.com/avito/callback",
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.avito.ru/oauth/token", data=token_data) as response:
            result = await response.json()
            
            if response.status == 200:
                # Токены получены успешно
                return f"""
                <html>
                <head>
                    <title>Avito OAuth - Успешно</title>
                    <script src="https://cdn.tailwindcss.com"></script>
                </head>
                <body class="bg-green-50 min-h-screen flex items-center justify-center">
                    <div class="bg-white p-8 rounded-xl shadow-lg max-w-md">
                        <div class="text-center">
                            <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                <i class="fas fa-check text-green-500 text-3xl"></i>
                            </div>
                            <h1 class="text-2xl font-bold text-gray-800 mb-2">OAuth завершён!</h1>
                            <p class="text-gray-600 mb-6">Токены Avito API получены успешно</p>
                            
                            <div class="bg-gray-50 p-4 rounded-lg text-left mb-6">
                                <p class="text-sm font-medium text-gray-700 mb-2">Добавьте в .env:</p>
                                <code class="text-xs text-gray-600 block whitespace-pre-wrap break-all">
AVITO_ACCESS_TOKEN={result.get('access_token', '')}
AVITO_REFRESH_TOKEN={result.get('refresh_token', '')}
                                </code>
                            </div>
                            
                            <button onclick="window.close()" 
                                    class="bg-green-500 hover:bg-green-600 text-white px-6 py-2 rounded-lg">
                                Закрыть
                            </button>
                        </div>
                    </div>
                </body>
                </html>
                """
            else:
                return f"""
                <html>
                <head><title>Ошибка</title><script src="https://cdn.tailwindcss.com"></script></head>
                <body class="bg-red-50 min-h-screen flex items-center justify-center">
                    <div class="bg-white p-8 rounded-xl shadow-lg max-w-md text-center">
                        <h1 class="text-2xl font-bold text-red-600 mb-4">Ошибка OAuth</h1>
                        <p class="text-gray-600">{result.get('error', 'Неизвестная ошибка')}</p>
                    </div>
                </body>
                </html>
                """


# Подключаем роуты к основному приложению
app.include_router(router)

__all__ = ["app"]

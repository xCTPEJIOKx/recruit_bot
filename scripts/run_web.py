#!/usr/bin/env python3
"""
Recruitment System - Web Dashboard Launcher
"""
import asyncio
import sys
import os
import webbrowser

# Добавляем корень проекта в path
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from common import db

async def main():
    print("=" * 60)
    print("    Recruitment System - Запуск веб-интерфейса")
    print("=" * 60)
    print()
    
    # Подключение к БД
    await db.connect()
    print("[OK] База данных подключена")
    print()
    
    # Импорт после подключения к БД
    from web_dashboard.app import app
    import uvicorn
    
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8080,
        log_level="info",
        reload=False
    )
    
    server = uvicorn.Server(config)
    
    print("[INFO] Запуск сервера...")
    print()
    print("=" * 60)
    print("    Веб-интерфейс доступен!")
    print("=" * 60)
    print()
    print("URL:")
    print("  http://localhost:8080/")
    print()
    
    # Открываем браузер
    try:
        webbrowser.open("http://localhost:8080")
    except:
        pass
    
    # Запускаем сервер
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] Остановка...")

#!/usr/bin/env python3
"""
Запуск всех агентов одновременно
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path

# Добавляем корень проекта в path
sys.path.insert(0, str(Path(__file__).parent))

from common import db, settings
from telegram_bot import run_telegram_bot
from avito_agent.avito_browser_agent import run_avito_browser_agent  # Browser агент (реальные отклики)
from voice_agent import run_voice_agent
from orchestrator import run_orchestrator
from classifieds_agent import run_classifieds_agent

# Принудительная смена порта если 8000 занят
import socket
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('0.0.0.0', port)) == 0

if is_port_in_use(8000):
    print(f"⚠️ Порт 8000 занят, используем 8002...")
    settings.orchestrator_port = 8002
elif is_port_in_use(8001):
    print(f"⚠️ Порт 8001 занят, используем 8003...")
    settings.orchestrator_port = 8003

logger = logging.getLogger(__name__)


class AgentRunner:
    """Запуск и управление всеми агентами"""
    
    def __init__(self):
        self.is_running = False
        self.tasks = []
    
    async def start(self):
        """Запуск всех агентов"""
        logger.info("🚀 Запуск системы рекрутинговых агентов...")
        logger.info(f"📁 Путь к БД: {settings.database_path_abs}")
        
        self.is_running = True
        
        # Запускаем оркестратор (первым)
        logger.info("\n{'='*50}")
        logger.info("🎯 Запуск Orchestrator...")
        self.tasks.append(asyncio.create_task(self._run_with_restart(run_orchestrator, "Orchestrator")))
        await asyncio.sleep(2)  # Ждём пока запустится API
        
        # Запускаем Telegram бота
        logger.info("\n{'='*50}")
        logger.info("📱 Запуск Telegram Bot...")
        self.tasks.append(asyncio.create_task(self._run_with_restart(run_telegram_bot, "Telegram Bot")))
        
        # Запускаем Avito агента (Browser версия - реальные отклики)
        logger.info("\n{'='*50}")
        logger.info("📦 Запуск Avito Browser Agent (реальные отклики)")
        self.tasks.append(asyncio.create_task(self._run_with_restart(run_avito_browser_agent, "Avito Browser Agent")))
        
        # Запускаем Voice агента
        logger.info("\n{'='*50}")
        logger.info("📞 Запуск Voice Agent...")
        self.tasks.append(asyncio.create_task(self._run_with_restart(run_voice_agent, "Voice Agent")))
        
        # Запускаем Classifieds агента
        logger.info("\n{'='*50}")
        logger.info("📢 Запуск Classifieds Agent...")
        self.tasks.append(asyncio.create_task(self._run_with_restart(run_classifieds_agent, "Classifieds Agent")))
        
        logger.info("\n{'='*50}")
        logger.info("✅ Все агенты запущены!")
        logger.info("📊 API Orchestrator: http://localhost:8000")
        logger.info("📈 Dashboard: http://localhost:8000/dashboard")
        logger.info("\nНажмите Ctrl+C для остановки\n")
        
        # Ждём пока все работают
        try:
            await asyncio.gather(*self.tasks)
        except asyncio.CancelledError:
            logger.info("🛑 Получен сигнал остановки...")
    
    async def stop(self):
        """Остановка всех агентов"""
        self.is_running = False
        
        for task in self.tasks:
            task.cancel()
        
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        logger.info("👋 Все агенты остановлены")
    
    async def _run_with_restart(self, coro_func, name: str, max_retries: int = 3):
        """Запуск агента с авто-перезапуском при ошибках"""
        retries = 0
        
        while self.is_running and retries < max_retries:
            try:
                await coro_func()
            except asyncio.CancelledError:
                logger.info(f"🛑 {name} остановлен")
                break
            except Exception as e:
                retries += 1
                logger.error(f"❌ {name} ошибка ({retries}/{max_retries}): {e}")
                
                if retries < max_retries:
                    logger.info(f"🔄 {name} перезапуск через 5 секунд...")
                    await asyncio.sleep(5)
                else:
                    logger.error(f"🚫 {name} превышено количество попыток")


async def main():
    """Основная функция"""
    # Настройка логирования
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )
    
    # Подключение к БД
    await db.connect()
    logger.info("✅ База данных подключена")
    
    # Обработка сигналов
    runner = AgentRunner()
    
    def signal_handler(sig, frame):
        logger.info(f"\n📶 Получен сигнал {sig}")
        asyncio.create_task(runner.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await runner.start()
    finally:
        await db.close()
        logger.info("✅ База данных отключена")


if __name__ == "__main__":
    asyncio.run(main())

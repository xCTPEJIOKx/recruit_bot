#!/usr/bin/env python3
"""
Запуск Avito Browser Agent
Автоматическая обработка откликов на Avito через браузер
"""
import asyncio
import logging
import signal
import sys
import os
from pathlib import Path

# Добавляем корень проекта в path и меняем рабочую директорию
project_root = Path(__file__).parent.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root))

from common.database import db
from common.config import settings
from avito_agent.avito_browser_agent import AvitoBrowserAgent

logger = logging.getLogger(__name__)


async def run_avito_browser():
    """Запуск Avito Browser Agent"""
    logger.info("="*60)
    logger.info("🤖 AVITO BROWSER AGENT")
    logger.info("="*60)
    logger.info("\nФункционал:")
    logger.info("  • Мониторинг новых откликов на Avito")
    logger.info("  • Отправка приглашений в Telegram бот")
    logger.info("  • Сохранение кандидатов в базу данных")
    logger.info("\nКонфигурация:")
    logger.info(f"  • Avito Login: {logging.getLogger().handlers and 'настроен' or 'не настроен'}")
    logger.info(f"  • Telegram Bot: @Recruit2026_bot")
    logger.info("="*60 + "\n")
    
    agent = AvitoBrowserAgent()
    
    # Обработка сигналов
    stop_event = asyncio.Event()
    
    def signal_handler(sig, frame):
        logger.info(f"\n📶 Получен сигнал остановки...")
        stop_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await agent.start()
    except asyncio.CancelledError:
        logger.info("🛑 Агент остановлен")
    finally:
        await agent.stop()


async def main():
    """Основная функция"""
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )
    
    # Подключение к БД
    await db.connect()
    logger.info("✅ База данных подключена")
    
    try:
        await run_avito_browser()
    finally:
        await db.close()
        logger.info("✅ База данных отключена")


if __name__ == "__main__":
    asyncio.run(main())

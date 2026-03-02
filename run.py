#!/usr/bin/env python3
"""
Recruitment System - Запуск Web App + API
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import db
from telegram_bot.bot import TelegramBot
from voice_agent.voice_agent import VoiceAgent
from orchestrator.orchestrator import Orchestrator

logger = logging.getLogger(__name__)


async def main():
    """Запуск системы"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    await db.connect()
    logger.info("✅ База данных подключена")

    # Запуск Orchestrator (API + Web App)
    orchestrator = Orchestrator()
    orch_task = asyncio.create_task(orchestrator.start())
    await asyncio.sleep(2)

    # Запуск Telegram бота
    tg_bot = TelegramBot()
    tg_task = asyncio.create_task(tg_bot.start())
    await asyncio.sleep(2)

    # Запуск Voice агента
    voice = VoiceAgent()
    voice_task = asyncio.create_task(voice.start())

    logger.info("=" * 50)
    logger.info("✅ Система запущена!")
    logger.info("📡 API: http://localhost:8000")
    logger.info("🌐 Web App: http://localhost:8000/static/index.html")
    logger.info("📊 Dashboard: http://localhost:8000/candidates")
    logger.info("=" * 50)

    try:
        await asyncio.gather(orch_task, tg_task, voice_task)
    except KeyboardInterrupt:
        logger.info("\n🛑 Остановка...")
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())

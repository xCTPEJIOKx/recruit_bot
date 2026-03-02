#!/usr/bin/env python3
"""
Скрипт для отправки приглашений кандидатам из Avito в Telegram
Запускается периодически через orchestrator
"""
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.database import db
from common.models import Candidate, AgentType, Task
from agents.telegram_agent import TelegramAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AvitoInviteProcessor:
    """Обработчик приглашений для кандидатов из Avito"""

    def __init__(self):
        self.telegram_agent = TelegramAgent()
        self.processed_candidates = set()  # Кандидаты, которым уже отправили приглашение

    async def process_new_avito_candidates(self):
        """Обработать новых кандидатов из Avito"""
        try:
            # Получаем новых кандидатов из Avito
            from common.database import get_candidates_by_status, CandidateStatus
            
            candidates = await db.get_candidates_by_status(CandidateStatus.NEW)
            
            # Фильтруем только тех, кто с Avito и кому ещё не отправляли
            avito_candidates = [
                c for c in candidates 
                if c.source == 'avito' and c.id not in self.processed_candidates
            ]
            
            if not avito_candidates:
                logger.debug("Нет новых кандидатов из Avito для обработки")
                return 0
            
            logger.info(f"📬 Найдено {len(avito_candidates)} новых кандидатов из Avito")
            
            sent_count = 0
            for candidate in avito_candidates:
                success = await self.telegram_agent.send_avito_invite(
                    candidate_id=candidate.id,
                    vacancy_id=candidate.vacancy_id
                )
                
                if success:
                    self.processed_candidates.add(candidate.id)
                    sent_count += 1
                    logger.info(f"✅ Отправлено приглашение: {candidate.name} ({candidate.phone})")
                else:
                    logger.warning(f"❌ Не удалось отправить приглашение: {candidate.name}")
            
            logger.info(f"📤 Отправлено {sent_count}/{len(avito_candidates)} приглашений")
            return sent_count
            
        except Exception as e:
            logger.error(f"Ошибка обработки кандидатов: {e}")
            return 0

    async def run_periodic(self, interval_seconds: int = 60):
        """Периодический запуск"""
        logger.info(f"🔄 Запуск периодической обработки (интервал: {interval_seconds}с)")
        
        while True:
            try:
                await self.process_new_avito_candidates()
            except Exception as e:
                logger.error(f"Ошибка в периодической обработке: {e}")
            
            await asyncio.sleep(interval_seconds)


async def main():
    """Основная функция"""
    logger.info("🚀 Запуск обработчика приглашений Avito → Telegram")
    
    # Подключение к БД
    await db.connect()
    
    try:
        processor = AvitoInviteProcessor()
        
        # Запускаем периодическую обработку (каждые 30 секунд)
        await processor.run_periodic(interval_seconds=30)
        
    except KeyboardInterrupt:
        logger.info("🛑 Остановка по сигналу пользователя")
    finally:
        await db.close()
        await processor.telegram_agent.stop()


if __name__ == "__main__":
    asyncio.run(main())

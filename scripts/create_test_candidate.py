#!/usr/bin/env python3
"""
Создать тестового кандидата и отправить приглашение
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from common.database import db
from common.models import Candidate, Vacancy, CandidateStatus
from agents.telegram_agent import TelegramAgent


async def main():
    await db.connect()
    
    # Ваш Telegram ID
    TG_ID = 8197222276
    
    # Создаём тестового кандидата
    candidate = Candidate(
        name="Тестовый Кандидат",
        phone="+79991234567",
        telegram_id=TG_ID,
        telegram_username="test_user",
        source="avito",
        status=CandidateStatus.NEW,
        notes="Тестовый кандидат для проверки Avito → Telegram приглашений"
    )
    
    # Получаем первую активную вакансию
    vacancies = await db.get_active_vacancies()
    if vacancies:
        candidate.vacancy_id = vacancies[0].id
        print(f"📌 Вакансия: {vacancies[0].title}")
    
    # Сохраняем кандидата
    await db.create_candidate(candidate)
    print(f"✅ Создан кандидат:")
    print(f"   Имя: {candidate.name}")
    print(f"   Телефон: {candidate.phone}")
    print(f"   Telegram ID: {candidate.telegram_id}")
    print(f"   Источник: {candidate.source}")
    print(f"   ID: {candidate.id}")
    
    # Отправляем приглашение
    print(f"\n📤 Отправка приглашения в Telegram...")
    agent = TelegramAgent()
    success = await agent.send_avito_invite(
        candidate_id=candidate.id,
        vacancy_id=candidate.vacancy_id
    )
    
    if success:
        print(f"✅ Приглашение отправлено в Telegram!")
        print(f"   Проверьте @Recruit2026_bot")
    else:
        print(f"❌ Ошибка отправки приглашения")
    
    await agent.stop()
    await db.close()


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Скрипт для отправки тестового приглашения кандидату в Telegram
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from common.database import db
from common.models import Candidate
from agents.telegram_agent import TelegramAgent


async def send_invite(phone: str):
    """Отправить приглашение кандидату по номеру телефона"""
    await db.connect()
    
    # Ищем кандидата по телефону
    candidates = await db.get_all_candidates(limit=1000)
    candidate = None
    
    phone_clean = phone.replace(' ', '').replace('-', '')
    for c in candidates:
        c_phone = c.phone.replace(' ', '').replace('-', '') if c.phone else ''
        if phone_clean in c_phone or c_phone in phone_clean:
            candidate = c
            break
    
    if not candidate:
        print(f"❌ Кандидат с номером {phone} не найден")
        await db.close()
        return
    
    print(f"📬 Найден кандидат:")
    print(f"   Имя: {candidate.name}")
    print(f"   Телефон: {candidate.phone}")
    print(f"   Telegram ID: {candidate.telegram_id}")
    print(f"   Источник: {candidate.source}")
    
    if not candidate.telegram_id:
        print("\n⚠️  У кандидата нет Telegram ID!")
        print("   Кандидат должен сначала написать боту @Recruit2026_bot")
        print("   После этого его telegram_id сохранится в базе")
        await db.close()
        return
    
    # Отправляем приглашение
    agent = TelegramAgent()
    
    print(f"\n📤 Отправка приглашения...")
    success = await agent.send_avito_invite(
        candidate_id=candidate.id,
        vacancy_id=candidate.vacancy_id
    )
    
    if success:
        print(f"✅ Приглашение отправлено!")
    else:
        print(f"❌ Ошибка отправки приглашения")
    
    await agent.stop()
    await db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python3 send_invite.py <телефон>")
        print("Пример: python3 send_invite.py +79538765405")
        sys.exit(1)
    
    phone = sys.argv[1]
    asyncio.run(send_invite(phone))

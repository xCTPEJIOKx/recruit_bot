#!/usr/bin/env python3
"""
Создать задачу на звонок
"""
import asyncio
import sys
sys.path.insert(0, '.')

from common import db, Candidate, Task, AgentType, CandidateStatus

async def create_call_task():
    await db.connect()
    
    # Создаём кандидата
    candidate = Candidate(
        name="Пользователь",
        phone="+79538765405",
        source="manual",
        status=CandidateStatus.NEW,
        notes="Тестовый звонок"
    )
    
    await db.create_candidate(candidate)
    print(f"✅ Кандидат создан: {candidate.id}")
    
    # Создаём задачу на звонок
    task = Task(
        agent_type=AgentType.VOICE,
        task_type="call_candidate",
        payload={
            "candidate_id": candidate.id,
            "phone": "+79538765405",
            "name": "Пользователь",
        },
        priority=0  # Высший приоритет
    )
    
    await db.create_task(task)
    print(f"✅ Задача на звонок создана: {task.id}")
    print(f"📞 Номер: +79538765405")
    print()
    print("⏳ Voice Agent обработает задачу в течение 5 секунд...")
    
    await db.close()

if __name__ == "__main__":
    asyncio.run(create_call_task())

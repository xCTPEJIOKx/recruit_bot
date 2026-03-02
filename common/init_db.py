#!/usr/bin/env python3
"""
Инициализация базы данных
"""
import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в path
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.database import db
from common.models import Vacancy


async def init_db():
    """Инициализация БД и создание тестовых данных"""
    print("🔧 Инициализация базы данных...")
    
    await db.connect()
    print("✅ База данных подключена")
    
    # Создадим тестовую вакансию
    vacancies = await db.get_active_vacancies()
    if not vacancies:
        vacancy = Vacancy(
            title="Менеджер по продажам",
            description="Мы ищем активного менеджера по продажам в нашу команду!",
            salary_min=50000,
            salary_max=150000,
            requirements="- Опыт продаж от 1 года\n- Грамотная речь\n- Умение работать в команде",
            conditions="- Удалённая работа\n- Гибкий график\n- Обучение за счёт компании",
        )
        await db.create_vacancy(vacancy)
        print(f"✅ Создана тестовая вакансия: {vacancy.title}")
    
    # Статистика
    stats = await db.get_stats()
    print("\n📊 Статистика:")
    print(f"   Активных вакансий: {stats['active_vacancies']}")
    print(f"   Всего кандидатов: {sum(stats['candidates_by_status'].values())}")
    
    await db.close()
    print("\n✅ Инициализация завершена!")


if __name__ == "__main__":
    asyncio.run(init_db())

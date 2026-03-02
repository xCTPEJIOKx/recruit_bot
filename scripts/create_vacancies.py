#!/usr/bin/env python3
"""
Скрипт для создания тестовых вакансий
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from common import db, Vacancy


async def create_sample_vacancies():
    """Создание тестовых вакансий"""
    await db.connect()
    
    vacancies = [
        Vacancy(
            title="Менеджер по продажам",
            description="Мы ищем активного менеджера по продажам в нашу команду!\n\nЧто нужно делать:\n• Обрабатывать входящие заявки\n• Консультировать клиентов\n• Вести переговоры\n• Выполнять план продаж",
            salary_min=50000,
            salary_max=150000,
            requirements="• Опыт продаж от 1 года\n• Грамотная речь\n• Умение работать в команде\n• Ориентация на результат",
            conditions="• Удалённая работа\n• Гибкий график\n• Обучение за счёт компании\n• Карьерный рост",
        ),
        Vacancy(
            title="Оператор call-центра",
            description="Приглашаем операторов для работы в call-центре!\n\nОбязанности:\n• Обработка входящих звонков\n• Консультирование клиентов\n• Работа в CRM-системе",
            salary_min=35000,
            salary_max=80000,
            requirements="• Грамотная речь\n• Умение слушать\n• Уверенный пользователь ПК\n• Можно без опыта",
            conditions="• Сменный график 2/2\n• Официальное оформление\n• Премии по результатам работы",
        ),
        Vacancy(
            title="Специалист по подбору персонала",
            description="В связи с расширением ищем рекрутера!\n\nЧто предстоит делать:\n• Поиск кандидатов на различных площадках\n• Проведение собеседований\n• Ведение базы кандидатов",
            salary_min=45000,
            salary_max=100000,
            requirements="• Опыт в подборе персонала от 1 года\n• Знание источников поиска\n• Коммуникабельность\n• Внимательность",
            conditions="• Офис/удалёнка на выбор\n• Пятидневка\n• Дружный коллектив\n• Интересные задачи",
        ),
    ]
    
    for vacancy in vacancies:
        # Проверяем, нет ли уже такой вакансии
        existing = await db.get_active_vacancies()
        if not any(v.title == vacancy.title for v in existing):
            await db.create_vacancy(vacancy)
            print(f"✅ Создана вакансия: {vacancy.title}")
        else:
            print(f"⏭️  Пропущено: {vacancy.title} (уже существует)")
    
    stats = await db.get_stats()
    print(f"\n📊 Всего активных вакансий: {stats['active_vacancies']}")
    
    await db.close()


if __name__ == "__main__":
    asyncio.run(create_sample_vacancies())

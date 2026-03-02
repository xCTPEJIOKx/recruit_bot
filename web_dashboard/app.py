"""
Web Dashboard - Графический интерфейс для системы рекрутинга
"""
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import asyncio
from pathlib import Path

from common import db, Candidate, CandidateStatus, Vacancy, AgentType, Task

# Создание приложения
app = FastAPI(title="Recruitment Dashboard")

# Пути
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Шаблоны
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Монтирование статики
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ========== Модели ==========

class CandidateForm(BaseModel):
    name: str
    phone: str
    source: str = "manual"
    vacancy_id: Optional[str] = None
    notes: Optional[str] = None


class VacancyForm(BaseModel):
    title: str
    description: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    requirements: Optional[str] = None
    conditions: Optional[str] = None


# ========== Страницы ==========

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Главная страница - Дашборд"""
    stats = await db.get_stats()
    agents = await db.get_all_agents_status()
    
    # Проверка живых агентов
    alive_agents = 0
    for agent in agents:
        if agent.last_heartbeat and \
           (datetime.now() - agent.last_heartbeat).total_seconds() < 60:
            alive_agents += 1
    
    # Конверсия
    funnel = stats.get('candidates_by_status', {})
    total = sum(funnel.values()) or 1
    
    context = {
        "request": request,
        "stats": stats,
        "alive_agents": alive_agents,
        "total_agents": 3,
        "funnel": funnel,
        "total_candidates": total,
    }
    
    return templates.TemplateResponse("dashboard.html", context)


@app.get("/candidates", response_class=HTMLResponse)
async def candidates_page(request: Request, status: Optional[str] = None, source: Optional[str] = None):
    """Страница кандидатов"""
    if status:
        candidates = await db.get_candidates_by_status(CandidateStatus(status))
    else:
        candidates = await db.get_all_candidates(limit=100)
    
    # Фильтр по источнику
    if source:
        candidates = [c for c in candidates if c.source == source]
    
    vacancies = await db.get_active_vacancies()
    
    context = {
        "request": request,
        "candidates": candidates,
        "vacancies": vacancies,
        "current_status": status,
        "current_source": source,
        "status_enum": CandidateStatus,
    }
    
    return templates.TemplateResponse("candidates.html", context)


@app.get("/vacancies", response_class=HTMLResponse)
async def vacancies_page(request: Request):
    """Страница вакансий"""
    vacancies = await db.get_active_vacancies()
    
    # Получаем количество кандидатов на каждую вакансию
    all_candidates = await db.get_all_candidates(limit=1000)
    vacancy_counts = {}
    for c in all_candidates:
        if c.vacancy_id:
            vacancy_counts[c.vacancy_id] = vacancy_counts.get(c.vacancy_id, 0) + 1
    
    context = {
        "request": request,
        "vacancies": vacancies,
        "vacancy_counts": vacancy_counts,
    }
    
    return templates.TemplateResponse("vacancies.html", context)


@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    """Страница аналитики"""
    stats = await db.get_stats()
    candidates = await db.get_all_candidates(limit=1000)
    
    # Статистика по источникам
    source_stats = stats.get('candidates_by_source', {})
    
    # Статистика по статусам
    status_stats = stats.get('candidates_by_status', {})
    
    # Конверсия
    funnel = status_stats
    total = sum(funnel.values()) or 1
    
    conversion_rates = {
        'new_to_contacted': round(funnel.get('contacted', 0) / max(funnel.get('new', 1), 1) * 100, 1),
        'contacted_to_qualified': round(funnel.get('qualified', 0) / max(funnel.get('contacted', 1), 1) * 100, 1),
        'qualified_to_interview': round(funnel.get('interview', 0) / max(funnel.get('qualified', 1), 1) * 100, 1),
        'interview_to_hired': round(funnel.get('hired', 0) / max(funnel.get('interview', 1), 1) * 100, 1),
    }
    
    # Активность по дням (последние 7 дней)
    daily_stats = {}
    for c in candidates:
        date = c.created_at.strftime('%Y-%m-%d')
        daily_stats[date] = daily_stats.get(date, 0) + 1
    
    # Сортируем по дате
    sorted_days = sorted(daily_stats.items())[-7:]
    
    context = {
        "request": request,
        "stats": stats,
        "source_stats": source_stats,
        "status_stats": status_stats,
        "conversion_rates": conversion_rates,
        "daily_stats": sorted_days,
        "total_candidates": sum(status_stats.values()),
    }
    
    return templates.TemplateResponse("analytics.html", context)


@app.get("/contacts", response_class=HTMLResponse)
async def contacts_page(request: Request):
    """Страница контактов"""
    # Получаем контакты из API (те же данные что и для Web App)
    contacts = [
        {
            "name": "Отдел кадров",
            "role": "Рекрутинг",
            "phone": "+7 (999) 123-45-67",
            "email": "hr@company.com"
        },
        {
            "name": "Менеджер по персоналу",
            "role": "Главный менеджер",
            "phone": "+7 (999) 765-43-21",
            "email": "manager@company.com"
        }
    ]
    
    context = {
        "request": request,
        "contacts": contacts,
    }

    return templates.TemplateResponse("contacts.html", context)


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Страница настроек"""
    from common import settings

    current_settings = {
        'telegram_bot_token': '***' + settings.telegram_bot_token[-5:] if settings.telegram_bot_token else '',
        'avito_client_id': settings.avito_client_id or '',
        'voximplant_account_id': settings.voximplant_account_id or '',
        'twilio_account_sid': settings.twilio_account_sid or '',
    }

    context = {
        "request": request,
        "settings": current_settings,
    }

    return templates.TemplateResponse("settings.html", context)


# ========== API Endpoints ==========

@app.get("/api/dashboard")
async def api_dashboard():
    """API: Данные дашборда"""
    stats = await db.get_stats()
    agents = await db.get_all_agents_status()
    
    alive_agents = 0
    for agent in agents:
        if agent.last_heartbeat and \
           (datetime.now() - agent.last_heartbeat).total_seconds() < 60:
            alive_agents += 1
    
    return {
        "stats": stats,
        "alive_agents": alive_agents,
        "total_agents": 3,
    }


@app.get("/api/candidates")
async def api_candidates(limit: int = 100, status: Optional[str] = None):
    """API: Список кандидатов"""
    if status:
        candidates = await db.get_candidates_by_status(CandidateStatus(status))
    else:
        candidates = await db.get_all_candidates(limit=limit)
    
    return {"candidates": [c.to_dict() for c in candidates]}


@app.get("/api/candidates/{candidate_id}")
async def api_candidate(candidate_id: str):
    """API: Кандидат по ID"""
    candidate = await db.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    interactions = await db.get_interactions(candidate_id)
    
    return {
        "candidate": candidate.to_dict(),
        "interactions": [i.to_dict() for i in interactions],
    }


@app.post("/api/candidates")
async def api_create_candidate(candidate_data: CandidateForm):
    """API: Создание кандидата"""
    candidate = Candidate(
        name=candidate_data.name,
        phone=candidate_data.phone,
        source=candidate_data.source,
        vacancy_id=candidate_data.vacancy_id,
        notes=candidate_data.notes or "",
    )

    await db.create_candidate(candidate)

    # Создаём задачу на звонок
    task = Task(
        agent_type=AgentType.VOICE,
        task_type="call_candidate",
        payload={
            "candidate_id": candidate.id,
            "phone": candidate.phone,
            "name": candidate.name,
        },
        priority=1
    )
    await db.create_task(task)

    # Отправляем уведомление в Telegram
    await send_telegram_notification(candidate)

    return {"id": candidate.id, "status": "created"}


async def send_telegram_notification(candidate):
    """Отправка уведомления в Telegram бот"""
    try:
        from common import settings
        import aiohttp
        
        bot_token = settings.telegram_bot_token
        admin_chat_id = settings.telegram_admin_chat_id
        
        if not bot_token:
            return
        
        # Если admin_chat_id не задан, пробуем получить его
        if not admin_chat_id:
            # Отправляем в бота - уведомления придут в бота
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            async with aiohttp.ClientSession() as session:
                await session.post(url, json={
                    "chat_id": bot_token.split(':')[0],
                    "text": "⚠️ Настройте TELEGRAM_ADMIN_CHAT_ID в .env для получения уведомлений",
                    "parse_mode": "HTML"
                })
            return
        
        # Формируем сообщение
        message = f"""
🔔 <b>Новый отклик!</b>

👤 <b>Имя:</b> {candidate.name}
📞 <b>Телефон:</b> {candidate.phone}
📋 <b>Источник:</b> {candidate.source}
📝 <b>Вакансия:</b> {candidate.vacancy_id[:30] + '...' if candidate.vacancy_id and len(candidate.vacancy_id) > 30 else candidate.vacancy_id or 'Не указана'}

🕐 <b>Время:</b> {candidate.created_at.strftime('%d.%m.%Y %H:%M')}
"""
        
        # Отправляем через Telegram API
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        async with aiohttp.ClientSession() as session:
            await session.post(url, json={
                "chat_id": admin_chat_id,
                "text": message,
                "parse_mode": "HTML"
            })
            
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")


@app.put("/api/candidates/{candidate_id}/status")
async def api_update_candidate_status(candidate_id: str, request: Request):
    """API: Обновление статуса кандидата"""
    try:
        body = await request.json()
        new_status = body.get('new_status')
    except:
        new_status = None
    
    if not new_status:
        raise HTTPException(status_code=400, detail="new_status required")
    
    try:
        status = CandidateStatus(new_status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")

    await db.update_candidate_status(candidate_id, status)

    return {"status": "updated"}


@app.delete("/api/candidates/{candidate_id}")
async def api_delete_candidate(candidate_id: str):
    """API: Удаление кандидата"""
    # В реальности нужно добавить метод в БД
    return {"status": "not_implemented"}


@app.get("/api/vacancies")
async def api_vacancies():
    """API: Список вакансий"""
    vacancies = await db.get_active_vacancies()
    return {"vacancies": [v.to_dict() for v in vacancies]}


@app.post("/api/vacancies")
async def api_create_vacancy(vacancy_data: VacancyForm):
    """API: Создание вакансии"""
    vacancy = Vacancy(
        title=vacancy_data.title,
        description=vacancy_data.description,
        salary_min=vacancy_data.salary_min,
        salary_max=vacancy_data.salary_max,
        requirements=vacancy_data.requirements or "",
        conditions=vacancy_data.conditions or "",
    )
    
    await db.create_vacancy(vacancy)
    
    return {"id": vacancy.id, "status": "created"}


@app.put("/api/vacancies/{vacancy_id}")
async def api_update_vacancy(vacancy_id: str, vacancy_data: VacancyForm):
    """API: Обновление вакансии"""
    vacancy = await db.get_vacancy(vacancy_id)
    if not vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    
    vacancy.title = vacancy_data.title
    vacancy.description = vacancy_data.description
    vacancy.salary_min = vacancy_data.salary_min
    vacancy.salary_max = vacancy_data.salary_max
    vacancy.requirements = vacancy_data.requirements or ""
    vacancy.conditions = vacancy_data.conditions or ""
    
    await db.update_vacancy(vacancy)
    
    return {"status": "updated"}


@app.delete("/api/vacancies/{vacancy_id}")
async def api_delete_vacancy(vacancy_id: str):
    """API: Удаление вакансии (деактивация)"""
    vacancy = await db.get_vacancy(vacancy_id)
    if not vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    
    vacancy.is_active = False
    await db.update_vacancy(vacancy)
    
    return {"status": "deleted"}


@app.get("/api/status")
async def api_status():
    """API: Статус системы"""
    agents = await db.get_all_agents_status()

    result = {}
    for agent in agents:
        is_alive = agent.last_heartbeat and \
                  (datetime.now() - agent.last_heartbeat).total_seconds() < 60

        result[agent.agent_type.value] = {
            "alive": is_alive,
            "last_heartbeat": agent.last_heartbeat.isoformat() if agent.last_heartbeat else None,
            "tasks_completed": agent.tasks_completed,
            "tasks_failed": agent.tasks_failed,
        }

    return {
        "orchestrator": "running",
        "agents": result,
    }


@app.get("/api/settings")
async def api_settings():
    """API: Настройки и контакты (синхронизировано с Web App)"""
    # Контакты - общие для всех интерфейсов
    contacts = [
        {
            "name": "Отдел кадров",
            "role": "Рекрутинг",
            "phone": "+7 (999) 123-45-67",
            "email": "hr@company.com"
        },
        {
            "name": "Менеджер по персоналу",
            "role": "Главный менеджер",
            "phone": "+7 (999) 765-43-21",
            "email": "manager@company.com"
        }
    ]
    return {
        "contacts": contacts,
        "company_name": "Recruitment System",
        "support_email": "support@company.com"
    }


# ========== Вспомогательные функции ==========

def status_to_emoji(status: str) -> str:
    """Эмодзи для статуса"""
    emojis = {
        "new": "🆕",
        "contacted": "📞",
        "qualified": "✅",
        "interview": "📅",
        "offer": "📋",
        "hired": "🎉",
        "rejected": "❌",
        "blacklist": "🚫",
    }
    return emojis.get(status, "❓")


def status_to_russian(status: str) -> str:
    """Перевод статуса"""
    translations = {
        "new": "Новый",
        "contacted": "Связались",
        "qualified": "Квалифицирован",
        "interview": "Собеседование",
        "offer": "Предложение",
        "hired": "Принят",
        "rejected": "Отказ",
        "blacklist": "Чёрный список",
    }
    return translations.get(status, status)

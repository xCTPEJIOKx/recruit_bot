"""
Orchestrator - Координатор работы всех агентов
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from common import db, AgentType, AgentStatus, Task, Candidate, CandidateStatus, Vacancy

logger = logging.getLogger(__name__)


class Orchestrator:
    """Координатор работы агентов"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self.app = FastAPI(title="Recruitment Orchestrator")
        self.is_running = False
        self._agent_statuses: Dict[AgentType, AgentStatus] = {}

        # CORS для Web App
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Монтирование статики для Web App
        static_dir = Path(__file__).parent.parent / "web_dashboard" / "static"
        if static_dir.exists():
            self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

        self._register_routes()
    
    def _register_routes(self):
        """Регистрация API routes"""
        
        @self.app.get("/")
        async def root():
            return {
                "service": "Recruitment Orchestrator",
                "status": "running" if self.is_running else "stopped",
                "version": "1.0.0"
            }
        
        @self.app.get("/health")
        async def health_check():
            """Проверка здоровья оркестратора"""
            return {"status": "healthy"}
        
        @self.app.get("/status")
        async def get_status():
            """Статус всех агентов"""
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
                    "last_error": agent.last_error,
                }
            
            return {
                "orchestrator": "running" if self.is_running else "stopped",
                "agents": result,
            }
        
        @self.app.get("/stats")
        async def get_stats():
            """Статистика системы"""
            stats = await db.get_stats()
            return stats
        
        @self.app.get("/candidates")
        async def get_candidates(limit: int = 100, status: Optional[str] = None):
            """Список кандидатов"""
            if status:
                candidates = await db.get_candidates_by_status(CandidateStatus(status))
            else:
                candidates = await db.get_all_candidates(limit)
            return {"candidates": [c.to_dict() for c in candidates]}
        
        @self.app.get("/candidates/{candidate_id}")
        async def get_candidate(candidate_id: str):
            """Кандидат по ID"""
            candidate = await db.get_candidate(candidate_id)
            if not candidate:
                raise HTTPException(status_code=404, detail="Candidate not found")
            return candidate.to_dict()
        
        @self.app.post("/candidates")
        async def create_candidate(candidate_data: dict):
            """Создание кандидата"""
            candidate = Candidate.from_dict(candidate_data)
            await db.create_candidate(candidate)
            return {"id": candidate.id, "status": "created"}
        
        @self.app.put("/candidates/{candidate_id}/status")
        async def update_candidate_status(candidate_id: str, new_status: str):
            """Обновление статуса кандидата"""
            try:
                status = CandidateStatus(new_status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")
            
            await db.update_candidate_status(candidate_id, status)
            return {"status": "updated"}
        
        @self.app.get("/vacancies")
        async def get_vacancies(active_only: bool = True):
            """Список вакансий"""
            if active_only:
                vacancies = await db.get_active_vacancies()
            else:
                # Все вакансии (нужно добавить метод в БД)
                vacancies = await db.get_active_vacancies()
            return {"vacancies": [v.to_dict() for v in vacancies]}
        
        @self.app.post("/vacancies")
        async def create_vacancy(vacancy_data: dict):
            """Создание вакансии"""
            vacancy = Vacancy.from_dict(vacancy_data)
            await db.create_vacancy(vacancy)
            return {"id": vacancy.id, "status": "created"}

        @self.app.put("/vacancies/{vacancy_id}")
        async def update_vacancy(vacancy_id: str, vacancy_data: dict):
            """Обновление вакансии"""
            vacancy = await db.get_vacancy(vacancy_id)
            if not vacancy:
                raise HTTPException(status_code=404, detail="Vacancy not found")

            vacancy.title = vacancy_data.get('title', vacancy.title)
            vacancy.description = vacancy_data.get('description', vacancy.description)
            vacancy.salary_min = vacancy_data.get('salary_min', vacancy.salary_min)
            vacancy.salary_max = vacancy_data.get('salary_max', vacancy.salary_max)
            vacancy.requirements = vacancy_data.get('requirements', vacancy.requirements)
            vacancy.conditions = vacancy_data.get('conditions', vacancy.conditions)

            await db.update_vacancy(vacancy)
            return {"status": "updated"}

        @self.app.delete("/vacancies/{vacancy_id}")
        async def delete_vacancy(vacancy_id: str):
            """Удаление вакансии (деактивация)"""
            vacancy = await db.get_vacancy(vacancy_id)
            if not vacancy:
                raise HTTPException(status_code=404, detail="Vacancy not found")

            vacancy.is_active = False
            await db.update_vacancy(vacancy)
            return {"status": "deleted"}
        
        @self.app.get("/tasks")
        async def get_tasks(agent_type: Optional[str] = None, status: Optional[str] = None):
            """Список задач"""
            # Упрощённая реализация
            return {"tasks": []}
        
        @self.app.post("/tasks")
        async def create_task(task_data: dict):
            """Создание задачи"""
            task = Task.from_dict(task_data)
            await db.create_task(task)
            return {"id": task.id, "status": "created"}
        
        @self.app.get("/interactions/{candidate_id}")
        async def get_interactions(candidate_id: str, limit: int = 50):
            """История взаимодействий с кандидатом"""
            interactions = await db.get_interactions(candidate_id, limit)
            return {"interactions": [i.to_dict() for i in interactions]}
        
        @self.app.post("/agents/{agent_type}/heartbeat")
        async def agent_heartbeat(agent_type: str, status: dict):
            """Получение heartbeat от агента"""
            try:
                agent_type_enum = AgentType(agent_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid agent type: {agent_type}")
            
            agent_status = AgentStatus(
                agent_type=agent_type_enum,
                is_alive=status.get("is_alive", True),
                last_heartbeat=datetime.now(),
                tasks_completed=status.get("tasks_completed", 0),
                tasks_failed=status.get("tasks_failed", 0),
                last_error=status.get("last_error", ""),
            )
            await db.update_agent_status(agent_status)
            
            return {"status": "ok"}
        
        @self.app.get("/dashboard")
        async def dashboard():
            """Данные для дашборда"""
            stats = await db.get_stats()
            agents = await db.get_all_agents_status()

            # Подсчитываем живых агентов
            alive_agents = 0
            for agent in agents:
                if agent.last_heartbeat and \
                   (datetime.now() - agent.last_heartbeat).total_seconds() < 60:
                    alive_agents += 1

            # Конверсия по воронке
            funnel = stats.get("candidates_by_status", {})
            total = sum(funnel.values()) or 1

            conversion = {
                "new_to_contacted": funnel.get("contacted", 0) / funnel.get("new", 1) if funnel.get("new") else 0,
                "contacted_to_qualified": funnel.get("qualified", 0) / funnel.get("contacted", 1) if funnel.get("contacted") else 0,
                "qualified_to_interview": funnel.get("interview", 0) / funnel.get("qualified", 1) if funnel.get("qualified") else 0,
                "interview_to_hired": funnel.get("hired", 0) / funnel.get("interview", 1) if funnel.get("interview") else 0,
            }

            return {
                "total_candidates": total,
                "active_vacancies": stats.get("active_vacancies", 0),
                "alive_agents": alive_agents,
                "funnel": funnel,
                "conversion": conversion,
                "total_interactions": stats.get("total_interactions", 0),
            }

        @self.app.get("/api/dashboard")
        async def api_dashboard():
            """API: Данные дашборда (для Web App и Dashboard)"""
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
                "total_agents": 4,
            }

        @self.app.get("/api/candidates")
        async def api_candidates(limit: int = 100, status: Optional[str] = None):
            """API: Список кандидатов"""
            if status:
                candidates = await db.get_candidates_by_status(CandidateStatus(status))
            else:
                candidates = await db.get_all_candidates(limit=limit)
            return {"candidates": [c.to_dict() for c in candidates]}

        @self.app.get("/api/vacancies")
        async def api_vacancies():
            """API: Список вакансий"""
            vacancies = await db.get_active_vacancies()
            return {"vacancies": [v.to_dict() for v in vacancies]}

        @self.app.post("/api/candidates")
        async def api_create_candidate(candidate_data: dict):
            """API: Создание кандидата"""
            candidate = Candidate.from_dict(candidate_data)
            await db.create_candidate(candidate)
            
            # Создаём задачу на звонок
            from common import AgentType, Task
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
            
            return {"id": candidate.id, "status": "created"}

        @self.app.put("/api/candidates/{candidate_id}/status")
        async def api_update_candidate_status(candidate_id: str, new_status: str):
            """API: Обновление статуса кандидата"""
            try:
                status = CandidateStatus(new_status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")
            await db.update_candidate_status(candidate_id, status)
            return {"status": "updated"}

        @self.app.get("/api/settings")
        async def api_settings():
            """API: Настройки и контакты (синхронизировано с Dashboard)"""
            # Контакты из настроек (можно хранить в БД или .env)
            from common import settings as app_settings
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

        @self.app.get("/api/avito/callback")
        async def avito_callback(code: str, error: Optional[str] = None):
            """OAuth callback от Avito"""
            import aiohttp
            from common import settings
            
            if error:
                return {"error": error}
            
            # Обмениваем code на токен
            token_url = "https://api.avito.ru/token"
            data = {
                "client_id": settings.avito_client_id,
                "client_secret": settings.avito_client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": f"https://{settings.webapp_url.replace('https://', '')}/api/avito/callback"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, data=data) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        return {
                            "success": True,
                            "message": "Токен получен! Добавьте в .env:",
                            "access_token": token_data.get("access_token", ""),
                            "refresh_token": token_data.get("refresh_token", "")
                        }
                    else:
                        return {"error": await response.text()}

    async def start(self):
        """Запуск оркестратора"""
        logger.info(f"🎯 Запуск Orchestrator на {self.host}:{self.port}...")

        self.is_running = True

        # Запускаем фоновые задачи
        asyncio.create_task(self._monitor_agents_loop())
        asyncio.create_task(self._distribute_tasks_loop())
        asyncio.create_task(self._cleanup_loop())

        # Запускаем HTTP сервер
        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info",
            access_log=False
        )
        server = uvicorn.Server(config)

        # Запускаем сервер в фоне
        asyncio.create_task(server.serve())

        # Ждём пока сервер запустится
        await asyncio.sleep(2)

        logger.info(f"✅ Orchestrator запущен. API доступен на http://{self.host}:{self.port}")
    
    async def stop(self):
        """Остановка оркестратора"""
        self.is_running = False
        logger.info("🛑 Orchestrator остановлен")
    
    async def _monitor_agents_loop(self):
        """Мониторинг здоровья агентов"""
        while self.is_running:
            try:
                await self._check_agents_health()
            except Exception as e:
                logger.error(f"Ошибка мониторинга агентов: {e}")
            await asyncio.sleep(30)  # Каждые 30 секунд
    
    async def _distribute_tasks_loop(self):
        """Распределение задач между агентами"""
        while self.is_running:
            try:
                await self._distribute_tasks()
            except Exception as e:
                logger.error(f"Ошибка распределения задач: {e}")
            await asyncio.sleep(10)  # Каждые 10 секунд
    
    async def _cleanup_loop(self):
        """Очистка старых данных"""
        while self.is_running:
            try:
                # Очистка будет реализована при необходимости
                pass
            except Exception as e:
                logger.error(f"Ошибка очистки: {e}")
            await asyncio.sleep(3600)  # Каждый час
    
    async def _check_agents_health(self):
        """Проверка здоровья агентов"""
        agents = await db.get_all_agents_status()
        
        for agent in agents:
            if not agent.last_heartbeat:
                logger.warning(f"⚠️ Агент {agent.agent_type.value} никогда не отправлял heartbeat")
                continue
            
            seconds_since_heartbeat = (datetime.now() - agent.last_heartbeat).total_seconds()
            
            if seconds_since_heartbeat > 60:
                logger.warning(f"⚠️ Агент {agent.agent_type.value} не отвечает ({seconds_since_heartbeat:.0f} сек)")
            else:
                logger.debug(f"✅ Агент {agent.agent_type.value} активен")
    
    async def _distribute_tasks(self):
        """
        Распределение задач между агентами
        В текущей реализации задачи создаются напрямую в БД
        """
        # Здесь можно добавить логику приоритизации
        # и балансировки нагрузки между агентами
        pass


# ========== Entry Point ==========

async def run_orchestrator(host: str = "0.0.0.0", port: int = 8000):
    """Запуск оркестратора"""
    from common import settings
    
    orchestrator = Orchestrator(
        host=settings.orchestrator_host if host == "0.0.0.0" else host,
        port=settings.orchestrator_port if port == 8000 else port
    )
    await orchestrator.start()
    
    # Держим оркестратор запущенным
    while orchestrator.is_running:
        await asyncio.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    async def main():
        await db.connect()
        try:
            await run_orchestrator()
        finally:
            await db.close()
    
    asyncio.run(main())

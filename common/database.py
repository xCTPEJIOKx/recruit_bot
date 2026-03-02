"""
Клиент базы данных (SQLite)
"""
import aiosqlite
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from .models import (
    Candidate, CandidateStatus,
    Vacancy,
    Interaction, InteractionType,
    Task,
    AgentStatus, AgentType
)
from .config import settings


class Database:
    """Асинхронный клиент для SQLite"""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.database_path_abs
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self):
        """Подключение к базе данных"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = await aiosqlite.connect(str(self.db_path))
        self._connection.row_factory = aiosqlite.Row
        await self._init_tables()
    
    async def close(self):
        """Закрытие подключения"""
        if self._connection:
            await self._connection.close()
    
    async def _init_tables(self):
        """Создание таблиц"""
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                id TEXT PRIMARY KEY,
                name TEXT,
                phone TEXT,
                telegram_id INTEGER,
                telegram_username TEXT,
                source TEXT DEFAULT 'unknown',
                status TEXT DEFAULT 'new',
                vacancy_id TEXT,
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS vacancies (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                salary_min INTEGER,
                salary_max INTEGER,
                requirements TEXT,
                conditions TEXT,
                is_active INTEGER DEFAULT 1,
                avito_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id TEXT PRIMARY KEY,
                candidate_id TEXT NOT NULL,
                agent_type TEXT NOT NULL,
                interaction_type TEXT NOT NULL,
                content TEXT,
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (candidate_id) REFERENCES candidates(id)
            )
        """)
        
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                agent_type TEXT NOT NULL,
                task_type TEXT NOT NULL,
                payload TEXT,
                priority INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                assigned_at TIMESTAMP,
                completed_at TIMESTAMP,
                result TEXT,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3
            )
        """)
        
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS agent_status (
                agent_type TEXT PRIMARY KEY,
                is_alive INTEGER DEFAULT 0,
                last_heartbeat TIMESTAMP,
                tasks_completed INTEGER DEFAULT 0,
                tasks_failed INTEGER DEFAULT 0,
                last_error TEXT
            )
        """)
        
        # Индексы для ускорения поиска
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status)
        """)
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_candidates_source ON candidates(source)
        """)
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)
        """)
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_interactions_candidate ON interactions(candidate_id)
        """)
        
        await self._connection.commit()
    
    # ========== Candidates ==========
    
    async def create_candidate(self, candidate: Candidate) -> Candidate:
        """Создание нового кандидата"""
        await self._connection.execute("""
            INSERT INTO candidates (id, name, phone, telegram_id, telegram_username, 
                                   source, status, vacancy_id, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            candidate.id, candidate.name, candidate.phone,
            candidate.telegram_id, candidate.telegram_username,
            candidate.source, candidate.status.value, candidate.vacancy_id,
            candidate.notes, candidate.created_at.isoformat(), candidate.updated_at.isoformat()
        ))
        await self._connection.commit()
        return candidate
    
    async def get_candidate(self, candidate_id: str) -> Optional[Candidate]:
        """Получение кандидата по ID"""
        async with self._connection.execute(
            "SELECT * FROM candidates WHERE id = ?", (candidate_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return Candidate.from_dict(dict(row))
        return None
    
    async def get_candidate_by_telegram(self, telegram_id: int) -> Optional[Candidate]:
        """Получение кандидата по Telegram ID"""
        async with self._connection.execute(
            "SELECT * FROM candidates WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return Candidate.from_dict(dict(row))
        return None
    
    async def update_candidate_status(self, candidate_id: str, status: CandidateStatus) -> bool:
        """Обновление статуса кандидата"""
        await self._connection.execute("""
            UPDATE candidates 
            SET status = ?, updated_at = ?
            WHERE id = ?
        """, (status.value, datetime.now().isoformat(), candidate_id))
        await self._connection.commit()
        return True
    
    async def update_candidate(self, candidate: Candidate) -> bool:
        """Обновление данных кандидата"""
        candidate.updated_at = datetime.now()
        await self._connection.execute("""
            UPDATE candidates 
            SET name = ?, phone = ?, telegram_id = ?, telegram_username = ?,
                source = ?, status = ?, vacancy_id = ?, notes = ?, updated_at = ?
            WHERE id = ?
        """, (
            candidate.name, candidate.phone, candidate.telegram_id,
            candidate.telegram_username, candidate.source, candidate.status.value,
            candidate.vacancy_id, candidate.notes, candidate.updated_at.isoformat(),
            candidate.id
        ))
        await self._connection.commit()
        return True
    
    async def get_candidates_by_status(self, status: CandidateStatus) -> List[Candidate]:
        """Получение кандидатов по статусу"""
        async with self._connection.execute(
            "SELECT * FROM candidates WHERE status = ? ORDER BY created_at DESC",
            (status.value,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [Candidate.from_dict(dict(row)) for row in rows]
    
    async def get_all_candidates(self, limit: int = 100) -> List[Candidate]:
        """Получение всех кандидатов (с лимитом)"""
        async with self._connection.execute(
            "SELECT * FROM candidates ORDER BY created_at DESC LIMIT ?", (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [Candidate.from_dict(dict(row)) for row in rows]
    
    # ========== Vacancies ==========
    
    async def create_vacancy(self, vacancy: Vacancy) -> Vacancy:
        """Создание вакансии"""
        await self._connection.execute("""
            INSERT INTO vacancies (id, title, description, salary_min, salary_max,
                                  requirements, conditions, is_active, avito_id,
                                  created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            vacancy.id, vacancy.title, vacancy.description,
            vacancy.salary_min, vacancy.salary_max,
            vacancy.requirements, vacancy.conditions,
            1 if vacancy.is_active else 0, vacancy.avito_id,
            vacancy.created_at.isoformat(), vacancy.updated_at.isoformat()
        ))
        await self._connection.commit()
        return vacancy
    
    async def get_vacancy(self, vacancy_id: str) -> Optional[Vacancy]:
        """Получение вакансии по ID"""
        async with self._connection.execute(
            "SELECT * FROM vacancies WHERE id = ?", (vacancy_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return Vacancy.from_dict(dict(row))
        return None
    
    async def get_active_vacancies(self) -> List[Vacancy]:
        """Получение активных вакансий"""
        async with self._connection.execute(
            "SELECT * FROM vacancies WHERE is_active = 1 ORDER BY created_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [Vacancy.from_dict(dict(row)) for row in rows]
    
    async def update_vacancy(self, vacancy: Vacancy) -> bool:
        """Обновление вакансии"""
        vacancy.updated_at = datetime.now()
        await self._connection.execute("""
            UPDATE vacancies 
            SET title = ?, description = ?, salary_min = ?, salary_max = ?,
                requirements = ?, conditions = ?, is_active = ?, avito_id = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            vacancy.title, vacancy.description, vacancy.salary_min,
            vacancy.salary_max, vacancy.requirements, vacancy.conditions,
            1 if vacancy.is_active else 0, vacancy.avito_id,
            vacancy.updated_at.isoformat(), vacancy.id
        ))
        await self._connection.commit()
        return True
    
    # ========== Interactions ==========
    
    async def log_interaction(self, interaction: Interaction) -> Interaction:
        """Логирование взаимодействия"""
        await self._connection.execute("""
            INSERT INTO interactions (id, candidate_id, agent_type, interaction_type,
                                     content, result, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            interaction.id, interaction.candidate_id,
            interaction.agent_type.value, interaction.interaction_type.value,
            interaction.content, interaction.result, interaction.created_at.isoformat()
        ))
        await self._connection.commit()
        return interaction
    
    async def get_interactions(self, candidate_id: str, limit: int = 50) -> List[Interaction]:
        """Получение истории взаимодействий с кандидатом"""
        async with self._connection.execute(
            """SELECT * FROM interactions 
               WHERE candidate_id = ? 
               ORDER BY created_at DESC LIMIT ?""",
            (candidate_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [Interaction.from_dict(dict(row)) for row in rows]
    
    # ========== Tasks ==========
    
    async def create_task(self, task: Task) -> Task:
        """Создание задачи"""
        import json
        await self._connection.execute("""
            INSERT INTO tasks (id, agent_type, task_type, payload, priority,
                              status, assigned_at, completed_at, result,
                              retry_count, max_retries)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task.id, task.agent_type.value, task.task_type,
            json.dumps(task.payload), task.priority, task.status,
            task.assigned_at.isoformat() if task.assigned_at else None,
            task.completed_at.isoformat() if task.completed_at else None,
            task.result, task.retry_count, task.max_retries
        ))
        await self._connection.commit()
        return task
    
    async def get_pending_tasks(self, agent_type: AgentType, limit: int = 10) -> List[Task]:
        """Получение pending задач для агента"""
        import json
        async with self._connection.execute(
            """SELECT * FROM tasks 
               WHERE agent_type = ? AND status = 'pending'
               ORDER BY priority ASC, id ASC
               LIMIT ?""",
            (agent_type.value, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [Task.from_dict(dict(row)) for row in rows]
    
    async def update_task(self, task: Task) -> bool:
        """Обновление задачи"""
        import json
        await self._connection.execute("""
            UPDATE tasks 
            SET status = ?, assigned_at = ?, completed_at = ?, result = ?,
                retry_count = ?
            WHERE id = ?
        """, (
            task.status,
            task.assigned_at.isoformat() if task.assigned_at else None,
            task.completed_at.isoformat() if task.completed_at else None,
            task.result, task.retry_count, task.id
        ))
        await self._connection.commit()
        return True
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Получение задачи по ID"""
        import json
        async with self._connection.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return Task.from_dict(dict(row))
        return None
    
    # ========== Agent Status ==========
    
    async def update_agent_status(self, status: AgentStatus) -> bool:
        """Обновление статуса агента"""
        await self._connection.execute("""
            INSERT OR REPLACE INTO agent_status 
            (agent_type, is_alive, last_heartbeat, tasks_completed, tasks_failed, last_error)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            status.agent_type.value,
            1 if status.is_alive else 0,
            status.last_heartbeat.isoformat() if status.last_heartbeat else None,
            status.tasks_completed, status.tasks_failed, status.last_error
        ))
        await self._connection.commit()
        return True
    
    async def get_agent_status(self, agent_type: AgentType) -> Optional[AgentStatus]:
        """Получение статуса агента"""
        async with self._connection.execute(
            "SELECT * FROM agent_status WHERE agent_type = ?", (agent_type.value,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return AgentStatus.from_dict(dict(row))
        return None
    
    async def get_all_agents_status(self) -> List[AgentStatus]:
        """Получение статусов всех агентов"""
        async with self._connection.execute(
            "SELECT * FROM agent_status"
        ) as cursor:
            rows = await cursor.fetchall()
            return [AgentStatus.from_dict(dict(row)) for row in rows]
    
    # ========== Stats ==========
    
    async def get_stats(self) -> dict:
        """Получение общей статистики"""
        # Количество кандидатов по статусам
        cursor = await self._connection.execute("""
            SELECT status, COUNT(*) as count 
            FROM candidates 
            GROUP BY status
        """)
        status_counts = {row["status"]: row["count"] for row in await cursor.fetchall()}
        
        # Количество кандидатов по источникам
        cursor = await self._connection.execute("""
            SELECT source, COUNT(*) as count 
            FROM candidates 
            GROUP BY source
        """)
        source_counts = {row["source"]: row["count"] for row in await cursor.fetchall()}
        
        # Всего вакансий
        cursor = await self._connection.execute("SELECT COUNT(*) as count FROM vacancies")
        total_vacancies = (await cursor.fetchone())["count"]
        
        # Активных вакансий
        cursor = await self._connection.execute(
            "SELECT COUNT(*) as count FROM vacancies WHERE is_active = 1"
        )
        active_vacancies = (await cursor.fetchone())["count"]
        
        # Всего взаимодействий
        cursor = await self._connection.execute("SELECT COUNT(*) as count FROM interactions")
        total_interactions = (await cursor.fetchone())["count"]
        
        return {
            "candidates_by_status": status_counts,
            "candidates_by_source": source_counts,
            "total_vacancies": total_vacancies,
            "active_vacancies": active_vacancies,
            "total_interactions": total_interactions,
        }


# Глобальный экземпляр БД
db = Database()


async def get_db() -> Database:
    """Получить подключение к БД (для dependency injection)"""
    return db

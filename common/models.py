"""
Модели данных для системы рекрутинга
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class CandidateStatus(str, Enum):
    """Статусы кандидата в воронке"""
    NEW = "new"  # Новый отклик
    CONTACTED = "contacted"  # Связались
    QUALIFIED = "qualified"  # Квалифицирован
    INTERVIEW = "interview"  # Назначено собеседование
    OFFER = "offer"  # Предложение сделано
    HIRED = "hired"  # Принят
    REJECTED = "rejected"  # Отказ
    BLACKLIST = "blacklist"  # Чёрный список


class AgentType(str, Enum):
    """Типы агентов"""
    AVITO = "avito"
    VOICE = "voice"
    TELEGRAM = "telegram"
    ORCHESTRATOR = "orchestrator"
    CLASSIFIEDS = "classifieds"


class InteractionType(str, Enum):
    """Типы взаимодействий"""
    MESSAGE_RECEIVED = "message_received"
    MESSAGE_SENT = "message_sent"
    CALL_MADE = "call_made"
    CALL_RECEIVED = "call_received"
    AVITO_RESPONSE = "avito_response"
    STATUS_CHANGED = "status_changed"
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"


@dataclass
class Candidate:
    """Кандидат на вакансию"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    phone: Optional[str] = None
    telegram_id: Optional[int] = None
    telegram_username: Optional[str] = None
    source: str = "unknown"  # avito, telegram, voice, etc.
    status: CandidateStatus = CandidateStatus.NEW
    vacancy_id: Optional[str] = None
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "telegram_id": self.telegram_id,
            "telegram_username": self.telegram_username,
            "source": self.source,
            "status": self.status.value,
            "vacancy_id": self.vacancy_id,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Candidate":
        return cls(
            id=data["id"],
            name=data.get("name"),
            phone=data.get("phone"),
            telegram_id=data.get("telegram_id"),
            telegram_username=data.get("telegram_username"),
            source=data.get("source", "unknown"),
            status=CandidateStatus(data.get("status", "new")),
            vacancy_id=data.get("vacancy_id"),
            notes=data.get("notes", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
        )


@dataclass
class Vacancy:
    """Вакансия"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    requirements: str = ""
    conditions: str = ""
    is_active: bool = True
    avito_id: Optional[str] = None  # ID объявления на Avito
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "requirements": self.requirements,
            "conditions": self.conditions,
            "is_active": self.is_active,
            "avito_id": self.avito_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Vacancy":
        return cls(
            id=data["id"],
            title=data.get("title", ""),
            description=data.get("description", ""),
            salary_min=data.get("salary_min"),
            salary_max=data.get("salary_max"),
            requirements=data.get("requirements", ""),
            conditions=data.get("conditions", ""),
            is_active=data.get("is_active", True),
            avito_id=data.get("avito_id"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
        )


@dataclass
class Interaction:
    """Взаимодействие с кандидатом"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    candidate_id: str = ""
    agent_type: AgentType = AgentType.TELEGRAM
    interaction_type: InteractionType = InteractionType.MESSAGE_SENT
    content: str = ""
    result: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "candidate_id": self.candidate_id,
            "agent_type": self.agent_type.value,
            "interaction_type": self.interaction_type.value,
            "content": self.content,
            "result": self.result,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Interaction":
        return cls(
            id=data["id"],
            candidate_id=data["candidate_id"],
            agent_type=AgentType(data["agent_type"]),
            interaction_type=InteractionType(data["interaction_type"]),
            content=data.get("content", ""),
            result=data.get("result", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
        )


@dataclass
class Task:
    """Задача для агента"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_type: AgentType = AgentType.TELEGRAM
    task_type: str = ""  # call_candidate, send_message, publish_vacancy, etc.
    payload: dict = field(default_factory=dict)
    priority: int = 0  # 0 - highest
    status: str = "pending"  # pending, in_progress, completed, failed
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: str = ""
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent_type": self.agent_type.value,
            "task_type": self.task_type,
            "payload": self.payload,
            "priority": self.priority,
            "status": self.status,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            id=data["id"],
            agent_type=AgentType(data["agent_type"]),
            task_type=data.get("task_type", ""),
            payload=data.get("payload", {}),
            priority=data.get("priority", 0),
            status=data.get("status", "pending"),
            assigned_at=datetime.fromisoformat(data["assigned_at"]) if data.get("assigned_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            result=data.get("result", ""),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
        )


@dataclass
class AgentStatus:
    """Статус агента"""
    agent_type: AgentType
    is_alive: bool = False
    last_heartbeat: Optional[datetime] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    last_error: str = ""
    
    def to_dict(self) -> dict:
        return {
            "agent_type": self.agent_type.value,
            "is_alive": self.is_alive,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "last_error": self.last_error,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "AgentStatus":
        return cls(
            agent_type=AgentType(data["agent_type"]),
            is_alive=data.get("is_alive", False),
            last_heartbeat=datetime.fromisoformat(data["last_heartbeat"]) if data.get("last_heartbeat") else None,
            tasks_completed=data.get("tasks_completed", 0),
            tasks_failed=data.get("tasks_failed", 0),
            last_error=data.get("last_error", ""),
        )

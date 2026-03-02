"""
Общие модули для системы рекрутинговых агентов
"""
from .config import settings, get_settings
from .database import db, get_db
from .models import (
    Candidate, CandidateStatus,
    Vacancy,
    Interaction, InteractionType,
    Task,
    AgentStatus, AgentType
)

__all__ = [
    "settings",
    "get_settings",
    "db",
    "get_db",
    "Candidate",
    "CandidateStatus",
    "Vacancy",
    "Interaction",
    "InteractionType",
    "Task",
    "AgentStatus",
    "AgentType",
]

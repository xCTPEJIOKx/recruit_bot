"""
Конфигурация системы рекрутинговых агентов
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Telegram
    telegram_bot_token: str = ""

    # Avito (для браузерной автоматизации)
    avito_login: str = ""  # Логин от Avito (телефон или email)
    avito_password: str = ""  # Пароль от Avito

    # Avito API
    avito_client_id: Optional[str] = None
    avito_client_secret: Optional[str] = None
    avito_access_token: Optional[str] = None
    avito_refresh_token: Optional[str] = None
    avito_redirect_uri: Optional[str] = None
    
    # Telephony - Voximplant
    voximplant_account_id: Optional[str] = None
    voximplant_api_key: Optional[str] = None
    voximplant_phone_number: Optional[str] = None
    
    # Telephony - Twilio
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    
    # Database
    database_path: str = "./data/recruitment.db"
    
    # Orchestrator
    orchestrator_host: str = "0.0.0.0"
    orchestrator_port: int = 8000

    # Web App URL (для Telegram)
    webapp_url: str = "http://localhost:8080"

    # Logging
    log_level: str = "INFO"
    
    # Debug mode
    debug: bool = False
    
    # Project root
    project_root: Path = Path(__file__).parent.parent
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def database_path_abs(self) -> Path:
        """Абсолютный путь к базе данных"""
        path = Path(self.database_path)
        if not path.is_absolute():
            path = self.project_root / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return path


# Глобальный экземпляр настроек
settings = Settings()


def get_settings() -> Settings:
    """Получить настройки (для dependency injection)"""
    return settings

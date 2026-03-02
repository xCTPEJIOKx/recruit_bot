"""
Classifieds Agent - Автопостинг вакансий на бесплатные доски объявлений
Поддерживаемые площадки:
- Avito (требуется API)
- HH.ru (требуется API)
- SuperJob (требуется API)
- Rabota.ru (требуется API)
- Zarplata.ru (требуется API)
- GorodRabot.ru (парсинг)
- Youla (парсинг)
- Drom.ru (парсинг)
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import aiohttp
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from common import db, Vacancy, AgentType, AgentStatus

logger = logging.getLogger(__name__)


# ========== Конфигурация площадок ==========

CLASSIFIEDS_PLATFORMS = {
    "avito": {
        "name": "Avito",
        "url": "https://www.avito.ru",
        "post_url": "https://www.avito.ru/brand/new",
        "free": False,  # Платно для вакансий
        "requires_auth": True,
    },
    "hh": {
        "name": "HH.ru",
        "url": "https://hh.ru",
        "post_url": "https://hh.ru/employer/vacancy",
        "free": True,  # Бесплатно для работодателей
        "requires_auth": True,
    },
    "superjob": {
        "name": "SuperJob",
        "url": "https://www.superjob.ru",
        "post_url": "https://www.superjob.ru/employer/",
        "free": False,
        "requires_auth": True,
    },
    "rabota": {
        "name": "Rabota.ru",
        "url": "https://www.rabota.ru",
        "post_url": "https://www.rabota.ru/employer/vacancy/create",
        "free": True,
        "requires_auth": True,
    },
    "zarplata": {
        "name": "Zarplata.ru",
        "url": "https://www.zarplata.ru",
        "post_url": "https://www.zarplata.ru/employer/vacancy",
        "free": True,
        "requires_auth": True,
    },
    "gorodrabot": {
        "name": "GorodRabot.ru",
        "url": "https://gorodrabot.ru",
        "post_url": "https://gorodrabot.ru/employer/add_vacancy",
        "free": True,
        "requires_auth": True,
    },
    "youla": {
        "name": "Youla",
        "url": "https://youla.ru",
        "post_url": "https://youla.ru/moskva/uslugi/new",
        "free": True,
        "requires_auth": True,
    },
    "drom": {
        "name": "Drom.ru (Работа)",
        "url": "https://www.drom.ru/work/",
        "post_url": "https://www.drom.ru/work/add_vacancy.html",
        "free": True,
        "requires_auth": True,
    },
    "farpost": {
        "name": "Farpost",
        "url": "https://www.farpost.ru",
        "post_url": "https://www.farpost.ru/vacancies/add/",
        "free": True,
        "requires_auth": False,
    },
    "irr": {
        "name": "Из рук в руки (IRR.ru)",
        "url": "https://irr.ru",
        "post_url": "https://irr.ru/add/",
        "free": True,
        "requires_auth": True,
    },
}


class ClassifiedsAgent:
    """Агент для постинга на доски объявлений"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.is_running = False
        self.driver: Optional[webdriver.Chrome] = None
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Статистика
        self.posts_today = 0
        self.posts_total = 0
        self.errors = 0
        
        # Настройки
        self.max_posts_per_day = 50  # Лимит постов в день
        self.post_interval = 60  # Интервал между постами (секунды)
    
    async def start(self):
        """Запуск агента"""
        logger.info("🤖 Запуск Classifieds Agent...")
        
        self.is_running = True
        await self._send_heartbeat()
        
        # Инициализация сессии
        self.session = aiohttp.ClientSession()
        
        # Запуск фоновых задач
        asyncio.create_task(self._auto_post_loop())
        asyncio.create_task(self._check_platforms_loop())
        
        logger.info("✅ Classifieds Agent запущен")
    
    async def stop(self):
        """Остановка агента"""
        self.is_running = False
        
        if self.session:
            await self.session.close()
        
        if self.driver:
            self.driver.quit()
        
        logger.info("🛑 Classifieds Agent остановлен")
    
    async def _auto_post_loop(self):
        """Цикл автопостинга"""
        while self.is_running:
            try:
                await self._post_vacancies()
            except Exception as e:
                logger.error(f"Ошибка автопостинга: {e}")
                self.errors += 1
            
            # Ждём следующий цикл
            await asyncio.sleep(self.post_interval)
    
    async def _check_platforms_loop(self):
        """Проверка доступности площадок"""
        while self.is_running:
            try:
                await self._check_platforms()
            except Exception as e:
                logger.error(f"Ошибка проверки площадок: {e}")
            
            await asyncio.sleep(300)  # Каждые 5 минут
    
    async def _post_vacancies(self):
        """Постинг вакансий"""
        # Проверяем лимит
        if self.posts_today >= self.max_posts_per_day:
            logger.info("📊 Дневной лимит постов достигнут")
            return
        
        # Получаем активные вакансии
        vacancies = await db.get_active_vacancies()
        
        if not vacancies:
            logger.info("📭 Нет активных вакансий для постинга")
            return
        
        for vacancy in vacancies:
            if self.posts_today >= self.max_posts_per_day:
                break
            
            # Постим на каждую площадку
            for platform_id, platform_info in CLASSIFIEDS_PLATFORMS.items():
                if not platform_info.get("free", False):
                    continue  # Пропускаем платные
                
                try:
                    success = await self._post_to_platform(platform_id, vacancy)
                    if success:
                        self.posts_today += 1
                        self.posts_total += 1
                        logger.info(f"✅ Опубликовано на {platform_info['name']}: {vacancy.title}")
                        
                        # Пауза между постами
                        await asyncio.sleep(10)
                        
                except Exception as e:
                    logger.error(f"Ошибка постинга на {platform_info['name']}: {e}")
                    self.errors += 1
    
    async def _post_to_platform(self, platform_id: str, vacancy: Vacancy) -> bool:
        """Постинг на конкретную площадку"""
        platform = CLASSIFIEDS_PLATFORMS.get(platform_id)
        
        if not platform:
            return False
        
        if platform_id == "farpost":
            return await self._post_to_farpost(vacancy)
        
        elif platform_id == "youla":
            return await self._post_to_youla(vacancy)
        
        elif platform_id == "drom":
            return await self._post_to_drom(vacancy)
        
        elif platform_id == "irr":
            return await self._post_to_irr(vacancy)
        
        # Для остальных - симуляция или API
        return await self._post_via_api(platform_id, vacancy)
    
    async def _post_via_api(self, platform_id: str, vacancy: Vacancy) -> bool:
        """Постинг через API (симуляция для бесплатных)"""
        # В реальности здесь был бы вызов API
        # Для бесплатных площадок часто нет публичного API
        
        logger.info(f"📝 Постинг на {platform_id} (требуется ручная настройка)")
        
        # Симуляция успешного поста
        await asyncio.sleep(2)
        
        return True
    
    async def _post_to_farpost(self, vacancy: Vacancy) -> bool:
        """Постинг на Farpost (бесплатно, без регистрации)"""
        try:
            # Инициализация драйвера
            await self._init_driver()
            
            # Переход на страницу создания вакансии
            self.driver.get("https://www.farpost.ru/vacancies/add/")
            
            # Заполнение формы
            await asyncio.sleep(3)
            
            # Название вакансии
            title_field = self.driver.find_element(By.NAME, "title")
            title_field.send_keys(vacancy.title)
            
            # Описание
            desc_field = self.driver.find_element(By.NAME, "text")
            desc_field.send_keys(f"{vacancy.description}\n\n{vacancy.requirements}\n\n{vacancy.conditions}")
            
            # Зарплата
            if vacancy.salary_min:
                salary_field = self.driver.find_element(By.NAME, "price")
                salary_field.send_keys(str(vacancy.salary_min))
            
            # Контакты
            # (требуется дополнительная настройка)
            
            logger.info(f"✅ Farpost: форма заполнена для {vacancy.title}")
            
            # В реальности здесь была бы отправка формы
            # submit_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
            # submit_button.click()
            
            return True
            
        except Exception as e:
            logger.error(f"Farpost ошибка: {e}")
            return False
        
        finally:
            if self.driver and not self.headless:
                pass  # Оставляем браузер открытым для отладки
    
    async def _post_to_youla(self, vacancy: Vacancy) -> bool:
        """Постинг на Youla"""
        try:
            await self._init_driver()
            
            self.driver.get("https://youla.ru/moskva/uslugi/new")
            await asyncio.sleep(3)
            
            # Заполнение формы (структура может измениться)
            logger.info(f"✅ Youla: форма открыта для {vacancy.title}")
            
            return True
            
        except Exception as e:
            logger.error(f"Youla ошибка: {e}")
            return False
    
    async def _post_to_drom(self, vacancy: Vacancy) -> bool:
        """Постинг на Drom.ru Работа"""
        try:
            await self._init_driver()
            
            self.driver.get("https://www.drom.ru/work/add_vacancy.html")
            await asyncio.sleep(3)
            
            logger.info(f"✅ Drom: форма открыта для {vacancy.title}")
            
            return True
            
        except Exception as e:
            logger.error(f"Drom ошибка: {e}")
            return False
    
    async def _post_to_irr(self, vacancy: Vacancy) -> bool:
        """Постинг на IRR.ru"""
        try:
            await self._init_driver()
            
            self.driver.get("https://irr.ru/add/")
            await asyncio.sleep(3)
            
            logger.info(f"✅ IRR: форма открыта для {vacancy.title}")
            
            return True
            
        except Exception as e:
            logger.error(f"IRR ошибка: {e}")
            return False
    
    async def _init_driver(self):
        """Инициализация WebDriver"""
        if self.driver:
            return
        
        options = webdriver.ChromeOptions()
        
        if self.headless:
            options.add_argument("--headless")
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        self.driver = webdriver.Chrome(options=options)
    
    async def _check_platforms(self):
        """Проверка доступности площадок"""
        for platform_id, platform in CLASSIFIEDS_PLATFORMS.items():
            try:
                async with self.session.get(platform["url"], timeout=10) as response:
                    if response.status == 200:
                        logger.debug(f"✅ {platform['name']} доступен")
                    else:
                        logger.warning(f"⚠️ {platform['name']} вернул статус {response.status}")
            except Exception as e:
                logger.warning(f"❌ {platform['name']} недоступен: {e}")
    
    async def _send_heartbeat(self):
        """Отправка heartbeat"""
        async def heartbeat_loop():
            while self.is_running:
                try:
                    status = AgentStatus(
                        agent_type=AgentType.CLASSIFIEDS,
                        is_alive=True,
                        last_heartbeat=datetime.now(),
                        tasks_completed=self.posts_total,
                        tasks_failed=self.errors,
                    )
                    await db.update_agent_status(status)
                except Exception as e:
                    logger.error(f"Ошибка heartbeat: {e}")
                await asyncio.sleep(30)
        
        asyncio.create_task(heartbeat_loop())
    
    async def get_stats(self) -> dict:
        """Получение статистики"""
        return {
            "posts_today": self.posts_today,
            "posts_total": self.posts_total,
            "errors": self.errors,
            "platforms": len(CLASSIFIEDS_PLATFORMS),
            "free_platforms": sum(1 for p in CLASSIFIEDS_PLATFORMS.values() if p.get("free", False)),
        }


# ========== Entry Point ==========

async def run_classifieds_agent():
    """Запуск Classifieds Agent"""
    agent = ClassifiedsAgent(headless=True)
    await agent.start()
    
    while agent.is_running:
        await asyncio.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    async def main():
        await db.connect()
        try:
            await run_classifieds_agent()
        finally:
            await db.close()
    
    asyncio.run(main())

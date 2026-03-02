"""
Avito Agent - Публикация вакансий и обработка откликов
Полноценная интеграция с Avito API
"""
import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import aiohttp
from urllib.parse import urlencode

from common import db, Candidate, CandidateStatus, Interaction, InteractionType, AgentType, AgentStatus, Vacancy

logger = logging.getLogger(__name__)


class AvitoAPI:
    """Клиент для Avito API"""
    
    BASE_URL = "https://api.avito.ru"
    TOKEN_URL = "https://api.avito.ru/oauth/token"
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._token_expires: Optional[datetime] = None
    
    async def get_access_token(self, auth_code: str, redirect_uri: str) -> dict:
        """Получение access token из auth code"""
        data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': redirect_uri,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.TOKEN_URL, data=data) as response:
                result = await response.json()
                
                if response.status == 200:
                    self._access_token = result['access_token']
                    self._refresh_token = result.get('refresh_token')
                    expires_in = result.get('expires_in', 86400)
                    self._token_expires = datetime.now() + timedelta(seconds=expires_in)
                    logger.info("✅ Access token получен")
                    return result
                else:
                    logger.error(f"❌ Ошибка получения токена: {result}")
                    raise Exception(f"OAuth error: {result.get('error', 'Unknown')}")
    
    async def refresh_access_token(self) -> dict:
        """Обновление access token через refresh token"""
        if not self._refresh_token:
            raise Exception("No refresh token available")
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self._refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.TOKEN_URL, data=data) as response:
                result = await response.json()
                
                if response.status == 200:
                    self._access_token = result['access_token']
                    self._refresh_token = result.get('refresh_token', self._refresh_token)
                    expires_in = result.get('expires_in', 86400)
                    self._token_expires = datetime.now() + timedelta(seconds=expires_in)
                    logger.info("✅ Access token обновлён")
                    return result
                else:
                    logger.error(f"❌ Ошибка обновления токена: {result}")
                    raise Exception(f"Token refresh error: {result.get('error', 'Unknown')}")
    
    async def _get_valid_token(self) -> Optional[str]:
        """Получение валидного токена"""
        if self._access_token:
            if self._token_expires and datetime.now() < self._token_expires:
                return self._access_token
            elif self._refresh_token:
                try:
                    await self.refresh_access_token()
                    return self._access_token
                except Exception as e:
                    logger.error(f"Ошибка обновления токена: {e}")
                    return None
        return None
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None
    ) -> Optional[dict]:
        """HTTP запрос к API"""
        token = await self._get_valid_token()
        if not token:
            logger.warning("⚠️ Нет валидного токена")
            return None
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }
        
        url = f"{self.BASE_URL}{endpoint}"
        if params:
            url += f"?{urlencode(params)}"
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                url,
                headers=headers,
                json=json_data
            ) as response:
                if response.status == 401:
                    # Токен истёк, пробуем обновить
                    await self.refresh_access_token()
                    return await self._request(method, endpoint, params, json_data)
                
                if response.status in [200, 201]:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"❌ API error {response.status}: {error_text}")
                    return None
    
    # ========== Вакансии ==========
    
    async def get_vacancies(self, limit: int = 100) -> List[dict]:
        """Получение списка вакансий"""
        params = {'limit': limit}
        result = await self._request('GET', '/autorus/v1/vacancies', params)
        if result:
            return result.get('vacancies', [])
        return []
    
    async def get_vacancy(self, vacancy_id: str) -> Optional[dict]:
        """Получение вакансии по ID"""
        result = await self._request('GET', f'/autorus/v1/vacancies/{vacancy_id}')
        return result
    
    async def create_vacancy(self, vacancy_data: dict) -> Optional[str]:
        """
        Создание вакансии
        Возвращает ID созданной вакансии
        """
        # Форматирование данных под Avito API
        avito_vacancy = {
            'title': vacancy_data.get('title', ''),
            'description': vacancy_data.get('description', ''),
            'salary': {
                'min': vacancy_data.get('salary_min'),
                'max': vacancy_data.get('salary_max'),
                'currency': 'RUB',
                'type': 'gross'
            } if vacancy_data.get('salary_min') or vacancy_data.get('salary_max') else None,
            'employment': vacancy_data.get('employment', 'full'),
            'workplace': vacancy_data.get('workplace', 'office'),
            'city': vacancy_data.get('city', 'Москва'),
            'contact': {
                'name': vacancy_data.get('contact_name', 'HR Отдел'),
                'phone': vacancy_data.get('contact_phone', '+79990000000')
            }
        }
        
        # Удаляем None значения
        avito_vacancy = {k: v for k, v in avito_vacancy.items() if v is not None}
        if 'salary' in avito_vacancy:
            avito_vacancy['salary'] = {k: v for k, v in avito_vacancy['salary'].items() if v is not None}
        
        result = await self._request('POST', '/autorus/v1/vacancies', json_data=avito_vacancy)
        
        if result:
            vacancy_id = result.get('id') or result.get('vacancy_id')
            logger.info(f"✅ Вакансия создана: {vacancy_id}")
            return vacancy_id
        
        return None
    
    async def update_vacancy(self, vacancy_id: str, vacancy_data: dict) -> bool:
        """Обновление вакансии"""
        result = await self._request(
            'PUT',
            f'/autorus/v1/vacancies/{vacancy_id}',
            json_data=vacancy_data
        )
        return result is not None
    
    async def delete_vacancy(self, vacancy_id: str) -> bool:
        """Удаление вакансии"""
        result = await self._request('DELETE', f'/autorus/v1/vacancies/{vacancy_id}')
        return result is not None
    
    # ========== Отклики ==========
    
    async def get_responses(self, vacancy_id: str, limit: int = 100) -> List[dict]:
        """Получение откликов на вакансию"""
        params = {'limit': limit}
        result = await self._request(
            'GET',
            f'/autorus/v1/vacancies/{vacancy_id}/responses',
            params
        )
        if result:
            return result.get('responses', [])
        return []
    
    async def get_response(self, response_id: str) -> Optional[dict]:
        """Получение деталей отклика"""
        result = await self._request('GET', f'/autorus/v1/responses/{response_id}')
        return result
    
    async def send_message(
        self,
        response_id: str,
        message: str,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """Отправка сообщения кандидату"""
        data = {
            'message': message,
            'attachments': attachments or []
        }
        result = await self._request(
            'POST',
            f'/autorus/v1/responses/{response_id}/message',
            json_data=data
        )
        return result is not None
    
    # ========== Пользователь ==========
    
    async def get_user_info(self) -> Optional[dict]:
        """Получение информации о пользователе"""
        result = await self._request('GET', '/user')
        return result


class AvitoAgent:
    """Агент для работы с Avito"""
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token = access_token
        self._refresh_token = refresh_token
        self.api: Optional[AvitoAPI] = None
        self.is_running = False
        self._processed_responses: set = set()  # Уже обработанные отклики
    
    async def start(self):
        """Запуск агента"""
        logger.info("🤖 Запуск Avito агента...")
        
        # Инициализация API
        if self.client_id and self.client_secret:
            self.api = AvitoAPI(
                self.client_id,
                self.client_secret,
                access_token=self._access_token,
                refresh_token=self._refresh_token
            )
            
            # Проверяем токен
            user_info = await self.api.get_user_info()
            if user_info:
                logger.info(f"✅ Avito API инициализирован: {user_info.get('name', 'User')}")
            else:
                logger.warning("⚠️ Avito API: не удалось получить информацию о пользователе")
        else:
            logger.warning("⚠️ Avito API креды не настроены. Работа в режиме симуляции.")
            logger.info("📝 Для реальных откликов настройте Avito API (см. AVITO_SETUP.md)")
        
        self.is_running = True
        await self._send_heartbeat()
        
        # Запускаем фоновые задачи
        asyncio.create_task(self._check_responses_loop())
        asyncio.create_task(self._publish_vacancies_loop())
        asyncio.create_task(self._sync_vacancies_loop())
    
    async def stop(self):
        """Остановка агента"""
        self.is_running = False
        logger.info("🛑 Avito агент остановлен")
    
    async def _check_responses_loop(self):
        """Периодическая проверка откликов"""
        while self.is_running:
            try:
                await self._check_new_responses()
            except Exception as e:
                logger.error(f"Ошибка проверки откликов: {e}")
            await asyncio.sleep(60)  # Каждую минуту
    
    async def _publish_vacancies_loop(self):
        """Периодическая публикация вакансий"""
        while self.is_running:
            try:
                await self._publish_inactive_vacancies()
            except Exception as e:
                logger.error(f"Ошибка публикации вакансий: {e}")
            await asyncio.sleep(300)  # Каждые 5 минут
    
    async def _sync_vacancies_loop(self):
        """Синхронизация вакансий с Avito"""
        while self.is_running:
            try:
                await self._sync_vacancies()
            except Exception as e:
                logger.error(f"Ошибка синхронизации вакансий: {e}")
            await asyncio.sleep(600)  # Каждые 10 минут
    
    async def _check_new_responses(self):
        """Проверка новых откликов"""
        if not self.api:
            # Симуляция в режиме без API
            await self._simulate_response()
            return
        
        vacancies = await db.get_active_vacancies()
        
        for vacancy in vacancies:
            if not vacancy.avito_id:
                continue
            
            try:
                responses = await self.api.get_responses(vacancy.avito_id)
                
                for response in responses:
                    response_id = response.get('id')
                    
                    # Пропускаем уже обработанные
                    if response_id in self._processed_responses:
                        continue
                    
                    await self._process_response(response, vacancy)
                    self._processed_responses.add(response_id)
                    
            except Exception as e:
                logger.error(f"Ошибка получения откликов для {vacancy.id}: {e}")
    
    async def _simulate_response(self):
        """Симуляция отклика (режим без API)"""
        import random
        
        # Шанс 5% на создание тестового отклика каждый цикл
        if random.random() > 0.05:
            return
        
        names = [
            "Александр Иванов",
            "Дмитрий Петров",
            "Максим Сидоров",
            "Сергей Смирнов",
            "Андрей Козлов",
            "Елена Кузнецова",
            "Ольга Попова",
            "Наталья Лебедева"
        ]
        
        cities = ["Москва", "Санкт-Петербург", "Казань", "Новосибирск", "Екатеринбург"]
        
        vacancy = random.choice(await db.get_active_vacancies()) if await db.get_active_vacancies() else None
        
        candidate = Candidate(
            name=random.choice(names),
            phone=f"+7{random.randint(9000000000, 9999999999)}",
            source="avito",
            status=CandidateStatus.NEW,
            vacancy_id=vacancy.id if vacancy else None,
            notes=f"Отклик с Avito. Город: {random.choice(cities)}",
        )
        
        await db.create_candidate(candidate)
        logger.info(f"✅ Новый кандидат с Avito (симуляция): {candidate.name}")
        
        # Логируем взаимодействие
        await db.log_interaction(Interaction(
            candidate_id=candidate.id,
            agent_type=AgentType.AVITO,
            interaction_type=InteractionType.AVITO_RESPONSE,
            content=f"Отклик на вакансию: {vacancy.title if vacancy else 'Неизвестно'}",
            result="new_candidate"
        ))
        
        # Создаём задачу для Voice Agent
        from common import Task
        call_task = Task(
            agent_type=AgentType.VOICE,
            task_type="call_candidate",
            payload={
                "candidate_id": candidate.id,
                "phone": candidate.phone,
                "name": candidate.name,
                "source": "avito",
            },
            priority=1
        )
        await db.create_task(call_task)
    
    async def _process_response(self, response: dict, vacancy: Vacancy):
        """Обработка отклика с Avito API"""
        candidate_data = response.get('candidate', {})
        
        candidate = Candidate(
            name=candidate_data.get('name', 'Не указано'),
            phone=candidate_data.get('phone', ''),
            source="avito",
            status=CandidateStatus.NEW,
            vacancy_id=vacancy.id,
            notes=response.get('message', ''),
        )
        
        await db.create_candidate(candidate)
        logger.info(f"✅ Новый кандидат с Avito: {candidate.name}")
        
        # Логируем взаимодействие
        await db.log_interaction(Interaction(
            candidate_id=candidate.id,
            agent_type=AgentType.AVITO,
            interaction_type=InteractionType.AVITO_RESPONSE,
            content=f"Отклик на вакансию: {vacancy.title}",
            result="new_candidate"
        ))
        
        # Отправляем сообщение кандидату через Avito
        response_id = response.get('id')
        if response_id and self.api:
            await self.api.send_message(
                response_id,
                f"Здравствуйте, {candidate.name}! Спасибо за отклик на вакансию '{vacancy.title}'. "
                f"Мы рассмотрели вашу заявку и свяжемся с вами в ближайшее время. "
                f"Также вы можете пройти быструю квалификацию в нашем Telegram боте."
            )
        
        # Создаём задачу для Voice Agent
        from common import Task
        call_task = Task(
            agent_type=AgentType.VOICE,
            task_type="call_candidate",
            payload={
                "candidate_id": candidate.id,
                "phone": candidate.phone,
                "name": candidate.name,
                "source": "avito",
            },
            priority=1
        )
        await db.create_task(call_task)
    
    async def _publish_inactive_vacancies(self):
        """Публикация вакансий без Avito ID"""
        if not self.api:
            return
        
        vacancies = await db.get_active_vacancies()
        
        for vacancy in vacancies:
            if vacancy.avito_id:
                continue
            
            try:
                vacancy_data = {
                    'title': vacancy.title,
                    'description': vacancy.description,
                    'salary_min': vacancy.salary_min,
                    'salary_max': vacancy.salary_max,
                }
                
                avito_id = await self.api.create_vacancy(vacancy_data)
                
                if avito_id:
                    vacancy.avito_id = avito_id
                    await db.update_vacancy(vacancy)
                    logger.info(f"✅ Вакансия опубликована на Avito: {vacancy.title}")
                    
            except Exception as e:
                logger.error(f"Ошибка публикации вакансии {vacancy.id}: {e}")
    
    async def _sync_vacancies(self):
        """Синхронизация вакансий с Avito"""
        if not self.api:
            return
        
        try:
            avito_vacancies = await self.api.get_vacancies()
            
            for avito_vac in avito_vacancies:
                avito_id = avito_vac.get('id')
                
                # Ищем вакансию в БД
                # (в реальности нужен более умный поиск)
                
        except Exception as e:
            logger.error(f"Ошибка синхронизации: {e}")
    
    async def _send_heartbeat(self):
        """Отправка heartbeat в БД"""
        async def heartbeat_loop():
            while self.is_running:
                try:
                    status = AgentStatus(
                        agent_type=AgentType.AVITO,
                        is_alive=True,
                        last_heartbeat=datetime.now(),
                    )
                    await db.update_agent_status(status)
                except Exception as e:
                    logger.error(f"Ошибка heartbeat: {e}")
                await asyncio.sleep(30)
        
        asyncio.create_task(heartbeat_loop())


# ========== OAuth Helper ==========

async def get_oauth_url(client_id: str, redirect_uri: str) -> str:
    """Генерация URL для OAuth авторизации"""
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'vacancies responses',
    }
    return f"https://api.avito.ru/oauth/authorize?{urlencode(params)}"


# ========== Entry Point ==========

access_token = None
refresh_token = None

async def run_avito_agent():
    """Запуск Avito агента"""
    from common import settings
    
    agent = AvitoAgent(
        client_id=settings.avito_client_id,
        client_secret=settings.avito_client_secret,
        access_token=settings.avito_access_token,
        refresh_token=settings.avito_refresh_token
    )
    await agent.start()
    
    # Держим агент запущенным
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
            await run_avito_agent()
        finally:
            await db.close()
    
    asyncio.run(main())

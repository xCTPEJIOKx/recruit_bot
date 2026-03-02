"""
Voice Agent - Голосовой агент для звонков кандидатам
Интеграция с Voximplant и Twilio для реальных звонков
"""
import asyncio
import logging
import random
import json
import base64
import hmac
import hashlib
import time
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path

import aiohttp

from common import db, Candidate, CandidateStatus, Interaction, InteractionType, AgentType, AgentStatus, Task

logger = logging.getLogger(__name__)


# ========== Скрипты диалогов ==========

CALL_SCRIPTS = {
    "greeting": [
        "Здравствуйте, {name}! Вас беспокоит рекрутинговый сервис. Вы откликались на вакансию. У вас есть минутка?",
        "Добрый день, {name}! Это рекрутинговая служба. Хотели обсудить вашу заявку на вакансию. Вам удобно говорить?",
        "Здравствуйте, {name}! Звоню по поводу вашего отклика на вакансию. Не отвлекаю?",
    ],
    "no_answer": [
        "К сожалению, абонент не ответил. Попробуем позже.",
    ],
    "positive_response": [
        "Отлично! Я отправлю вам подробности в Telegram. Ожидайте сообщение!",
        "Замечательно! Сейчас оформим все детали и свяжемся с вами ещё раз.",
    ],
}


class VoximplantClient:
    """Клиент для Voximplant API"""
    
    BASE_URL = "https://api.voximplant.com/platform_api"
    
    def __init__(self, account_id: str, api_key: str):
        self.account_id = account_id
        self.api_key = api_key
    
    def _get_signature(self, params: dict) -> str:
        """Генерация подписи API"""
        sorted_params = sorted(params.items())
        param_string = "".join(f"{k}={v}" for k, v in sorted_params)
        param_string += self.api_key
        return hashlib.md5(param_string.encode()).hexdigest()
    
    async def _request(self, endpoint: str, params: dict) -> dict:
        """HTTP запрос к API"""
        params['account_id'] = self.account_id
        params['timestamp'] = int(time.time())
        params['signature'] = self._get_signature(params)
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.BASE_URL}/{endpoint}"
            async with session.post(url, data=params) as response:
                return await response.json()
    
    async def make_call(self, phone: str, scenario_id: int, caller_id: str) -> dict:
        """Исходящий звонок"""
        params = {
            'phone': phone,
            'scenario_id': scenario_id,
            'callerid': caller_id,
        }
        return await self._request('MakeOutgoingCall', params)
    
    async def get_call_status(self, call_id: str) -> dict:
        """Статус звонка"""
        params = {'callid': call_id}
        return await self._request('GetCallStatus', params)
    
    async def get_scenarios(self) -> List[dict]:
        """Получить список сценариев"""
        return await self._request('GetScenarios', {})
    
    async def create_scenario(self, name: str, script: str) -> dict:
        """Создать сценарий"""
        params = {
            'name': name,
            'script': script,
        }
        return await self._request('AddScenario', params)


class TwilioClient:
    """Клиент для Twilio API"""
    
    BASE_URL = "https://api.twilio.com/2010-04-01"
    
    def __init__(self, account_sid: str, auth_token: str):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self._auth = aiohttp.BasicAuth(account_sid, auth_token)
    
    async def make_call(self, to: str, from_: str, url: str) -> dict:
        """Исходящий звонок"""
        params = {
            'To': to,
            'From': from_,
            'Url': url,
        }
        
        async with aiohttp.ClientSession(auth=self._auth) as session:
            url = f"{self.BASE_URL}/Accounts/{self.account_sid}/Calls.json"
            async with session.post(url, data=params) as response:
                return await response.json()
    
    async def get_call_status(self, call_sid: str) -> dict:
        """Статус звонка"""
        async with aiohttp.ClientSession(auth=self._auth) as session:
            url = f"{self.BASE_URL}/Accounts/{self.account_sid}/Calls/{call_sid}.json"
            async with session.get(url) as response:
                return await response.json()


class VoiceAgent:
    """Голосовой агент для звонков"""
    
    def __init__(self, webhook_port: int = 8001):
        self.webhook_port = webhook_port
        self.is_running = False
        self._active_calls: Dict[str, dict] = {}
        
        # Клиенты телефонии
        self.voximplant: Optional[VoximplantClient] = None
        self.twilio: Optional[TwilioClient] = None
        self.telephony_provider: str = "simulation"  # simulation, voximplant, twilio
    
    async def start(self):
        """Запуск агента"""
        logger.info("🤖 Запуск Voice агента...")
        
        # Инициализация телефонии
        await self._init_telephony()
        
        self.is_running = True
        await self._send_heartbeat()
        
        # Запускаем обработчик задач
        asyncio.create_task(self._process_tasks_loop())
        
        # Запускаем webhook сервер для входящих звонков
        asyncio.create_task(self._start_webhook())
        
        logger.info(f"✅ Voice агент запущен (режим: {self.telephony_provider})")
    
    async def stop(self):
        """Остановка агента"""
        self.is_running = False
        logger.info("🛑 Voice агент остановлен")
    
    async def _init_telephony(self):
        """Инициализация телефонии"""
        from common import settings
        
        # Voximplant
        if settings.voximplant_account_id and settings.voximplant_api_key:
            self.voximplant = VoximplantClient(
                settings.voximplant_account_id,
                settings.voximplant_api_key
            )
            self.telephony_provider = "voximplant"
            logger.info("✅ Voximplant инициализирован")
        
        # Twilio
        elif settings.twilio_account_sid and settings.twilio_auth_token:
            self.twilio = TwilioClient(
                settings.twilio_account_sid,
                settings.twilio_auth_token
            )
            self.telephony_provider = "twilio"
            logger.info("✅ Twilio инициализирован")
        
        else:
            logger.warning("⚠️ Телефония не настроена. Работа в режиме симуляции.")
            logger.info("📝 Для реальных звонков добавьте VOXIMPLANT_* или TWILIO_* в .env")
    
    async def _process_tasks_loop(self):
        """Обработка задач из очереди"""
        while self.is_running:
            try:
                tasks = await db.get_pending_tasks(AgentType.VOICE, limit=5)
                
                for task in tasks:
                    await self._process_task(task)
                
            except Exception as e:
                logger.error(f"Ошибка обработки задач: {e}")
            
            await asyncio.sleep(5)
    
    async def _process_task(self, task: Task):
        """Обработка одной задачи"""
        try:
            task.status = "in_progress"
            task.assigned_at = datetime.now()
            await db.update_task(task)
            
            if task.task_type == "call_candidate":
                result = await self._make_call(task.payload)
                task.result = result
                task.status = "completed"
                task.completed_at = datetime.now()
            
            elif task.task_type == "handle_incoming_call":
                result = await self._handle_incoming_call(task.payload)
                task.result = result
                task.status = "completed"
                task.completed_at = datetime.now()
            
            else:
                task.status = "failed"
                task.result = f"Неизвестный тип задачи: {task.task_type}"
            
            await db.update_task(task)
            
            # Обновляем статистику агента
            status = await db.get_agent_status(AgentType.VOICE)
            if status:
                if task.status == "completed":
                    status.tasks_completed += 1
                else:
                    status.tasks_failed += 1
                await db.update_agent_status(status)
            
        except Exception as e:
            logger.error(f"Ошибка выполнения задачи {task.id}: {e}")
            task.status = "failed"
            task.result = str(e)
            task.retry_count += 1
            
            if task.retry_count < task.max_retries:
                task.status = "pending"
            await db.update_task(task)
    
    async def _make_call(self, payload: dict) -> str:
        """Совершение звонка кандидату"""
        candidate_id = payload.get("candidate_id")
        phone = payload.get("phone")
        name = payload.get("name", "кандидат")
        
        logger.info(f"📞 Звонок кандидату: {name}, {phone}")
        
        if self.telephony_provider == "simulation":
            call_result = await self._simulate_call(candidate_id, name)
        elif self.telephony_provider == "voximplant":
            call_result = await self._voximplant_call(candidate_id, phone, name)
        elif self.telephony_provider == "twilio":
            call_result = await self._twilio_call(candidate_id, phone, name)
        else:
            call_result = "unknown_provider"
        
        # Логируем взаимодействие
        await db.log_interaction(Interaction(
            candidate_id=candidate_id,
            agent_type=AgentType.VOICE,
            interaction_type=InteractionType.CALL_MADE,
            content=f"Звонок на номер {phone} ({self.telephony_provider})",
            result=call_result
        ))
        
        return call_result
    
    async def _voximplant_call(self, candidate_id: str, phone: str, name: str) -> str:
        """Звонок через Voximplant"""
        try:
            from common import settings
            
            # Получаем или создаём сценарий
            scenario_id = await self._get_or_create_voximplant_scenario()
            
            # Совершаем звонок
            result = await self.voximplant.make_call(
                phone=phone,
                scenario_id=scenario_id,
                caller_id=settings.voximplant_phone_number or "+70000000000"
            )
            
            if result.get('result', False):
                call_id = result.get('call_id', '')
                self._active_calls[candidate_id] = {
                    'provider': 'voximplant',
                    'call_id': call_id,
                    'started_at': datetime.now()
                }
                logger.info(f"✅ Voximplant: звонок начат, call_id={call_id}")
                return "call_initiated"
            else:
                error = result.get('error', 'Unknown error')
                logger.error(f"❌ Voximplant ошибка: {error}")
                return f"voximplant_error: {error}"
        
        except Exception as e:
            logger.error(f"Ошибка Voximplant звонка: {e}")
            return f"voximplant_exception: {e}"
    
    async def _get_or_create_voximplant_scenario(self) -> int:
        """Получить или создать сценарий Voximplant"""
        # В реальности здесь проверка и создание сценария
        # Для простоты возвращаем фиксированный ID
        # Сценарий должен быть создан в панели Voximplant
        return 1  # Замените на реальный ID сценария
    
    async def _twilio_call(self, candidate_id: str, phone: str, name: str) -> str:
        """Звонок через Twilio"""
        try:
            from common import settings
            
            # URL webhook для управления звонком
            webhook_url = f"http://localhost:{self.webhook_port}/voice/twilio_webhook"
            
            result = await self.twilio.make_call(
                to=phone,
                from_=settings.twilio_phone_number or "+10000000000",
                url=webhook_url
            )
            
            if result.get('sid'):
                call_sid = result['sid']
                self._active_calls[candidate_id] = {
                    'provider': 'twilio',
                    'call_id': call_sid,
                    'started_at': datetime.now()
                }
                logger.info(f"✅ Twilio: звонок начат, call_sid={call_sid}")
                return "call_initiated"
            else:
                error = result.get('message', 'Unknown error')
                logger.error(f"❌ Twilio ошибка: {error}")
                return f"twilio_error: {error}"
        
        except Exception as e:
            logger.error(f"Ошибка Twilio звонка: {e}")
            return f"twilio_exception: {e}"
    
    async def _simulate_call(self, candidate_id: str, name: str) -> str:
        """Симуляция телефонного разговора"""
        scenarios = [
            "answered_positive",
            "answered_neutral",
            "no_answer",
            "declined",
            "wrong_number",
        ]
        weights = [0.4, 0.2, 0.2, 0.1, 0.1]
        result = random.choices(scenarios, weights=weights)[0]
        
        if result == "answered_positive":
            logger.info(f"✅ {name}: Ответил, заинтересован")
            await db.update_candidate_status(candidate_id, CandidateStatus.CONTACTED)
            await self._create_interview_task(candidate_id, name)
            return "answered_positive: кандидат заинтересован"
        
        elif result == "answered_neutral":
            logger.info(f"⚠️ {name}: Ответил, сомневается")
            await db.update_candidate_status(candidate_id, CandidateStatus.CONTACTED)
            return "answered_neutral: кандидат сомневается"
        
        elif result == "no_answer":
            logger.info(f"❌ {name}: Не ответил")
            return "no_answer"
        
        elif result == "declined":
            logger.info(f"🚫 {name}: Отклонил звонок")
            return "declined"
        
        else:
            logger.info(f"⛔ {name}: Неверный номер")
            return "wrong_number"
    
    async def _create_interview_task(self, candidate_id: str, name: str):
        """Создание задачи на назначение собеседования"""
        task = Task(
            agent_type=AgentType.TELEGRAM,
            task_type="send_interview_invite",
            payload={
                "candidate_id": candidate_id,
                "name": name,
                "message": f"Здравствуйте, {name}! Рады пригласить вас на собеседование! 🎉\n\nКогда вам удобно встретиться?",
            },
            priority=0
        )
        await db.create_task(task)
    
    async def _handle_incoming_call(self, payload: dict) -> str:
        """Обработка входящего звонка"""
        phone = payload.get("phone")
        logger.info(f"📥 Входящий звонок с номера: {phone}")
        return "incoming_call_handled"
    
    async def _start_webhook(self):
        """Запуск webhook сервера для входящих звонков"""
        from fastapi import FastAPI, Request
        from fastapi.responses import PlainTextResponse, JSONResponse
        import uvicorn
        
        app = FastAPI()
        
        @app.post("/voice/twilio_webhook")
        async def twilio_webhook(request: Request):
            """Webhook для Twilio"""
            form_data = await request.form()
            call_status = form_data.get('CallStatus', 'unknown')
            
            logger.info(f"📞 Twilio webhook: CallStatus={call_status}")
            
            # Возвращаем TwiML для управления звонком
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Say voice="alice" language="ru-RU">
                    Здравствуйте! Это рекрутинговый сервис.
                </Say>
                <Pause length="1"/>
                <Say voice="alice" language="ru-RU">
                    Пожалуйста, оставайтесь на линии, оператор скоро ответит.
                </Say>
            </Response>"""
            
            return PlainTextResponse(content=twiml, media_type="application/xml")
        
        @app.post("/voice/voximplant_webhook")
        async def voximplant_webhook(request: Request):
            """Webhook для Voximplant"""
            data = await request.json()
            logger.info(f"📞 Voximplant webhook: {data}")
            
            # Возвращаем сценарий для Voximplant
            scenario = {
                "commands": [
                    {"type": "playTones", "text": "Здравствуйте! Это рекрутинговый сервис."},
                    {"type": "recordCall", "value": "true"},
                ]
            }
            
            return JSONResponse(content=scenario)
        
        @app.get("/voice/status")
        async def call_status():
            """Статус активных звонков"""
            return {"active_calls": len(self._active_calls), "calls": self._active_calls}
        
        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=self.webhook_port,
            log_level="info",
            access_log=False
        )
        server = uvicorn.Server(config)
        
        logger.info(f"🌐 Webhook сервер запущен на порту {self.webhook_port}")
        await server.serve()
    
    async def _send_heartbeat(self):
        """Отправка heartbeat в БД"""
        async def heartbeat_loop():
            while self.is_running:
                try:
                    status = AgentStatus(
                        agent_type=AgentType.VOICE,
                        is_alive=True,
                        last_heartbeat=datetime.now(),
                    )
                    await db.update_agent_status(status)
                except Exception as e:
                    logger.error(f"Ошибка heartbeat: {e}")
                await asyncio.sleep(30)
        
        asyncio.create_task(heartbeat_loop())
    
    # ========== STT/TTS (offline) ==========
    
    async def speech_to_text(self, audio_data: bytes) -> Optional[str]:
        """Преобразование речи в текст (Vosk)"""
        try:
            from vosk import Model, KaldiRecognizer
            import io
            import wave
            
            model_path = Path(__file__).parent / "vosk-model-small-ru-0.22"
            
            if not model_path.exists():
                logger.warning("Модель Vosk не найдена.")
                return None
            
            model = Model(str(model_path))
            rec = KaldiRecognizer(model, 16000)
            
            rec.AcceptWaveform(audio_data)
            result = rec.Result()
            
            return json.loads(result).get('text', '')
        
        except Exception as e:
            logger.error(f"Ошибка STT: {e}")
            return None
    
    async def text_to_speech(self, text: str, output_path: str):
        """Преобразование текста в речь (Silero)"""
        try:
            import torch
            
            model, _ = torch.hub.load(
                repo_or_dir='snakers4/silero-models',
                model='silero_tts',
                language='ru',
                speaker='xenia'
            )
            
            audio = model.apply_tts(text=text, speaker='xenia')
            
            import soundfile as sf
            sf.write(output_path, audio, 48000)
            
            logger.info(f"✅ TTS: сохранено в {output_path}")
        
        except Exception as e:
            logger.error(f"Ошибка TTS: {e}")


# ========== Entry Point ==========

async def run_voice_agent():
    """Запуск Voice агента"""
    agent = VoiceAgent()
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
            await run_voice_agent()
        finally:
            await db.close()
    
    asyncio.run(main())

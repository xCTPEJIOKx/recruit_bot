"""
Telegram Bot - Агент для квалификации кандидатов
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from common import db, Candidate, CandidateStatus, Interaction, InteractionType, AgentType, AgentStatus, Vacancy

logger = logging.getLogger(__name__)


# ========== States ==========

class QualificationState(StatesGroup):
    """Состояния для квалификации кандидата"""
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_experience = State()
    waiting_for_schedule = State()
    waiting_for_salary = State()
    waiting_for_confirm = State()


# ========== Keyboards ==========

def get_menu_keyboard() -> ReplyKeyboardMarkup:
    """Основное меню без кнопок"""
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[],
        resize_keyboard=True
    )
    return keyboard


def get_schedule_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора графика"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕐 Полный день (5/2)", callback_data="schedule_full")],
        [InlineKeyboardButton(text="⏰ Частичная занятость", callback_data="schedule_part")],
        [InlineKeyboardButton(text="🏠 Удалённо", callback_data="schedule_remote")],
        [InlineKeyboardButton(text="📅 Гибкий график", callback_data="schedule_flexible")],
    ])


def get_experience_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора опыта"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Нет опыта", callback_data="exp_none")],
        [InlineKeyboardButton(text="📚 До 1 года", callback_data="exp_less_1")],
        [InlineKeyboardButton(text="💼 1-3 года", callback_data="exp_1_3")],
        [InlineKeyboardButton(text="🎯 3+ года", callback_data="exp_3_plus")],
    ])


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_yes")],
        [InlineKeyboardButton(text="❌ Изменить данные", callback_data="confirm_no")],
    ])


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Админская клавиатура"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 Кандидаты", callback_data="admin_candidates")],
        [InlineKeyboardButton(text="📋 Вакансии", callback_data="admin_vacancies")],
    ])


# ========== Handler Class ==========

class TelegramBot:
    """Telegram Bot Agent"""
    
    def __init__(self, token: str):
        self.token = token
        self.bot: Optional[Bot] = None
        self.dp: Optional[Dispatcher] = None
        self.is_running = False
        
        # Данные для квалификации
        self.qualification_data: dict = {}
    
    async def start(self):
        """Запуск бота"""
        logger.info("🤖 Запуск Telegram бота...")
        
        self.bot = Bot(token=self.token)
        self.dp = Dispatcher(storage=MemoryStorage())
        
        # Регистрация хендлеров
        self._register_handlers()
        
        # Запуск polling
        self.is_running = True
        await self._send_heartbeat()
        
        try:
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"Ошибка polling: {e}")
            self.is_running = False
    
    async def stop(self):
        """Остановка бота"""
        self.is_running = False
        if self.bot:
            await self.bot.session.close()
    
    def _register_handlers(self):
        """Регистрация обработчиков"""
        # Команды
        self.dp.message(Command("start"))(self.cmd_start)
        self.dp.message(Command("status"))(self.cmd_status)
        self.dp.message(Command("stats"))(self.cmd_stats)
        self.dp.message(Command("vacancies"))(self.cmd_vacancies)
        self.dp.message(Command("webapp"))(self.cmd_webapp)

        # Обработка текста во время квалификации
        self.dp.message(StateFilter(None))(self.handle_text_during_qualification)
    
    # ========== Commands ==========
    
    async def cmd_start(self, message: types.Message):
        """Обработка /start - только текст"""
        user = message.from_user

        # Проверяем, есть ли уже кандидат с таким telegram_id
        candidate = await db.get_candidate_by_telegram(user.id)

        # Отправляем приветствие
        await message.answer(
            f"👋 **Здравствуйте, {user.first_name}!**\n\n"
            f"🤖 Я бот по подбору персонала.\n\n"
            f"📱 **Нажмите меню:**"
        )

        # Логгируем взаимодействие
        if candidate:
            await self._log_interaction(candidate.id, InteractionType.MESSAGE_RECEIVED, "/start")
    
    async def cmd_status(self, message: types.Message):
        """Обработка /status - статус кандидата"""
        candidate = await db.get_candidate_by_telegram(message.from_user.id)
        
        if not candidate:
            await message.answer("❌ Вы ещё не откликались на вакансии.\n\nНажмите '📝 Откликнуться на вакансию', чтобы начать.")
            return
        
        interactions = await db.get_interactions(candidate.id, limit=5)
        
        status_text = f"""
📊 **Ваш статус**

Статус: {self._status_to_emoji(candidate.status)} {self._translate_status(candidate.status)}

📝 Информация:
• Имя: {candidate.name or 'Не указано'}
• Телефон: {candidate.phone or 'Не указан'}
• Вакансия: {candidate.vacancy_id or 'Не выбрана'}

📅 Дата отклика: {candidate.created_at.strftime('%d.%m.%Y %H:%M')}
"""
        await message.answer(status_text)
    
    async def cmd_stats(self, message: types.Message):
        """Обработка /stats - статистика (для админа)"""
        # Простая проверка на админа (можно улучшить)
        stats = await db.get_stats()
        
        text = f"""
📊 **Статистика рекрутинга**

**Кандидаты по статусам:**
"""
        for status, count in stats['candidates_by_status'].items():
            emoji = self._status_to_emoji(status)
            text += f"\n{emoji} {self._translate_status(status)}: {count}"
        
        text += f"\n\n**По источникам:**"
        for source, count in stats['candidates_by_source'].items():
            text += f"\n• {source}: {count}"
        
        text += f"\n\n**Вакансии:**"
        text += f"\n• Активные: {stats['active_vacancies']}"
        text += f"\n• Всего: {stats['total_vacancies']}"
        
        await message.answer(text)
    
    async def cmd_vacancies(self, message: types.Message):
        """Обработка /vacancies - список вакансий"""
        vacancies = await db.get_active_vacancies()

        if not vacancies:
            await message.answer("❌ Сейчас нет активных вакансий.")
            return

        for vacancy in vacancies:
            salary = ""
            if vacancy.salary_min or vacancy.salary_max:
                if vacancy.salary_min and vacancy.salary_max:
                    salary = f"\n💰 Зарплата: {vacancy.salary_min:,} - {vacancy.salary_max:,} ₽"
                elif vacancy.salary_min:
                    salary = f"\n💰 Зарплата: от {vacancy.salary_min:,} ₽"
                else:
                    salary = f"\n💰 Зарплата: до {vacancy.salary_max:,} ₽"

            text = f"""
💼 **{vacancy.title}**{salary}

{vacancy.description}

📋 **Требования:**
{vacancy.requirements}

✅ **Условия:**
{vacancy.conditions}
"""
            await message.answer(text)

    async def cmd_webapp(self, message: types.Message):
        """Обработка /webapp - открыть Web App"""
        from common import settings
        
        webapp_url = f"http://{settings.orchestrator_host}:{settings.orchestrator_port}/static/index.html"
        
        await message.answer(
            "🌐 **Открываю веб-интерфейс...**\n\n"
            "Нажмите на кнопку ниже, чтобы открыть графический интерфейс:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🚀 Открыть Web App", web_app=types.WebAppInfo(url=webapp_url))]
            ])
        )

    async def btn_webapp(self, message: types.Message):
        """Кнопка Web App - показываем меню снова"""
        await message.answer(
            "🚀 **Нажмите кнопку в меню:**",
            reply_markup=get_menu_keyboard()
        )
    
    # ========== Button Handlers ==========
    
    async def btn_apply(self, message: types.Message, state: FSMContext):
        """Кнопка 'Откликнуться на вакансию'"""
        vacancies = await db.get_active_vacancies()
        
        if not vacancies:
            await message.answer("❌ Сейчас нет активных вакансий. Попробуйте позже.")
            return
        
        # Показываем первую вакансию (можно улучшить)
        vacancy = vacancies[0]
        
        salary = ""
        if vacancy.salary_min or vacancy.salary_max:
            if vacancy.salary_min and vacancy.salary_max:
                salary = f"{vacancy.salary_min:,} - {vacancy.salary_max:,} ₽"
            elif vacancy.salary_min:
                salary = f"от {vacancy.salary_min:,} ₽"
            else:
                salary = f"до {vacancy.salary_max:,} ₽"
        
        await message.answer(
            f"💼 **{vacancy.title}**\n"
            f"💰 Зарплата: {salary}\n\n"
            f"{vacancy.description}\n\n"
            f"Начнём квалификацию!\n\n"
            f"📝 **Вопрос 1/5:** Как вас зовут?",
            parse_mode="Markdown"
        )
        
        await state.set_state(QualificationState.waiting_for_name)
        
        # Сохраняем vacancy_id во временные данные
        async with state.get_data() as data:
            data['vacancy_id'] = vacancy.id
    
    async def btn_my_status(self, message: types.Message):
        """Кнопка 'Мой статус'"""
        await self.cmd_status(message)
    
    async def btn_contact(self, message: types.Message):
        """Кнопка 'Связаться с нами'"""
        await message.answer(
            "📞 **Контакты:**\n\n"
            "📧 Email: hr@company.com\n"
            "📱 Telegram: @hr_manager\n"
            "🕐 Рабочее время: Пн-Пт 9:00-18:00\n\n"
            "Мы ответим вам в ближайшее время!"
        )
    
    # ========== Qualification Flow ==========
    
    async def handle_text_during_qualification(self, message: types.Message, state: FSMContext):
        """Обработка текста во время квалификации"""
        current_state = await state.get_state()
        
        if current_state == QualificationState.waiting_for_name:
            # Сохраняем имя
            async with state.update_data() as data:
                data['name'] = message.text
                data['telegram_id'] = message.from_user.id
                data['telegram_username'] = message.from_user.username
            
            await message.answer(
                f"Приятно познакомиться, {message.text}! 👋\n\n"
                f"📝 **Вопрос 2/5:** Ваш номер телефона?\n\n"
                f"_(Отправьте в формате +7XXX_______)_"
            )
            await state.set_state(QualificationState.waiting_for_phone)
        
        elif current_state == QualificationState.waiting_for_phone:
            # Сохраняем телефон
            async with state.update_data() as data:
                data['phone'] = message.text
            
            await message.answer(
                "📝 **Вопрос 3/5:** Какой у вас опыт работы?\n\n"
                f"_(Выберите вариант ниже)_",
                reply_markup=get_experience_keyboard()
            )
            await state.set_state(QualificationState.waiting_for_experience)
        
        elif current_state == QualificationState.waiting_for_experience:
            # Уже обработано в callback
            pass
        
        elif current_state == QualificationState.waiting_for_schedule:
            # Уже обработано в callback
            pass
        
        elif current_state == QualificationState.waiting_for_salary:
            # Сохраняем желаемую зарплату
            async with state.update_data() as data:
                data['expected_salary'] = message.text
            
            # Показываем сводку
            data = await state.get_data()
            summary = f"""
📋 **Проверьте ваши данные:**

👤 Имя: {data.get('name')}
📱 Телефон: {data.get('phone')}
💼 Опыт: {data.get('experience', 'Не указано')}
🕐 График: {data.get('schedule', 'Не указано')}
💰 Желаемая ЗП: {data.get('expected_salary')}

Всё верно?"""
            await message.answer(summary, reply_markup=get_confirm_keyboard())
            await state.set_state(QualificationState.waiting_for_confirm)
    
    async def callback_experience(self, callback: types.CallbackQuery, state: FSMContext):
        """Выбор опыта"""
        exp_map = {
            'exp_none': 'Нет опыта',
            'exp_less_1': 'До 1 года',
            'exp_1_3': '1-3 года',
            'exp_3_plus': '3+ года',
        }
        experience = exp_map.get(callback.data, 'Не указано')
        
        async with state.update_data() as data:
            data['experience'] = experience
        
        await callback.message.answer(
            f"📝 **Вопрос 4/5:** Какой график вас интересует?\n\n"
            f"_(Выберите вариант)_",
            reply_markup=get_schedule_keyboard()
        )
        await state.set_state(QualificationState.waiting_for_schedule)
        await callback.answer()
    
    async def callback_schedule(self, callback: types.CallbackQuery, state: FSMContext):
        """Выбор графика"""
        schedule_map = {
            'schedule_full': 'Полный день (5/2)',
            'schedule_part': 'Частичная занятость',
            'schedule_remote': 'Удалённо',
            'schedule_flexible': 'Гибкий график',
        }
        schedule = schedule_map.get(callback.data, 'Не указано')
        
        async with state.update_data() as data:
            data['schedule'] = schedule
        
        await callback.message.answer(
            f"📝 **Вопрос 5/5:** Какая зарплата вас интересует?\n\n"
            f"_(Напишите сумму в рублях)_"
        )
        await state.set_state(QualificationState.waiting_for_salary)
        await callback.answer()
    
    async def callback_confirm(self, callback: types.CallbackQuery, state: FSMContext):
        """Подтверждение данных"""
        if callback.data == "confirm_yes":
            # Создаём кандидата в БД
            data = await state.get_data()
            
            candidate = Candidate(
                name=data.get('name'),
                phone=data.get('phone'),
                telegram_id=data.get('telegram_id'),
                telegram_username=data.get('telegram_username'),
                source='telegram',
                status=CandidateStatus.NEW,
                vacancy_id=data.get('vacancy_id'),
                notes=f"Опыт: {data.get('experience')}, График: {data.get('schedule')}, Ожидаемая ЗП: {data.get('expected_salary')}"
            )
            
            await db.create_candidate(candidate)
            
            # Логируем взаимодействие
            await self._log_interaction(
                candidate.id,
                InteractionType.STATUS_CHANGED,
                f"Новый кандидат: {candidate.name}"
            )
            
            await callback.message.answer(
                f"✅ **Заявка отправлена!**\n\n"
                f"Спасибо, {candidate.name}! Ваша анкета принята.\n\n"
                f"📞 Мы свяжемся с вами по телефону {candidate.phone} в ближайшее время.\n\n"
                f"Вы можете проверить статус в любой момент командой /status",
                reply_markup=get_main_keyboard()
            )
            
            # Создаём задачу для Voice Agent
            await self._create_call_task(candidate)
            
        else:
            # Начинаем заново
            await callback.message.answer(
                "🔄 Начинаем квалификацию заново.\n\n"
                "📝 **Вопрос 1/5:** Как вас зовут?"
            )
            await state.set_state(QualificationState.waiting_for_name)
        
        await state.clear()
        await callback.answer()
    
    # ========== Helpers ==========
    
    async def _log_interaction(self, candidate_id: str, interaction_type: InteractionType, content: str, result: str = ""):
        """Логирование взаимодействия"""
        interaction = Interaction(
            candidate_id=candidate_id,
            agent_type=AgentType.TELEGRAM,
            interaction_type=interaction_type,
            content=content,
            result=result
        )
        await db.log_interaction(interaction)
    
    async def _create_call_task(self, candidate: Candidate):
        """Создание задачи на звонок кандидату"""
        from common import Task
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
        logger.info(f"✅ Создана задача на звонок: {candidate.phone}")
    
    async def _send_heartbeat(self):
        """Отправка heartbeat в БД"""
        async def heartbeat_loop():
            while self.is_running:
                try:
                    status = AgentStatus(
                        agent_type=AgentType.TELEGRAM,
                        is_alive=True,
                        last_heartbeat=datetime.now(),
                    )
                    await db.update_agent_status(status)
                except Exception as e:
                    logger.error(f"Ошибка heartbeat: {e}")
                await asyncio.sleep(30)  # Каждые 30 секунд
        
        asyncio.create_task(heartbeat_loop())
    
    def _status_to_emoji(self, status: CandidateStatus) -> str:
        """Эмодзи для статуса"""
        emojis = {
            CandidateStatus.NEW: "🆕",
            CandidateStatus.CONTACTED: "📞",
            CandidateStatus.QUALIFIED: "✅",
            CandidateStatus.INTERVIEW: "📅",
            CandidateStatus.OFFER: "📋",
            CandidateStatus.HIRED: "🎉",
            CandidateStatus.REJECTED: "❌",
            CandidateStatus.BLACKLIST: "🚫",
        }
        return emojis.get(status, "❓")
    
    def _translate_status(self, status: str) -> str:
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


# ========== Entry Point ==========

async def run_telegram_bot():
    """Запуск Telegram бота"""
    from common import settings
    
    if not settings.telegram_bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN не настроен!")
        logger.info("📝 Получите токен у @BotFather и добавьте в .env")
        return
    
    bot = TelegramBot(settings.telegram_bot_token)
    await bot.start()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    async def main():
        await db.connect()
        try:
            await run_telegram_bot()
        finally:
            await db.close()
    
    asyncio.run(main())

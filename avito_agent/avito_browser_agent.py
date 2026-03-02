"""
Avito Browser Agent - автоматическая работа с откликами через браузер
Не требует OAuth API - работает через веб-интерфейс Avito

Функционал:
- Проверка новых откликов на вакансии
- Отправка сообщений кандидатам с приглашением в Telegram бот
- Сохранение кандидатов в базу данных
- Создание задач для Voice Agent
"""
import asyncio
import logging
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from common.database import db
from common.models import Candidate, CandidateStatus, Interaction, InteractionType, AgentType, AgentStatus, Task, Vacancy
from common.config import settings

logger = logging.getLogger(__name__)


class AvitoBrowserAgent:
    """Агент для работы с Avito через браузер"""

    def __init__(self):
        self.login: str = settings.avito_login or ""
        self.password: str = settings.avito_password or ""
        self.telegram_bot_username: str = "Recruit2026_bot"
        
        self.base_url = "https://www.avito.ru"
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        self.is_running = False
        self._processed_chats: set = set()  # Уже обработанные чаты
        self._session_file = Path("/tmp/avito_session.json")

    async def connect(self) -> bool:
        """Подключение к Avito (вход в аккаунт)"""
        if not self.login or not self.password:
            logger.error("❌ Avito логин/пароль не настроены в .env")
            return False

        try:
            logger.info("🌐 Запуск браузера...")
            playwright = await async_playwright().start()

            # Запускаем Chromium с оптимизациями
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                    '--window-size=1920,1080',
                    '--disable-blink-features=AutomationControlled'
                ]
            )

            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )

            # Загружаем сохранённую сессию если есть
            if self._session_file.exists():
                logger.info("📂 Загрузка сохранённой сессии...")
                with open(self._session_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                await self.context.add_cookies(cookies)
                logger.info(f"✅ Загружено {len(cookies)} cookies")

            self.page = await self.context.new_page()

            # Проверяем авторизацию
            logger.info("🔐 Проверка авторизации...")
            await self.page.goto(f"{self.base_url}/profile", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(5)

            # Проверяем, вошли ли
            try:
                # Ищем элементы авторизованного пользователя
                profile_link = await self.page.query_selector('a[href="/user_profile"]')
                if profile_link:
                    logger.info("✅ Avito: сессия действительна")
                    return True
            except:
                pass

            # Сессия недействительна - логинимся
            logger.warning("⚠️ Сессия недействительна, выполняем вход...")
            
            # Avito использует правильный URL для входа
            login_url = f"{self.base_url}/#login?authsrc=h"
            
            logger.info(f"  → Переход на страницу входа: {login_url}")
            await self.page.goto(login_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(5)
            
            # Скриншот для отладки
            await self.page.screenshot(path="/tmp/avito_login_page.png")
            logger.info("📸 Скриншот страницы входа: /tmp/avito_login_page.png")
            
            # Получаем HTML для отладки
            html_content = await self.page.content()
            logger.info(f"📄 Размер HTML страницы: {len(html_content)} байт")
            
            # Ищем кнопку "Войти" и кликаем если форма не показана
            logger.info("  → Поиск формы входа...")
            try:
                login_button = await self.page.query_selector('button:has-text("Войти"), button:has-text("Log in"), [data-testid*="login"]')
                if login_button:
                    logger.info("✅ Найдена кнопка входа, кликаем...")
                    await login_button.click()
                    await asyncio.sleep(3)
            except Exception as e:
                logger.info(f"  → Кнопка не найдена: {e}")
            
            # Ввод логина - используем разные селекторы
            logger.info("  → Ввод логина...")
            try:
                # Avito использует input с type="text" или data-testid
                login_selectors = [
                    'input[type="text"]',
                    'input[type="tel"]',
                    'input[type="email"]',
                    'input[data-testid*="login"]',
                    'input[data-testid*="phone"]',
                    'input[name="login"]',
                    'input[name="phone"]',
                    '#login-input',
                    '#phone-input',
                    'input[placeholder*="телефон"]',
                    'input[placeholder*="email"]',
                    'input[placeholder*="Login"]',
                    'input[placeholder*="Phone"]',
                    'input[class*="login"]',
                    'input[class*="phone"]',
                    'input[class*="email"]'
                ]
                
                login_input = None
                for selector in login_selectors:
                    try:
                        login_input = await self.page.wait_for_selector(selector, timeout=3000)
                        logger.info(f"✅ Найдено поле логина по селектору: {selector}")
                        break
                    except:
                        continue
                
                if not login_input:
                    # Пробуем найти все input поля
                    all_inputs = await self.page.query_selector_all('input')
                    logger.info(f"Найдено input полей: {len(all_inputs)}")
                    
                    for i, inp in enumerate(all_inputs):
                        try:
                            inp_type = await inp.get_attribute('type')
                            inp_name = await inp.get_attribute('name')
                            inp_id = await inp.get_attribute('id')
                            inp_placeholder = await inp.get_attribute('placeholder')
                            inp_class = await inp.get_attribute('class')
                            logger.info(f"  Input {i}: type={inp_type}, id={inp_id}, name={inp_name}, placeholder={inp_placeholder}")
                        except:
                            continue
                    
                    # Используем первый подходящий input
                    for inp in all_inputs:
                        try:
                            inp_type = await inp.get_attribute('type')
                            if inp_type in ['text', 'tel', 'email', 'number']:
                                login_input = inp
                                logger.info(f"✅ Используем input type={inp_type}")
                                break
                        except:
                            continue
                
                if login_input:
                    await login_input.click()
                    await asyncio.sleep(1)
                    await login_input.fill(self.login)
                    await asyncio.sleep(2)
                    
                    # Кнопка продолжения
                    button_selectors = [
                        'button:has-text("Продолжить")',
                        'button:has-text("Continue")',
                        'button[type="submit"]',
                        'input[type="submit"]',
                        'button[class*="continue"]',
                        'button[class*="submit"]',
                        'button[class*="next"]',
                        'button:has-text("Далее")',
                        'button:has-text("Next")'
                    ]
                    
                    continue_btn = None
                    for selector in button_selectors:
                        try:
                            continue_btn = await self.page.query_selector(selector)
                            if continue_btn:
                                logger.info(f"✅ Найдена кнопка по селектору: {selector}")
                                break
                        except:
                            continue
                    
                    if continue_btn:
                        await continue_btn.click()
                        await asyncio.sleep(5)
                    else:
                        # Пробуем Enter
                        logger.info("  → Отправка через Enter...")
                        await self.page.keyboard.press('Enter')
                        await asyncio.sleep(5)
                else:
                    logger.error("❌ Не найдено поле для ввода логина")
                    # Сохраняем полный HTML для отладки
                    with open("/tmp/avito_login_html.txt", "w", encoding="utf-8") as f:
                        f.write(html_content[:10000])
                    logger.info("📄 HTML сохранён в /tmp/avito_login_html.txt")
                    return False
                    
            except Exception as e:
                logger.error(f"Ошибка ввода логина: {e}")
                await self.page.screenshot(path="/tmp/avito_login_error.png")
                return False

            # Ввод пароля
            logger.info("  → Ввод пароля...")
            try:
                password_selectors = [
                    'input[type="password"]',
                    'input[data-testid*="password"]',
                    'input[name="password"]',
                    '#password-input',
                    '#pwd-input',
                    'input[placeholder*="пароль"]',
                    'input[placeholder*="password"]',
                    'input[class*="password"]'
                ]
                
                password_input = None
                for selector in password_selectors:
                    try:
                        password_input = await self.page.wait_for_selector(selector, timeout=3000)
                        logger.info(f"✅ Найдено поле пароля по селектору: {selector}")
                        break
                    except:
                        continue
                
                if not password_input:
                    # Ищем все password поля
                    all_inputs = await self.page.query_selector_all('input')
                    for inp in all_inputs:
                        try:
                            inp_type = await inp.get_attribute('type')
                            if inp_type == 'password':
                                password_input = inp
                                logger.info(f"✅ Найдено password поле")
                                break
                        except:
                            continue
                
                if password_input:
                    await password_input.click()
                    await asyncio.sleep(1)
                    await password_input.fill(self.password)
                    await asyncio.sleep(2)

                    # Кнопка входа
                    button_selectors = [
                        'button:has-text("Войти")',
                        'button:has-text("Login")',
                        'button:has-text("Sign in")',
                        'button[type="submit"]',
                        'input[type="submit"]',
                        'button[class*="login"]',
                        'button[class*="signin"]'
                    ]
                    
                    login_btn = None
                    for selector in button_selectors:
                        try:
                            login_btn = await self.page.query_selector(selector)
                            if login_btn:
                                logger.info(f"✅ Найдена кнопка входа по селектору: {selector}")
                                break
                        except:
                            continue
                    
                    if login_btn:
                        await login_btn.click()
                        await asyncio.sleep(5)
                    else:
                        logger.info("  → Отправка через Enter...")
                        await self.page.keyboard.press('Enter')
                        await asyncio.sleep(5)
                else:
                    logger.error("❌ Не найдено поле для ввода пароля")
                    return False
                    
            except Exception as e:
                logger.error(f"Ошибка ввода пароля: {e}")
                await self.page.screenshot(path="/tmp/avito_password_error.png")
                return False

            # Проверка успешного входа
            await asyncio.sleep(3)
            current_url = self.page.url
            logger.info(f"📍 Текущий URL: {current_url}")

            if "profile" in current_url.lower() or "/user" in current_url.lower():
                logger.info("✅ Вход в Avito выполнен успешно")

                # Сохраняем сессию
                cookies = await self.context.cookies()
                with open(self._session_file, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f, indent=2, ensure_ascii=False)
                logger.info(f"💾 Сессия сохранена в {self._session_file}")

                return True

            # Возможно капча
            await self.page.screenshot(path="/tmp/avito_login.png", full_page=True)
            logger.warning("⚠️ Возможно требуется капча. Скриншот: /tmp/avito_login.png")
            return False

        except Exception as e:
            logger.error(f"❌ Ошибка подключения к Avito: {e}")
            return False

    async def get_response_chats(self) -> List[Dict]:
        """Получить список чатов с откликами на вакансии"""
        if not self.page:
            return []

        try:
            logger.info("📬 Получение списка чатов с откликами...")
            await self.page.goto(f"{self.base_url}/messenger", wait_until="domcontentloaded")
            await asyncio.sleep(5)

            # Ждём загрузки списка чатов
            try:
                await self.page.wait_for_selector('.messenger-threads-list, [class*="threads"]', timeout=10000)
            except:
                logger.warning("⚠️ Не удалось найти список чатов")
                return []

            chats = []
            
            # Ищем элементы чатов (селекторы могут меняться)
            chat_selectors = [
                '.messenger-thread',
                '[class*="thread"]',
                '[class*="chat-item"]',
                'div[role="listitem"]'
            ]

            chat_elements = []
            for selector in chat_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        chat_elements = elements
                        logger.info(f"✅ Найдено чатов по селектору '{selector}': {len(elements)}")
                        break
                except:
                    continue

            if not chat_elements:
                # Если не нашли чаты, пробуем найти сообщения
                logger.warning("⚠️ Чаты не найдены, пробуем альтернативный поиск...")
                return []

            # Парсим информацию о чатах
            for i, elem in enumerate(chat_elements[:20]):  # Первые 20 чатов
                try:
                    # Имя кандидата
                    name_elem = await elem.query_selector('.thread-name, [class*="name"], [class*="title"]')
                    name = await name_elem.inner_text() if name_elem else f"Кандидат {i+1}"

                    # Последнее сообщение
                    msg_elem = await elem.query_selector('.thread-message, [class*="message"], [class*="last-text"]')
                    last_message = await msg_elem.inner_text() if msg_elem else ""

                    # Время
                    time_elem = await elem.query_selector('.thread-time, [class*="time"], [class*="date"]')
                    time_text = await time_elem.inner_text() if time_elem else ""

                    # Проверяем, это отклик на вакансию
                    is_response = any(keyword in last_message.lower() for keyword in [
                        'отклик', 'ваканс', 'резюме', 'работа', 'менеджер', 'продаж'
                    ])

                    chats.append({
                        'name': name.strip(),
                        'last_message': last_message.strip(),
                        'time': time_text.strip(),
                        'is_response': is_response or True,  # Считаем все чаты потенциальными откликами
                        'element_index': i
                    })

                except Exception as e:
                    logger.error(f"Ошибка парсинга чата {i}: {e}")
                    continue

            logger.info(f"✅ Найдено чатов: {len(chats)}")
            return chats

        except Exception as e:
            logger.error(f"❌ Ошибка получения чатов: {e}")
            return []

    async def open_chat(self, chat_index: int = 0) -> bool:
        """Открыть чат по индексу"""
        if not self.page:
            return False

        try:
            # Находим все чаты и кликаем на нужный
            chat_selectors = [
                '.messenger-thread',
                '[class*="thread"]',
                '[class*="chat-item"]'
            ]

            for selector in chat_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements and chat_index < len(elements):
                        await elements[chat_index].click()
                        await asyncio.sleep(3)
                        return True
                except:
                    continue

            return False

        except Exception as e:
            logger.error(f"❌ Ошибка открытия чата: {e}")
            return False

    async def send_telegram_invite(self, candidate_name: str, vacancy_title: str = "вакансию") -> bool:
        """
        Отправить сообщение с приглашением в Telegram бот

        Args:
            candidate_name: Имя кандидата
            vacancy_title: Название вакансии

        Returns:
            bool: True если успешно
        """
        if not self.page:
            return False

        # Формируем сообщение
        telegram_link = f"https://t.me/{self.telegram_bot_username}"
        
        message = f"""
👋 Здравствуйте, {candidate_name}!

Меня зовут Анна, я HR-менеджер. Спасибо за ваш отклик на вакансию "{vacancy_title}"!

Для быстрого рассмотрения вашей кандидатуры, пожалуйста, пройдите короткую квалификацию в нашем Telegram боте — это займёт всего 2-3 минуты:

👉 {telegram_link}

Нажмите "Запустить" в боте и следуйте инструкциям.

После заполнения я свяжусь с вами для обсуждения деталей!

Если есть вопросы — пишите здесь, с радостью отвечу! ✨
"""

        try:
            logger.info(f"📤 Отправка приглашения кандидату: {candidate_name}")

            # Ждём загрузки поля ввода сообщения
            await asyncio.sleep(2)

            # Ищем поле ввода (разные селекторы)
            textarea_selectors = [
                'textarea[placeholder*="Сообщение"]',
                'textarea[placeholder*="Напишите сообщение"]',
                'textarea[class*="input"]',
                '[contenteditable="true"]',
                'div[role="textbox"]'
            ]

            textarea = None
            for selector in textarea_selectors:
                try:
                    textarea = await self.page.query_selector(selector)
                    if textarea:
                        logger.info(f"✅ Найдено поле ввода по селектору: {selector}")
                        break
                except:
                    continue

            if not textarea:
                logger.error("❌ Не найдено поле ввода сообщения")
                # Скриншот для отладки
                await self.page.screenshot(path="/tmp/avito_chat.png")
                return False

            # Вводим сообщение (для contenteditable используем другой метод)
            tag_name = await textarea.evaluate('el => el.tagName')
            
            if tag_name.lower() == 'textarea':
                await textarea.fill(message)
            else:
                # Для contenteditable
                await textarea.click()
                await asyncio.sleep(1)
                await self.page.keyboard.type(message)

            await asyncio.sleep(2)

            # Ищем кнопку отправки
            send_selectors = [
                'button[type="submit"]',
                'button[class*="send"]',
                'button[class*="submit"]',
                '[class*="send-button"]',
                'svg[class*="send"]',
                '[aria-label*="Отправить"]'
            ]

            send_btn = None
            for selector in send_selectors:
                try:
                    send_btn = await self.page.query_selector(selector)
                    if send_btn:
                        break
                except:
                    continue

            if send_btn:
                await send_btn.click()
                await asyncio.sleep(2)
                logger.info(f"✅ Сообщение отправлено кандидату: {candidate_name}")
                return True
            else:
                # Пробуем Enter
                logger.info("  → Отправка через Enter...")
                await self.page.keyboard.press('Enter')
                await asyncio.sleep(2)
                logger.info(f"✅ Сообщение отправлено (через Enter): {candidate_name}")
                return True

        except Exception as e:
            logger.error(f"❌ Ошибка отправки сообщения: {e}")
            await self.page.screenshot(path="/tmp/avito_send_error.png")
            return False

    async def extract_candidate_info(self) -> Dict:
        """
        Извлечь информацию о кандидате из чата

        Returns:
            Dict с информацией: name, phone, city, experience
        """
        info = {
            'name': 'Неизвестно',
            'phone': '',
            'city': '',
            'experience': ''
        }

        if not self.page:
            return info

        try:
            # Получаем заголовок чата (имя кандидата)
            header_selectors = [
                '.messenger-header',
                '[class*="header"]',
                '[class*="chat-title"]'
            ]

            for selector in header_selectors:
                try:
                    header = await self.page.query_selector(selector)
                    if header:
                        text = await header.inner_text()
                        # Извлекаем имя
                        info['name'] = text.split('\n')[0].strip()
                        break
                except:
                    continue

            # Получаем историю сообщений для поиска телефона
            messages = await self.page.query_selector_all('.message, [class*="message"]')
            for msg in messages[:10]:
                try:
                    text = await msg.inner_text()
                    # Ищем телефон
                    if '+' in text and any(d.isdigit() for d in text):
                        # Простой паттерн для телефона
                        import re
                        phones = re.findall(r'\+7\d{10}', text.replace(' ', '').replace('-', ''))
                        if phones:
                            info['phone'] = phones[0]
                            break
                except:
                    continue

            logger.info(f"✅ Информация о кандидате: {info}")
            return info

        except Exception as e:
            logger.error(f"❌ Ошибка извлечения информации: {e}")
            return info

    async def process_new_responses(self) -> int:
        """
        Обработать новые отклики

        Returns:
            int: Количество обработанных откликов
        """
        if not self.page:
            return 0

        processed_count = 0
        chats = await self.get_response_chats()

        for i, chat in enumerate(chats):
            # Пропускаем уже обработанные
            chat_key = f"{chat['name']}_{chat.get('time', '')}"
            if chat_key in self._processed_chats:
                continue

            logger.info(f"\n{'='*50}")
            logger.info(f"📨 Обработка чата #{i+1}: {chat['name']}")
            logger.info(f"   Сообщение: {chat['last_message'][:100]}...")

            # Открываем чат
            if not await self.open_chat(i):
                logger.warning(f"⚠️ Не удалось открыть чат #{i}")
                continue

            await asyncio.sleep(2)

            # Извлекаем информацию
            candidate_info = await self.extract_candidate_info()

            # Получаем активные вакансии для определения на какую отклик
            vacancies = await db.get_active_vacancies()
            vacancy = vacancies[0] if vacancies else None

            # Создаём кандидата в БД
            candidate = Candidate(
                name=candidate_info['name'],
                phone=candidate_info['phone'] or None,
                source="avito",
                status=CandidateStatus.NEW,
                vacancy_id=vacancy.id if vacancy else None,
                notes=f"Отклик с Avito. Чат: {chat['name']}"
            )

            await db.create_candidate(candidate)
            logger.info(f"✅ Кандидат сохранён в БД: {candidate.name} (ID: {candidate.id})")

            # Логируем взаимодействие
            await db.log_interaction(Interaction(
                candidate_id=candidate.id,
                agent_type=AgentType.AVITO,
                interaction_type=InteractionType.AVITO_RESPONSE,
                content=f"Отклик на вакансию: {vacancy.title if vacancy else 'Неизвестно'}",
                result="candidate_created"
            ))

            # Отправляем приглашение в Telegram
            vacancy_title = vacancy.title if vacancy else "вакансию"
            if await self.send_telegram_invite(candidate_info['name'], vacancy_title):
                logger.info(f"✅ Приглашение в Telegram отправлено")

                # Обновляем статус
                await db.update_candidate_status(candidate.id, CandidateStatus.CONTACTED)

                # Логируем отправку
                await db.log_interaction(Interaction(
                    candidate_id=candidate.id,
                    agent_type=AgentType.AVITO,
                    interaction_type=InteractionType.MESSAGE_SENT,
                    content=f"Приглашение в Telegram: t.me/{self.telegram_bot_username}",
                    result="telegram_invite_sent"
                ))

            processed_count += 1
            self._processed_chats.add(chat_key)

            # Небольшая задержка между обработкой
            await asyncio.sleep(3)

        return processed_count

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

    async def start(self):
        """Запуск агента"""
        logger.info("🤖 Запуск Avito Browser Agent...")

        # Подключение к Avito
        if not await self.connect():
            logger.error("❌ Не удалось подключиться к Avito")
            return

        self.is_running = True
        await self._send_heartbeat()

        logger.info("✅ Avito Browser Agent запущен")

        # Основной цикл обработки откликов
        while self.is_running:
            try:
                count = await self.process_new_responses()
                if count > 0:
                    logger.info(f"📊 Обработано откликов: {count}")
            except Exception as e:
                logger.error(f"Ошибка обработки откликов: {e}")
                # Пробуем переподключиться
                await asyncio.sleep(10)
                if not await self.connect():
                    logger.error("❌ Не удалось переподключиться к Avito")

            # Проверка каждые 60 секунд
            await asyncio.sleep(60)

    async def stop(self):
        """Остановка агента"""
        self.is_running = False
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.context = None
            self.page = None
        logger.info("👋 Avito Browser Agent остановлен")

    async def disconnect(self):
        """Отключение от Avito"""
        await self.stop()


# ========== Глобальный экземпляр ==========

agent: Optional[AvitoBrowserAgent] = None


async def get_agent() -> AvitoBrowserAgent:
    """Получить экземпляр агента"""
    global agent
    if agent is None:
        agent = AvitoBrowserAgent()
    return agent


async def run_avito_browser_agent():
    """Точка входа для запуска агента"""
    global agent
    
    # Инициализация БД
    await db.connect()
    
    agent = AvitoBrowserAgent()
    
    try:
        await agent.start()
    except KeyboardInterrupt:
        logger.info("👋 Остановка по сигналу...")
    finally:
        await agent.stop()
        await db.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    asyncio.run(run_avito_browser_agent())

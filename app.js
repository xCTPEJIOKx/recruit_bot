// Telegram Web App JavaScript
const tg = window.Telegram.WebApp;

// Инициализация
tg.ready();
tg.expand();

// Парсинг параметров URL
const urlParams = new URLSearchParams(window.location.search);
const action = urlParams.get('action');
const vacancyId = urlParams.get('vacancy_id');

// Данные для квалификации
let qualificationData = {
    name: '',
    phone: '',
    experience: '',
    schedule: '',
    salary: '',
    vacancy_id: null
};

let currentStep = 1;
const totalSteps = 5;

// Пример данных вакансий (в реальности загружать с сервера)
let vacancies = [];

// Загрузка вакансий
async function loadVacancies() {
    showLoading();

    try {
        // Загружаем вакансии из API Web Dashboard
        const response = await fetch('/api/vacancies');
        const data = await response.json();
        vacancies = data.vacancies || [];

        renderVacancies();
    } catch (error) {
        console.error('Ошибка загрузки вакансий:', error);
        tg.showAlert('Ошибка загрузки вакансий');
    }
}

// Отображение вакансий
function renderVacancies() {
    const container = document.getElementById('vacancies-list');

    if (vacancies.length === 0) {
        container.innerHTML = '<p class="text-center text-muted">Нет доступных вакансий</p>';
        return;
    }

    container.innerHTML = vacancies.map(vac => `
        <div class="vacancy-card fade-in">
            <div class="vacancy-title">${vac.title}</div>
            ${vac.salary_min ? `<div class="vacancy-salary">💰 ${formatSalary(vac.salary_min)}${vac.salary_max ? ' - ' + formatSalary(vac.salary_max) : ''}</div>` : ''}
            <div class="vacancy-description">${vac.description}</div>
            <button class="btn btn-primary w-100 mt-3" onclick="startQualification(${vac.id})">
                📝 Откликнуться
            </button>
        </div>
    `).join('');
}

// Форматирование зарплаты
function formatSalary(amount) {
    return new Intl.NumberFormat('ru-RU').format(amount) + ' ₽';
}

// Показать загрузку
function showLoading() {
    const container = document.getElementById('vacancies-list');
    container.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p class="mt-3 text-muted">Загрузка вакансий...</p>
        </div>
    `;
}

// Начать квалификацию
function startQualification(vacancy_id) {
    qualificationData.vacancy_id = vacancy_id;
    currentStep = 1;
    
    document.getElementById('vacancies-page').style.display = 'none';
    document.getElementById('qualification-page').style.display = 'block';
    
    showStep(1);
}

// Показать шаг
function showStep(step) {
    // Скрыть все шаги
    for (let i = 1; i <= totalSteps; i++) {
        document.getElementById(`step-${i}`).style.display = 'none';
    }
    
    // Показать текущий шаг
    document.getElementById(`step-${step}`).style.display = 'block';
    
    // Обновить прогресс
    const progress = (step / totalSteps) * 100;
    document.getElementById('progress-fill').style.width = `${progress}%`;
    document.getElementById('step-current').textContent = step;
    
    // Автофокус на поле ввода
    const input = document.querySelector(`#step-${step} input, #step-${step} textarea`);
    if (input && step <= 3) {
        setTimeout(() => input.focus(), 100);
    }
}

// Следующий шаг
function nextStep(current) {
    // Валидация
    if (!validateStep(current)) {
        return;
    }
    
    // Сохранить данные
    saveStepData(current);
    
    // Перейти к следующему шагу
    if (current < totalSteps) {
        currentStep = current + 1;
        showStep(currentStep);
    }
}

// Предыдущий шаг
function prevStep(current) {
    if (current > 1) {
        currentStep = current - 1;
        showStep(currentStep);
    }
}

// Валидация шага
function validateStep(step) {
    switch(step) {
        case 1:
            const name = document.getElementById('qual-name').value.trim();
            if (!name) {
                tg.showAlert('Пожалуйста, введите ваше имя');
                return false;
            }
            if (name.length < 2) {
                tg.showAlert('Имя должно быть не менее 2 символов');
                return false;
            }
            break;
        case 2:
            const phone = document.getElementById('qual-phone').value.trim();
            if (!phone) {
                tg.showAlert('Пожалуйста, введите ваш телефон');
                return false;
            }
            if (phone.length < 10) {
                tg.showAlert('Введите корректный номер телефона');
                return false;
            }
            break;
        case 3:
            const experience = document.getElementById('qual-experience').value.trim();
            if (!experience) {
                tg.showAlert('Пожалуйста, расскажите о вашем опыте');
                return false;
            }
            break;
        case 4:
            const schedule = document.getElementById('qual-schedule').value;
            if (!schedule) {
                tg.showAlert('Пожалуйста, выберите желаемый график');
                return false;
            }
            break;
        case 5:
            const salary = document.getElementById('qual-salary').value.trim();
            if (!salary) {
                tg.showAlert('Пожалуйста, укажите желаемую зарплату');
                return false;
            }
            break;
    }
    return true;
}

// Сохранить данные шага
function saveStepData(step) {
    switch(step) {
        case 1:
            qualificationData.name = document.getElementById('qual-name').value.trim();
            break;
        case 2:
            qualificationData.phone = document.getElementById('qual-phone').value.trim();
            break;
        case 3:
            qualificationData.experience = document.getElementById('qual-experience').value.trim();
            break;
        case 4:
            // Сохраняется в selectOption
            break;
        case 5:
            qualificationData.salary = document.getElementById('qual-salary').value.trim();
            break;
    }
}

// Выбор опции (график)
function selectOption(type, value) {
    // Убрать выделение со всех опций
    document.querySelectorAll('.option-card').forEach(card => {
        card.classList.remove('selected');
    });
    
    // Выделить выбранную опцию
    event.currentTarget.classList.add('selected');
    
    // Сохранить значение
    document.getElementById('qual-schedule').value = value;
    qualificationData.schedule = value;
    
    // Вибрация (Haptic Feedback)
    tg.HapticFeedback?.selectionChanged();
}

// Отправить заявку
async function submitApplication() {
    // Валидация последнего шага
    if (!validateStep(5)) {
        return;
    }

    // Сохранить зарплату
    saveStepData(5);

    // Показать кнопку "Отправка..."
    const btn = document.querySelector('.btn-submit');
    const originalText = btn.textContent;
    btn.textContent = '⏳ Отправка...';
    btn.disabled = true;

    try {
        // Отправка данных на API
        // Публичный API через localtunnel
        const API_URL = 'https://tiny-toys-tickle.loca.lt/api/candidates';
        
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: qualificationData.name,
                phone: qualificationData.phone,
                experience: qualificationData.experience,
                schedule: qualificationData.schedule,
                salary: parseInt(qualificationData.salary) || 0,
                vacancy_id: qualificationData.vacancy_id ? String(qualificationData.vacancy_id) : null,
                source: 'telegram_webapp',
                status: 'new'
            })
        });

        if (!response.ok) {
            throw new Error('Ошибка сервера: ' + response.status);
        }

        const result = await response.json();
        console.log('Кандидат создан:', result);

        // Логирование в Telegram
        tg.sendData(JSON.stringify(qualificationData));

        // Показать успех
        document.getElementById('qualification-page').style.display = 'none';
        document.getElementById('success-page').style.display = 'block';

        // Вибрация успеха
        tg.HapticFeedback?.notification('success');

    } catch (error) {
        console.error('Ошибка отправки:', error);
        // При ошибке всё равно показываем успех (для демо)
        document.getElementById('qualification-page').style.display = 'none';
        document.getElementById('success-page').style.display = 'block';
        tg.HapticFeedback?.notification('success');
    }
}

// Показать вакансии (сброс)
function showVacancies() {
    document.getElementById('vacancies-page').style.display = 'block';
    document.getElementById('qualification-page').style.display = 'none';
    document.getElementById('success-page').style.display = 'none';
    
    // Сброс формы
    document.getElementById('qual-name').value = '';
    document.getElementById('qual-phone').value = '';
    document.getElementById('qual-experience').value = '';
    document.getElementById('qual-schedule').value = '';
    document.getElementById('qual-salary').value = '';
    qualificationData = { name: '', phone: '', experience: '', schedule: '', salary: '', vacancy_id: null };
}

// Маска для телефона
document.addEventListener('DOMContentLoaded', function() {
    const phoneInput = document.getElementById('qual-phone');
    
    if (phoneInput) {
        phoneInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            
            // Удаляем всё кроме цифр
            if (value.length === 0) {
                e.target.value = '';
                return;
            }
            
            // Если начинается с 8, заменяем на 7
            if (value[0] === '8') {
                value = '7' + value.substring(1);
            }
            // Если не начинается с 7, добавляем 7
            if (value[0] !== '7') {
                value = '7' + value;
            }
            
            // Ограничиваем 11 цифрами
            if (value.length > 11) {
                value = value.substring(0, 11);
            }
            
            // Форматируем: +7 (XXX) XXX-XX-XX
            let formatted = '+7';
            if (value.length > 1) {
                formatted += ' (' + value.substring(1, 4);
            }
            if (value.length >= 5) {
                formatted += ') ' + value.substring(4, 7);
            }
            if (value.length >= 8) {
                formatted += '-' + value.substring(7, 9);
            }
            if (value.length >= 10) {
                formatted += '-' + value.substring(9, 11);
            }
            
            e.target.value = formatted;
        });
        
        // Обработка удаления (backspace)
        phoneInput.addEventListener('keydown', function(e) {
            if (e.key === 'Backspace' && e.target.value === '+7 ') {
                e.target.value = '';
            }
        });
        
        // При потере фокуса проверяем длину
        phoneInput.addEventListener('blur', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length < 11) {
                e.target.value = '';
            }
        });
    }
    
    // Загрузка вакансий после загрузки DOM
    loadVacancies();
});

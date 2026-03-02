// Telegram Web App JavaScript
const tg = window.Telegram.WebApp;

// Инициализация
tg.ready();
tg.expand();

// Парсинг параметров URL
const urlParams = new URLSearchParams(window.location.search);
const action = urlParams.get('action');
const vacancyId = urlParams.get('vacancy_id');

// Пример данных вакансий (в реальности загружать с сервера)
let vacancies = [];

// Загрузка вакансий
async function loadVacancies() {
    showLoading();
    
    try {
        // В реальности: fetch('/api/vacancies')
        // Для примера - моковые данные
        vacancies = [
            {
                id: 1,
                title: "Менеджер по продажам",
                salary_min: 50000,
                salary_max: 100000,
                description: "Ищем активного менеджера по продажам. Опыт работы от 1 года. Удалённая работа."
            },
            {
                id: 2,
                title: "Оператор колл-центра",
                salary_min: 40000,
                salary_max: 60000,
                description: "Приём входящих звонков, консультация клиентов. Обучение предоставляется."
            },
            {
                id: 3,
                title: "Помощник руководителя",
                salary_min: 60000,
                salary_max: 80000,
                description: "Организационная поддержка, ведение документации. Офис в центре."
            }
        ];
        
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
            <button class="btn btn-primary w-100 mt-3" onclick="showApplyForm(${vac.id})">
                📝 Откликнуться
            </button>
        </div>
    `).join('');
}

// Форматирование зарплаты
function formatSalary(amount) {
    return new Intl.NumberFormat('ru-RU').format(amount) + ' ₽';
}

// Показать страницу отклика
function showApplyForm(vacancy_id) {
    document.getElementById('vacancies-page').style.display = 'none';
    document.getElementById('apply-page').style.display = 'block';
    document.getElementById('vacancy-id').value = vacancy_id;
    
    // Найти вакансию и показать в заголовке
    const vac = vacancies.find(v => v.id === vacancy_id);
    if (vac) {
        document.querySelector('#apply-page h2').textContent = `📝 Отклик: ${vac.title}`;
    }
}

// Показать вакансии
function showVacancies() {
    document.getElementById('vacancies-page').style.display = 'block';
    document.getElementById('apply-page').style.display = 'none';
    document.getElementById('success-page').style.display = 'none';
}

// Показать успех
function showSuccess() {
    document.getElementById('apply-page').style.display = 'none';
    document.getElementById('success-page').style.display = 'block';
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

// Отправка формы
document.getElementById('apply-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const data = {
        vacancy_id: document.getElementById('vacancy-id').value,
        name: document.getElementById('name').value,
        phone: document.getElementById('phone').value,
        experience: document.getElementById('experience').value,
        resume_link: document.getElementById('resume_link').value,
        telegram_username: tg.initDataUnsafe?.user?.username || ''
    };
    
    // В реальности: fetch('/api/apply', { method: 'POST', body: JSON.stringify(data) })
    console.log('Отправка отклика:', data);
    
    // Сохранение в базу (через API бота)
    try {
        // Отправляем данные боту
        tg.sendData(JSON.stringify(data));
        
        // Показываем успех
        showSuccess();
        
        // Вибрация для обратной связи
        tg.HapticFeedback.notificationOccurred('success');
    } catch (error) {
        console.error('Ошибка отправки:', error);
        tg.showAlert('Ошибка при отправке отклика');
    }
});

// Инициализация при загрузке
if (action === 'apply' && vacancyId) {
    showApplyForm(vacancyId);
} else {
    loadVacancies();
}

// Настройка темы
document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color || '#ffffff');
document.documentElement.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color || '#000000');
document.documentElement.style.setProperty('--tg-theme-hint-color', tg.themeParams.hint_color || '#999999');
document.documentElement.style.setProperty('--tg-theme-link-color', tg.themeParams.link_color || '#2481cc');
document.documentElement.style.setProperty('--tg-theme-button-color', tg.themeParams.button_color || '#2481cc');
document.documentElement.style.setProperty('--tg-theme-button-text-color', tg.themeParams.button_text_color || '#ffffff');

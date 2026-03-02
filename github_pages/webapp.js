/**
 * Telegram Web App для Recruitment System
 * Синхронизировано с Web Dashboard - одни данные для всех интерфейсов
 */

// Инициализация Telegram Web App
const tg = window.Telegram.WebApp;

// Конфигурация API - авто-определение URL
function getApiBase() {
    // Если открыты через Cloudflare tunnel - используем тот же домен
    const currentHost = window.location.hostname;
    if (currentHost.includes('trycloudflare.com') || currentHost.includes('ngrok') || currentHost.includes('cloudflare')) {
        return `https://${currentHost}`;
    }
    // Локальная разработка
    return 'http://localhost:8000';
}

const API_BASE = getApiBase();

// Состояние приложения
let currentUser = null;
let candidates = [];
let vacancies = [];
let contacts = []; // Контакты для связи

// API endpoints (без префикса /api/ для совместимости)
const API = {
    dashboard: '/dashboard',
    candidates: '/candidates',
    vacancies: '/vacancies',
    settings: '/api/settings',  // Этот endpoint нужно добавить
    candidate: (id) => `/candidates/${id}`,
    candidateStatus: (id) => `/candidates/${id}/status`,
};

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

function initApp() {
    // Готово
    tg.ready();
    
    // Разворачиваем на весь экран
    tg.expand();
    
    // Получаем данные пользователя
    currentUser = tg.initDataUnsafe.user;
    
    if (currentUser) {
        updateUserInfo();
    }
    
    // Устанавливаем цвета темы
    updateThemeColors();
    
    // Настраиваем главную кнопку
    setupMainButton();
    
    // Загружаем данные
    loadDashboard();
    loadVacancies();
}

function updateUserInfo() {
    const name = `${currentUser.first_name} ${currentUser.last_name || ''}`.trim();
    const username = currentUser.username ? `@${currentUser.username}` : '';
    
    document.getElementById('userName').textContent = name;
    document.getElementById('profileName').textContent = name;
    document.getElementById('profileUsername').textContent = username || 'Нет username';
    document.getElementById('profileId').textContent = currentUser.id;
    document.getElementById('profileLang').textContent = currentUser.language_code || 'ru';
    
    // Аватар с первой буквой
    const initial = currentUser.first_name[0].toUpperCase();
    document.getElementById('userAvatar').textContent = initial;
    document.getElementById('profileAvatar').textContent = initial;
}

function updateThemeColors() {
    const root = document.documentElement;
    
    if (tg.themeParams) {
        root.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color || '#ffffff');
        root.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color || '#000000');
        root.style.setProperty('--tg-theme-hint-color', tg.themeParams.hint_color || '#999999');
        root.style.setProperty('--tg-theme-link-color', tg.themeParams.link_color || '#2481cc');
        root.style.setProperty('--tg-theme-button-color', tg.themeParams.button_color || '#2481cc');
        root.style.setProperty('--tg-theme-button-text-color', tg.themeParams.button_text_color || '#ffffff');
    }
}

function setupMainButton() {
    tg.MainButton.setText('ОТПРАВИТЬ ЗАЯВКУ');
    tg.MainButton.onClick(() => {
        submitApplicationFromMain();
    });
}

function showMainButton() {
    tg.MainButton.show();
    tg.MainButton.enable();
}

function hideMainButton() {
    tg.MainButton.hide();
}

function toggleMainButton() {
    if (tg.MainButton.isVisible) {
        hideMainButton();
    } else {
        showMainButton();
    }
}

// Навигация
function showPage(pageId) {
    // Скрываем все страницы
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    
    // Показываем нужную
    document.getElementById(`page-${pageId}`).classList.add('active');
    
    // Обновляем навигацию
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.page === pageId) {
            item.classList.add('active');
        }
    });
    
    // Загружаем данные для страницы
    switch(pageId) {
        case 'home':
            loadDashboard();
            hideMainButton();
            break;
        case 'candidates':
            loadCandidates();
            hideMainButton();
            break;
        case 'apply':
            loadVacanciesForSelect();
            showMainButton();
            break;
        case 'vacancies':
            loadVacancies();
            hideMainButton();
            break;
        case 'contacts':
            loadContacts();
            hideMainButton();
            break;
        case 'profile':
            hideMainButton();
            break;
    }
    
    // Haptic feedback
    tg.HapticFeedback.impactOccurred('light');
}

// Загрузка дашборда
async function loadDashboard() {
    try {
        const response = await fetch(`${API_BASE}/api/dashboard`);
        const data = await response.json();
        
        const stats = data.stats.candidates_by_status;
        
        document.getElementById('statTotal').textContent = data.stats.total || Object.values(stats).reduce((a, b) => a + b, 0);
        document.getElementById('statNew').textContent = stats.new || 0;
        document.getElementById('statContacted').textContent = stats.contacted || 0;
        document.getElementById('statHired').textContent = stats.hired || 0;
        
        // Загружаем недавних кандидатов
        loadRecentCandidates();
        
    } catch (error) {
        console.error('Ошибка загрузки дашборда:', error);
        showToast('Ошибка загрузки данных', 'error');
    }
}

// Загрузка недавних кандидатов
async function loadRecentCandidates() {
    try {
        const response = await fetch(`${API_BASE}/api/candidates?limit=5`);
        const data = await response.json();
        
        const container = document.getElementById('recentCandidates');
        
        if (!data.candidates || data.candidates.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-inbox"></i>
                    <h3>Нет кандидатов</h3>
                    <p>Первыми откликнитесь на вакансию!</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = data.candidates.slice(0, 5).map(c => `
            <div class="candidate-item">
                <div class="candidate-avatar">${c.name ? c.name[0].toUpperCase() : '?'}</div>
                <div class="candidate-info">
                    <div class="candidate-name">${c.name || 'Аноним'}</div>
                    <div class="candidate-phone">${c.phone || 'Нет телефона'}</div>
                </div>
                <span class="status-badge status-${c.status}">${getStatusEmoji(c.status)} ${c.status}</span>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Ошибка:', error);
    }
}

// Загрузка кандидатов
async function loadCandidates() {
    const statusFilter = document.getElementById('statusFilter').value;
    const container = document.getElementById('candidatesList');
    
    container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    
    try {
        let url = `${API_BASE}/api/candidates?limit=100`;
        if (statusFilter) {
            url = `${API_BASE}/api/candidates?status=${statusFilter}`;
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        candidates = data.candidates || [];
        
        if (candidates.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-users"></i>
                    <h3>Нет кандидатов</h3>
                    <p>Кандидаты появятся здесь после откликов</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = candidates.map(c => `
            <div class="candidate-item">
                <div class="candidate-avatar">${c.name ? c.name[0].toUpperCase() : '?'}</div>
                <div class="candidate-info">
                    <div class="candidate-name">${c.name || 'Аноним'}</div>
                    <div class="candidate-phone">${c.phone || 'Нет телефона'}</div>
                </div>
                <div class="candidate-actions">
                    <button class="action-btn approve" onclick="updateCandidateStatus('${c.id}', 'qualified')">
                        <i class="fas fa-check"></i>
                    </button>
                    <button class="action-btn reject" onclick="updateCandidateStatus('${c.id}', 'rejected')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Ошибка:', error);
        container.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><h3>Ошибка загрузки</h3></div>';
    }
}

// Обновление статуса кандидата
async function updateCandidateStatus(candidateId, newStatus) {
    tg.HapticFeedback.impactOccurred('medium');
    
    try {
        const response = await fetch(`${API_BASE}/api/candidates/${candidateId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ new_status: newStatus })
        });
        
        if (response.ok) {
            showToast(`Статус обновлён: ${newStatus}`, 'success');
            loadCandidates();
            loadDashboard();
        } else {
            showToast('Ошибка обновления', 'error');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showToast('Ошибка сети', 'error');
    }
}

// Загрузка вакансий для select
async function loadVacanciesForSelect() {
    const select = document.getElementById('vacancySelect');
    
    try {
        const response = await fetch(`${API_BASE}/api/vacancies`);
        const data = await response.json();
        
        vacancies = data.vacancies || [];
        
        if (vacancies.length === 0) {
            select.innerHTML = '<option value="">Нет активных вакансий</option>';
            return;
        }
        
        select.innerHTML = '<option value="">Выберите вакансию</option>' + 
            vacancies.map(v => `<option value="${v.id}">${v.title}</option>`).join('');
        
    } catch (error) {
        console.error('Ошибка:', error);
    }
}

// Загрузка вакансий
async function loadVacancies() {
    const container = document.getElementById('vacanciesList');
    
    try {
        const response = await fetch(`${API_BASE}/api/vacancies`);
        const data = await response.json();
        
        vacancies = data.vacancies || [];
        
        if (vacancies.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-briefcase"></i>
                    <h3>Нет вакансий</h3>
                    <p>Активные вакансии появятся здесь</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = vacancies.map(v => {
            const salary = formatSalary(v.salary_min, v.salary_max);
            return `
                <div class="card vacancy-card">
                    <div class="vacancy-title">${v.title}</div>
                    ${salary ? `<div class="vacancy-salary">${salary}</div>` : ''}
                    <div class="vacancy-desc">${v.description || 'Описание вакансии'}</div>
                    <button class="btn btn-primary" style="margin-top: 12px;" onclick="applyForVacancy('${v.id}')">
                        <i class="fas fa-paper-plane"></i>
                        Откликнуться
                    </button>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Ошибка:', error);
        container.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><h3>Ошибка загрузки</h3></div>';
    }
}

function formatSalary(min, max) {
    if (!min && !max) return '';
    if (min && max) return `${formatNumber(min)} - ${formatNumber(max)} ₽`;
    if (min) return `от ${formatNumber(min)} ₽`;
    return `до ${formatNumber(max)} ₽`;
}

function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}

// Отклик на вакансию
function applyForVacancy(vacancyId) {
    showPage('apply');
    document.getElementById('vacancySelect').value = vacancyId;
}

// Отправка заявки
async function submitApplication(event) {
    event.preventDefault();
    
    tg.HapticFeedback.impactOccurred('medium');
    
    const form = event.target;
    const formData = new FormData(form);
    
    const data = {
        name: formData.get('name'),
        phone: formData.get('phone'),
        vacancy_id: formData.get('vacancy_id'),
        source: 'telegram_webapp',
        notes: `Опыт: ${formData.get('experience')}, График: ${formData.get('schedule')}, Ожидаемая ЗП: ${formData.get('expected_salary')}`
    };
    
    // Добавляем данные пользователя Telegram
    if (currentUser) {
        data.telegram_id = currentUser.id;
        data.telegram_username = currentUser.username;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/candidates`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            const result = await response.json();
            showToast('Заявка отправлена!', 'success');
            
            // Закрываем главную кнопку
            hideMainButton();
            
            // Очищаем форму
            form.reset();
            
            // Возвращаемся на главную
            setTimeout(() => {
                showPage('home');
            }, 1000);
        } else {
            showToast('Ошибка отправки', 'error');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showToast('Ошибка сети', 'error');
    }
}

function submitApplicationFromMain() {
    const form = document.getElementById('applyForm');
    if (form.checkValidity()) {
        submitApplication({ preventDefault: () => {}, target: form });
    } else {
        form.reportValidity();
        tg.HapticFeedback.notificationOccurred('error');
    }
}

// Утилиты
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function getStatusEmoji(status) {
    const emojis = {
        'new': '🆕',
        'contacted': '📞',
        'qualified': '✅',
        'interview': '📅',
        'offer': '📋',
        'hired': '🎉',
        'rejected': '❌',
        'blacklist': '🚫'
    };
    return emojis[status] || '❓';
}

function closeApp() {
    tg.close();
}

// Загрузка контактов (синхронизировано с Dashboard)
async function loadContacts() {
    try {
        // Используем статические данные (те же что и в Dashboard)
        contacts = [
            {
                "name": "Отдел кадров",
                "role": "Рекрутинг",
                "phone": "+7 (999) 123-45-67",
                "email": "hr@company.com"
            },
            {
                "name": "Менеджер по персоналу",
                "role": "Главный менеджер",
                "phone": "+7 (999) 765-43-21",
                "email": "manager@company.com"
            }
        ];
        renderContacts();
    } catch (error) {
        console.error('Ошибка загрузки контактов:', error);
    }
}

// Отображение контактов
function renderContacts() {
    const container = document.getElementById('contactsList');
    if (!container) return;

    if (contacts.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-address-book"></i>
                <h3>Нет контактов</h3>
                <p>Контакты будут добавлены администратором</p>
            </div>
        `;
        return;
    }

    container.innerHTML = contacts.map(c => `
        <div class="card">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #667eea, #764ba2); display: flex; align-items: center; justify-content: center; color: white; font-weight: 700;">
                    ${c.name ? c.name[0].toUpperCase() : '👤'}
                </div>
                <div style="flex: 1;">
                    <div style="font-weight: 600;">${c.name || 'Контакт'}</div>
                    <div style="font-size: 13px; color: var(--tg-theme-hint-color);">${c.role || ''}</div>
                </div>
                ${c.phone ? `<a href="tel:${c.phone}" style="color: var(--primary); text-decoration: none;">
                    <i class="fas fa-phone"></i>
                </a>` : ''}
            </div>
        </div>
    `).join('');
}

// Экспорт для глобального доступа
window.showPage = showPage;
window.loadCandidates = loadCandidates;
window.updateCandidateStatus = updateCandidateStatus;
window.submitApplication = submitApplication;
window.applyForVacancy = applyForVacancy;
window.toggleMainButton = toggleMainButton;
window.closeApp = closeApp;

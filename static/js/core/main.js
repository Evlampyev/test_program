// static/js/core/main.js

// Глобальные функции
window.App = {
    // Инициализация приложения
    init: function() {
        this.setupCSRF();
        this.initComponents();
    },

    // Настройка CSRF токена для AJAX
    setupCSRF: function() {
        this.csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

        // Добавляем CSRF во все fetch запросы
        const originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            options.headers = options.headers || {};
            options.headers['X-CSRFToken'] = App.csrftoken;
            options.credentials = 'same-origin';
            return originalFetch(url, options);
        };
    },

    // Инициализация всех компонентов
    initComponents: function() {
        this.initTooltips();
        this.initDropdowns();
    },

    // Утилиты
    utils: {
        formatDate: function(date) {
            return new Date(date).toLocaleString('ru-RU');
        },

        showNotification: function(message, type = 'info') {
            // Показать уведомление
            console.log(`[${type}]: ${message}`);
        },

        handleError: function(error) {
            console.error('Error:', error);
            this.showNotification(error.message || 'Произошла ошибка', 'error');
        }
    }
};

// Запуск при загрузке DOM
document.addEventListener('DOMContentLoaded', function() {
    App.init();
});
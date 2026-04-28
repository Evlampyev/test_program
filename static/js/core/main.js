// static/js/core/main.js

// Глобальные функции
window.App = {
    // Инициализация приложения
    init: function () {
        this.csrftoken = this.getCSRFToken();
        console.log('App инициализирован');
        // НЕ перехватываем fetch, чтобы не создавать проблем
        // this.setupFetchInterceptor();
        this.initComponents();
    },

    // Получение CSRF токена
    getCSRFToken: function () {
        // Из meta-тега (самый надежный способ)
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) return metaTag.getAttribute('content');

        // Из cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') return value;
        }

        return null;
    },

    // Инициализация всех компонентов
    initComponents: function () {
        this.initTooltips();
        this.initDropdowns();
    },

    // Инициализация тултипов Bootstrap
    initTooltips: function () {
        if (typeof bootstrap !== 'undefined') {
            const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
            tooltips.forEach(el => new bootstrap.Tooltip(el));
        }
    },

    // Инициализация дропдаунов Bootstrap
    initDropdowns: function () {
        if (typeof bootstrap !== 'undefined') {
            const dropdowns = document.querySelectorAll('[data-bs-toggle="dropdown"]');
            dropdowns.forEach(el => new bootstrap.Dropdown(el));
        }
    },

    // Утилиты
    utils: {
        formatDate: function (date) {
            return new Date(date).toLocaleString('ru-RU');
        },

        showNotification: function (message, type = 'info') {
            console.log(`[${type}]: ${message}`);
        },

        handleError: function (error) {
            console.error('Error:', error);
            this.showNotification(error.message || 'Произошла ошибка', 'error');
        }
    }
};

// Запуск при загрузке DOM
document.addEventListener('DOMContentLoaded', function () {
    App.init();
});

// скрытие Учительский портал при меньшем разрешении
function handleResize() {
    const element = document.querySelector('.teacher-portal');
    if (element) {
        if (window.innerWidth < 1300) {
            element.style.display = 'none';
        } else {
            element.style.display = 'inline-block';
        }
    }
}

window.addEventListener('resize', handleResize);
handleResize();



// // static/js/core/main.js
//
// // Глобальные функции
// window.App = {
//     // Инициализация приложения
//     init: function () {
//         this.csrftoken = this.getCSRFToken();
//         console.log('App инициализирован, CSRF токен:', this.csrftoken);
//         this.setupFetchInterceptor();
//         this.initComponents();
//     },
//
//     // Получение CSRF токена
//     getCSRFToken: function () {
//         // Из скрытого поля
//         const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
//         if (csrfInput) return csrfInput.value;
//
//         // Из meta-тега
//         const metaTag = document.querySelector('meta[name="csrf-token"]');
//         if (metaTag) return metaTag.getAttribute('content');
//
//         // Из cookie
//         const cookies = document.cookie.split(';');
//         for (let cookie of cookies) {
//             const [name, value] = cookie.trim().split('=');
//             if (name === 'csrftoken') return value;
//         }
//
//         return null;
//     },
//
//     // Настройка перехвата fetch запросов (только для POST/PUT/DELETE)
//     setupFetchInterceptor: function () {
//         const originalFetch = window.fetch;
//         const self = this;
//
//         window.fetch = function (url, options = {}) {
//             options = options || {};
//             options.headers = options.headers || {};
//             options.credentials = 'same-origin';
//
//             // Добавляем CSRF-токен только для методов, которые его требуют
//             const method = (options.method || 'GET').toUpperCase();
//             const methodsRequiringCSRF = ['POST', 'PUT', 'PATCH', 'DELETE'];
//
//             if (methodsRequiringCSRF.includes(method) && self.csrftoken) {
//                 options.headers['X-CSRFToken'] = self.csrftoken;
//                 console.log(`Добавлен CSRF токен для ${method} запроса к ${url}`);
//             }
//
//             return originalFetch(url, options);
//         };
//     },
//
//     // Инициализация всех компонентов
//     initComponents: function () {
//         this.initTooltips();
//         this.initDropdowns();
//     },
//
//     // Инициализация тултипов Bootstrap
//     initTooltips: function () {
//         if (typeof bootstrap !== 'undefined') {
//             const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
//             tooltips.forEach(el => new bootstrap.Tooltip(el));
//         }
//     },
//
//     // Инициализация дропдаунов Bootstrap
//     initDropdowns: function () {
//         if (typeof bootstrap !== 'undefined') {
//             const dropdowns = document.querySelectorAll('[data-bs-toggle="dropdown"]');
//             dropdowns.forEach(el => new bootstrap.Dropdown(el));
//         }
//     },
//
//     // Утилиты
//     utils: {
//         formatDate: function (date) {
//             return new Date(date).toLocaleString('ru-RU');
//         },
//
//         showNotification: function (message, type = 'info') {
//             console.log(`[${type}]: ${message}`);
//         },
//
//         handleError: function (error) {
//             console.error('Error:', error);
//             this.showNotification(error.message || 'Произошла ошибка', 'error');
//         }
//     }
// };
//
// // Запуск при загрузке DOM
// document.addEventListener('DOMContentLoaded', function () {
//     App.init();
// });
// // скрытие Учительский портал при меньшем разрешении
// function handleResize() {
//     const element = document.querySelector('.teacher-portal');
//     if (window.innerWidth < 1300) {
//         element.style.display = 'none';
//     } else {
//         element.style.display = 'inline-block';
//     }
// }
//
// window.addEventListener('resize', handleResize);
// handleResize(); // Вызов при загрузке
//

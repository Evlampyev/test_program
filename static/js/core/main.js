// // static/js/core/main.js
//
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
    },

    // Уведомления в стиле django (добавлено без перезаписи объекта)
    showMessage: function (message, type = 'info') {
        const messagesContainer = document.querySelector('.main-content .container');
        if (!messagesContainer) return;

        let alertClass = '';
        let icon = '';

        switch (type) {
            case 'success':
                alertClass = 'alert-success';
                icon = '✅';
                break;
            case 'error':
                alertClass = 'alert-danger';
                icon = '❌';
                break;
            case 'warning':
                alertClass = 'alert-warning';
                icon = '⚠️';
                break;
            default:
                alertClass = 'alert-info';
                icon = 'ℹ️';
        }

        const alertDiv = document.createElement('div');
        alertDiv.className = `alert ${alertClass} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${icon} ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        messagesContainer.insertBefore(alertDiv, messagesContainer.firstChild);

        setTimeout(() => {
            alertDiv.classList.remove('show');
            setTimeout(() => alertDiv.remove(), 300);
        }, 5000);
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

(function() {
    // Функция автоматического скрытия одного алерта
    function autoHideAlert(alertElement) {
        if (alertElement.dataset.autoHide === 'true') return;
        alertElement.dataset.autoHide = 'true';
        setTimeout(() => {
            alertElement.classList.remove('show');
            setTimeout(() => alertElement.remove(), 300);
        }, 5000);
    }

    // Инициализация существующих алертов
    function initAlerts() {
        document.querySelectorAll('.alert').forEach(autoHideAlert);
    }

    // MutationObserver для отслеживания появления новых алертов
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType === 1) {
                    // Если сам узел – alert
                    if (node.classList && node.classList.contains('alert')) {
                        autoHideAlert(node);
                    }
                    // Если внутри узла есть дочерние alert
                    if (node.querySelectorAll) {
                        node.querySelectorAll('.alert').forEach(autoHideAlert);
                    }
                }
            });
        });
    });
    observer.observe(document.body, { childList: true, subtree: true });

    // Запуск при загрузке страницы
    document.addEventListener('DOMContentLoaded', initAlerts);
})();


// // Глобальные функции
// window.App = {
//     // Инициализация приложения
//     init: function () {
//         this.csrftoken = this.getCSRFToken();
//         console.log('App инициализирован');
//         // НЕ перехватываем fetch, чтобы не создавать проблем
//         // this.setupFetchInterceptor();
//         this.initComponents();
//     },
//
//     // Получение CSRF токена
//     getCSRFToken: function () {
//         // Из meta-тега (самый надежный способ)
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
//
// // скрытие Учительский портал при меньшем разрешении
// function handleResize() {
//     const element = document.querySelector('.teacher-portal');
//     if (element) {
//         if (window.innerWidth < 1300) {
//             element.style.display = 'none';
//         } else {
//             element.style.display = 'inline-block';
//         }
//     }
// }
//
// window.addEventListener('resize', handleResize);
// handleResize();
//
// // Уведомления в стиле django
// window.App = {
//     // ... существующий код ...
//
//     showMessage: function (message, type = 'info') {
//         const messagesContainer = document.querySelector('.main-content .container');
//         if (!messagesContainer) return;
//
//         let alertClass = '';
//         let icon = '';
//
//         switch (type) {
//             case 'success':
//                 alertClass = 'alert-success';
//                 icon = '✅';
//                 break;
//             case 'error':
//                 alertClass = 'alert-danger';
//                 icon = '❌';
//                 break;
//             case 'warning':
//                 alertClass = 'alert-warning';
//                 icon = '⚠️';
//                 break;
//             default:
//                 alertClass = 'alert-info';
//                 icon = 'ℹ️';
//         }
//
//         const alertDiv = document.createElement('div');
//         alertDiv.className = `alert ${alertClass} alert-dismissible fade show`;
//         alertDiv.innerHTML = `
//             ${icon} ${message}
//             <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
//         `;
//
//         messagesContainer.insertBefore(alertDiv, messagesContainer.firstChild);
//
//         setTimeout(() => {
//             alertDiv.classList.remove('show');
//             setTimeout(() => alertDiv.remove(), 300);
//         }, 5000);
//     }
// };
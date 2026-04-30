// Функция получения CSRF токена
function getCsrfToken() {
    // Из meta-тега
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag) return metaTag.getAttribute('content');

    // Из cookie
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') return value;
    }

    return null;
}

// Загрузка уведомлений
function loadNotifications() {
    // Проверяем, есть ли элемент для уведомлений (только для учителя)
    const badge = document.getElementById('notificationBadge');
    if (!badge) return; // Если нет элемента - выходим

    fetch('/notifications/api/', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'  // Важно для передачи cookies
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.unread_count > 0) {
                badge.textContent = data.unread_count;
                badge.style.display = 'inline';
            } else {
                badge.style.display = 'none';
            }

            const list = document.getElementById('notificationsList');
            if (list && data.notifications?.length) {
                list.innerHTML = data.notifications.map(n => `
                    <div class="dropdown-item notification-item ${n.is_read ? '' : 'unread'}"
                         data-id="${n.id}"
                         onclick="markNotificationRead(${n.id})">
                        <div class="d-flex">
<!--                            <div class="me-2">✔️</div>-->
                            <div style="flex: 1;">
                                <div class="d-flex justify-content-between">
                                    <strong class="small">${escapeHtml(n.title)}</strong>
                                    <small class="text-muted ms-2">${n.created_at}</small>
                                </div>
                                <p class="small text-muted mb-1">${escapeHtml(n.message)}</p>
                                <small class="text-primary">Задача #${n.task_id}</small>
                                ${n.task_level ? `<span class="badge-level level-${n.task_level} ms-2"><small><i class="fas fa-signal me-1"></i>Уровень ${n.task_level}</small></span>` : ''}
                            </div>
                        </div>
                    </div>
                `).join('');
            } else if (list) {
                list.innerHTML = '<div class="text-center py-4 text-muted">Нет уведомлений</div>';
            }
        })
        .catch(error => {
            console.error('Ошибка загрузки уведомлений:', error);
            // Не показываем ошибку пользователю, просто логируем
        });
}

// Функция для экранирования HTML (безопасность)
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Отметить одно уведомление
function markNotificationRead(id) {
    fetch(`/notifications/api/${id}/read/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        credentials: 'same-origin'
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) loadNotifications();
        })
        .catch(error => console.error('Ошибка:', error));
}

// Отметить все
function markAllNotificationsRead() {
    fetch('/notifications/api/read-all/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        credentials: 'same-origin'
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) loadNotifications();
        })
        .catch(error => console.error('Ошибка:', error));
}

// Загружаем при старте (только если есть элемент уведомлений)
document.addEventListener('DOMContentLoaded', function () {
    // Проверяем, есть ли элемент для уведомлений
    const badge = document.getElementById('notificationBadge');
    if (badge) {
        loadNotifications();
        // Обновляем каждые 30 секунд
        setInterval(loadNotifications, 30000);
    }
});


// function loadNotifications() {
//     fetch('/notifications/api/')
//         .then(response => response.json())
//         .then(data => {
//             const badge = document.getElementById('notificationBadge');
//             if (data.unread_count > 0) {
//                 badge.textContent = data.unread_count;
//                 badge.style.display = 'inline';
//             } else {
//                 badge.style.display = 'none';
//             }
//
//             const list = document.getElementById('notificationsList');
//             if (data.notifications?.length) {
//                 list.innerHTML = data.notifications.map(n => `
//                     <div class="dropdown-item notification-item ${n.is_read ? '' : 'unread'}"
//                          data-id="${n.id}"
//                          onclick="markNotificationRead(${n.id})">
//                         <div class="d-flex">
//                             <div class="me-2">✔️</div>
//                             <div>
//                                 <div class="d-flex justify-content-between">
//                                     <strong class="small">${n.title}</strong>
//                                     <small class="text-muted ms-2">${n.created_at}</small>
//                                 </div>
//                                 <p class="small text-muted mb-1" style="width: 100%" >${n.message}</p>
//                                 <small class="text-primary">Задача #${n.task_id}</small>
//                                  <span class="badge-level level-${n.task_level}"><small><i class="fas fa-signal me-1"></i>Уровень ${n.task_level}</small></span>
//                             </div>
//                         </div>
//                     </div>
//                 `).join('');
//             } else {
//                 list.innerHTML = '<div class="text-center py-4 text-muted">Нет уведомлений</div>';
//             }
//         })
//         .catch(error => console.error('Ошибка:', error));
// }
//
// // Отметить одно уведомление
// function markNotificationRead(id) {
//     fetch(`/notifications/api/${id}/read/`, {
//         method: 'POST'
//     })
//         .then(response => response.json())
//         .then(data => {
//             if (data.success) loadNotifications();
//         });
// }
//
// // Отметить все
// function markAllNotificationsRead() {
//     fetch('/notifications/api/read-all/', {
//         method: 'POST'
//     })
//         .then(response => response.json())
//         .then(data => {
//             if (data.success) loadNotifications();
//         });
// }
//
// // Загружаем при старте
// document.addEventListener('DOMContentLoaded', loadNotifications);
// setInterval(loadNotifications, 30000);


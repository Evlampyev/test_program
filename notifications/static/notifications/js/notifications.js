// Загрузка уведомлений
function loadNotifications() {
    fetch('/notifications/api/')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('notificationBadge');
            if (data.unread_count > 0) {
                badge.textContent = data.unread_count;
                badge.style.display = 'inline';
            } else {
                badge.style.display = 'none';
            }

            const list = document.getElementById('notificationsList');
            if (data.notifications?.length) {
                list.innerHTML = data.notifications.map(n => `
                    <div class="dropdown-item notification-item ${n.is_read ? '' : 'unread'}"
                         data-id="${n.id}"
                         onclick="markNotificationRead(${n.id})">
                        <div class="d-flex">
                            <div class="me-2">✔️</div>
                            <div>
                                <div class="d-flex justify-content-between">
                                    <strong class="small">${n.title}</strong>
                                    <small class="text-muted ms-2">${n.created_at}</small>
                                </div>
                                <p class="small text-muted mb-1">${n.message}</p>
                                <small class="text-primary">Задача #${n.task_id}</small>
                            </div>
                        </div>
                    </div>
                `).join('');
            } else {
                list.innerHTML = '<div class="text-center py-4 text-muted">Нет уведомлений</div>';
            }
        })
        .catch(error => console.error('Ошибка:', error));
}

// Отметить одно уведомление
function markNotificationRead(id) {
    fetch(`/notifications/api/${id}/read/`, {
        method: 'POST'
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) loadNotifications();
        });
}

// Отметить все
function markAllNotificationsRead() {
    fetch('/notifications/api/read-all/', {
        method: 'POST'
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) loadNotifications();
        });
}

// Загружаем при старте
document.addEventListener('DOMContentLoaded', loadNotifications);
setInterval(loadNotifications, 30000);


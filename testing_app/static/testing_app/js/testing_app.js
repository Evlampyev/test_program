// Анимация прогресс-бара при загрузке
document.addEventListener('DOMContentLoaded', function () {
    const progressFill = document.querySelector('.progress-fill');
    if (progressFill) {
        const targetWidth = progressFill.style.width;
        progressFill.style.width = '0%';
        setTimeout(() => {
            progressFill.style.width = targetWidth;
        }, 100);
    }
});



//из error.html

// Функция для повторного запуска тестов
async function retryTest(programId) {
    const btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '⏳ Запуск...';

    try {
        const response = await fetch(`/tester/run-tests/${programId}/`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if (response.ok) {
            window.location.href = `/tester/run-tests/${programId}/`;
        } else {
            alert('Ошибка при запуске тестов');
            btn.disabled = false;
            btn.innerHTML = '🔄 Повторить попытку';
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Ошибка при запуске тестов');
        btn.disabled = false;
        btn.innerHTML = '🔄 Повторить попытку';
    }
}

// Автоматическое копирование ошибки в буфер обмена (опционально)
function copyErrorToClipboard() {
    const errorText = document.querySelector('.error-stack')?.innerText;
    if (errorText) {
        navigator.clipboard.writeText(errorText).then(() => {
            alert('Текст ошибки скопирован в буфер обмена');
        });
    }
}

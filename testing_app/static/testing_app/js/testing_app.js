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
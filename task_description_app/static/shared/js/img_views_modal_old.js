// Класс для управления просмотром изображений
class ImageViewer {
    constructor() {
        this.createModal();
        this.bindEvents();
    }

    createModal() {
        // Создаем модальное окно, если его нет
        if (!document.querySelector('.image-viewer-modal')) {
            const modalHtml = `
                <div class="image-viewer-modal" id="imageViewerModal">
                    <div class="image-viewer-close" id="imageViewerClose">&times;</div>
                    <div class="image-viewer-content">
                        <img id="viewerImage" src="" alt="Увеличенное изображение">
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', modalHtml);
        }
    }

    bindEvents() {
        const modal = document.getElementById('imageViewerModal');
        const closeBtn = document.getElementById('imageViewerClose');
        const viewerImage = document.getElementById('viewerImage');

        // Закрытие по крестику
        if (closeBtn) {
            closeBtn.onclick = () => this.close();
        }

        // Закрытие по клику на фон
        if (modal) {
            modal.onclick = (e) => {
                if (e.target === modal) {
                    this.close();
                }
            };
        }

        // Закрытие по клавише ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen()) {
                this.close();
            }
        });
    }

    open(imageSrc) {
        const modal = document.getElementById('imageViewerModal');
        const viewerImage = document.getElementById('viewerImage');

        if (modal && viewerImage) {
            viewerImage.src = imageSrc;
            modal.style.display = 'block';
            document.body.style.overflow = 'hidden'; // Запрещаем скролл фона
        }
    }

    close() {
        const modal = document.getElementById('imageViewerModal');
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = ''; // Восстанавливаем скролл
        }
    }

    isOpen() {
        const modal = document.getElementById('imageViewerModal');
        return modal && modal.style.display === 'block';
    }
}

// Глобальный экземпляр просмотрщика
let imageViewer;

// Функция инициализации обработчиков для изображений
function initImageClickHandler() {
    // Находим все изображения внутри .markdown-content
    const images = document.querySelectorAll('.markdown-content img');

    images.forEach(img => {
        // Удаляем старый обработчик, если есть
        img.removeEventListener('click', imageClickHandler);
        // Добавляем новый
        img.addEventListener('click', imageClickHandler);
        // Добавляем атрибут title для подсказки
        img.title = 'Нажмите для увеличения';
        // Убеждаемся, что курсор - указатель
        img.style.cursor = 'pointer';
    });
}

// Обработчик клика по изображению
function imageClickHandler(e) {
    e.stopPropagation();
    if (imageViewer) {
        imageViewer.open(this.src);
    }
}

// Наблюдатель за изменениями DOM для динамически добавляемого контента
function observeDynamicContent() {
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            // Если добавлены новые узлы
            if (mutation.addedNodes.length) {
                // Проверяем, есть ли среди них .markdown-content или его родители
                const hasNewContent = Array.from(mutation.addedNodes).some(node => {
                    return node.nodeType === 1 && (
                        node.classList?.contains('markdown-content') ||
                        node.querySelector?.('.markdown-content')
                    );
                });

                if (hasNewContent) {
                    // Небольшая задержка для рендеринга DOM
                    setTimeout(initImageClickHandler, 100);
                }
            }
        });
    });

    observer.observe(document.body, {childList: true, subtree: true});
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function () {
    // Создаем просмотрщик изображений
    imageViewer = new ImageViewer();

    // Инициализируем обработчики для текущих изображений
    initImageClickHandler();

    // Запускаем наблюдение за динамическим контентом
    observeDynamicContent();
});

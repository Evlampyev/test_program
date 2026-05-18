// Обработка загрузки файла
document.getElementById('programUploadForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const formData = new FormData(this);
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const fileInput = document.getElementById('programFile');

    try {
        const response = await fetch('/upload/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrftoken,
            }
        });

        const data = await response.json();

        if (data.success) {
            window.App.showMessage('Файл успешно загружен!', 'success');
            // Очищаем поле выбора файла
            fileInput.value = '';
            // Сбрасываем отображение имени и содержимого
            document.getElementById('programFileName').textContent = 'Файл не выбран';
            // document.getElementById('programContent').innerHTML = '// Программа будет отображена после загрузки';
            if (data.program_id) {
                runTests(data.program_id);
            }
        } else {
            alert('Ошибка: ' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Ошибка при загрузке файла');
    }
});

// Запуск тестов
async function runTests(programId) {
    document.getElementById('testResults').style.display = 'block';
    document.getElementById('testResultsContent').innerHTML = '<p>Запуск тестов...</p>';

    try {
        const response = await fetch(`/tester/run-tests/${programId}/`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        const html = await response.text();
        document.getElementById('testResultsContent').innerHTML = html;

        // Обновляем статус
        updateTaskStatus(programId);
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('testResultsContent').innerHTML =
            '<p class="error">Ошибка при запуске тестов</p>';
    }
}

// Показать результаты предыдущей попытки
async function showResults(programId) {
    document.getElementById('testResults').style.display = 'block';
    await runTests(programId);
}

// Обновить статус задачи на странице
async function updateTaskStatus(programId) {
    // Здесь можно добавить AJAX запрос для обновления статуса
    // Или просто перезагрузить страницу
    // location.reload();
}

// Дополнительный JS для отображения содержимого файла
// document.getElementById('programFile').addEventListener('change', function (e) {
//     const file = e.target.files[0];
//     if (file) {
//         document.getElementById('programFileName').textContent = file.name;
//
//         // Читаем содержимое файла для предпросмотра
//         const reader = new FileReader();
//         reader.onload = function (e) {
//             document.getElementById('programContent').textContent = e.target.result;
//         };
//         reader.readAsText(file);
//     }
// });

// Инициализация highlight.js
hljs.highlightAll();

document.getElementById('programFile').addEventListener('change', function (e) {
    const file = e.target.files[0];
    if (file) {
        document.getElementById('programFileName').textContent = file.name;

        const reader = new FileReader();
        reader.onload = function (e) {
            const code = e.target.result;
            const preElement = document.getElementById('programContent');
            const codeElement = document.createElement('code');
            codeElement.className = 'language-python';
            codeElement.textContent = code;
            preElement.innerHTML = '';
            preElement.appendChild(codeElement);
            hljs.highlightElement(codeElement);
        };
        reader.readAsText(file);
    }
});

window.showResults = function (programId) {
    fetch(`/tester/run-tests/${programId}/`)
        .then(response => response.text())
        .then(html => {
            document.getElementById('testResults').style.display = 'block';
            document.getElementById('testResultsPlaceholder').style.display = 'none';
            document.getElementById('testResultsContent').innerHTML = html;
            // Переподсветка кода в результатах тестов
            document.querySelectorAll('#testResultsContent pre code').forEach((block) => {
                hljs.highlightBlock(block);
            });
        });
};

// Для обновления реальной структуры файлов

const express = require('express');
const fs = require('fs').promises;
const path = require('path');
const app = express();
const PORT = 3000;

app.use(express.static('public'));
app.use(express.json());

// Корневая папка с задачами
const TASKS_ROOT = path.join(__dirname, 'tasks');

// API для получения структуры папок
app.get('/api/structure', async (req, res) => {
    try {
        const structure = await getFolderStructure(TASKS_ROOT);
        res.json(structure);
    } catch (error) {
        res.status(500).json({error: error.message});
    }
});

// API для получения содержимого task.md
app.get('/api/task/*', async (req, res) => {
    try {
        const filePath = path.join(TASKS_ROOT, req.params[0], 'task.md');
        const content = await fs.readFile(filePath, 'utf-8');
        res.json({content});
    } catch (error) {
        res.status(404).json({error: 'task.md not found'});
    }
});

// API для получения списка файлов в папке задачи
app.get('/api/task-files/*', async (req, res) => {
    try {
        const taskPath = path.join(TASKS_ROOT, req.params[0]);
        const files = await fs.readdir(taskPath);
        res.json({files});
    } catch (error) {
        res.status(404).json({error: 'Task folder not found'});
    }
});

// Рекурсивное получение структуры папок
async function getFolderStructure(dirPath, relativePath = '') {
    const items = await fs.readdir(dirPath);
    const result = [];

    for (const item of items) {
        const fullPath = path.join(dirPath, item);
        const stat = await fs.stat(fullPath);
        const itemRelativePath = relativePath ? path.join(relativePath, item) : item;

        if (stat.isDirectory()) {
            // Проверяем, есть ли в папке task.md
            const children = await getFolderStructure(fullPath, itemRelativePath);
            const hasTaskMd = await checkForTaskMd(fullPath);

            // Определяем тип папки
            let type = 'folder';
            if (item.match(/^\d+\s*класс$/)) type = 'class';
            else if (item.match(/^Тема\s*№\d+$/)) type = 'topic';
            else if (item.match(/^Урок_\d+$/)) type = 'lesson';
            else if (item.match(/^level_[A-Z]$/)) type = 'level';

            result.push({
                name: item,
                type: type,
                path: itemRelativePath,
                hasTaskMd: hasTaskMd,
                children: children
            });
        } else if (item === 'task.md') {
            // Файлы task.md мы не добавляем как отдельные элементы,
            // они будут определяться через hasTaskMd в родительской папке
            continue;
        }
    }

    return result;
}

// Проверка наличия task.md в папке или подпапках
async function checkForTaskMd(dirPath) {
    try {
        const items = await fs.readdir(dirPath);
        for (const item of items) {
            const fullPath = path.join(dirPath, item);
            const stat = await fs.stat(fullPath);

            if (stat.isFile() && item === 'task.md') {
                return true;
            } else if (stat.isDirectory()) {
                const hasInSubdir = await checkForTaskMd(fullPath);
                if (hasInSubdir) return true;
            }
        }
        return false;
    } catch {
        return false;
    }
}

app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
    console.log(`Looking for tasks in: ${TASKS_ROOT}`);
});


// Для файла task_detail.html

// После вставки Markdown контента
function displayTask(content) {
    document.getElementById('taskContent').innerHTML = marked.parse(content);

    // Удалить все пустые блоки <pre><code>
    document.querySelectorAll('pre code').forEach(el => {
        if (el.innerHTML.trim() === '') {
            el.closest('pre').remove();
        }
    });
}

// Конец для файла task_detail.html


// Для файла task_list.html

// не переносится по хорошему

// Конец Для файла task_list.html


// для файла task_add.html

// не переносится по хорошему

// конец для файла task_add.html


// новые task_detail

// Показать результаты предыдущей попытки
async function showAttemptResults(attemptId) {
    console.log('Показ результатов для attemptId:', attemptId);

    if (!attemptId || isNaN(attemptId)) {
        console.error('Некорректный ID попытки:', attemptId);
        alert('Ошибка: ID попытки не определен');
        return;
    }

    const resultsDiv = document.getElementById('testResults');
    const resultsContent = document.getElementById('testResultsContent');
    const placeholder = document.getElementById('testResultsPlaceholder');

    if (!resultsDiv || !resultsContent) {
        console.error('Элементы для отображения результатов не найдены');
        return;
    }

    resultsDiv.style.display = 'block';
    if (placeholder) placeholder.style.display = 'none';

    resultsContent.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary"></div><p>Загрузка результатов...</p></div>';

    try {
        const url = `/tasks/attempt/${attemptId}/results/`;
        console.log('Запрос к URL:', url);

        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        console.log('Статус ответа:', response.status);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        console.log('Полученные данные:', data);

        if (data.success) {
            let html = `
                <div class="attempt-results">
                    <div class="attempt-header">
                        <h3>📝 Результаты попытки</h3>
                        <p class="text-muted">Время: ${data.attempt_time || 'не указано'}</p>
                        <p class="text-muted">ID задачи: ${data.task_display_id || data.real_task_id || data.task_id || 'не указан'}</p>
                        <div class="status-badge ${data.is_solved ? 'solved' : 'failed'}">
                            ${data.is_solved ? '✅ Задача решена' : '❌ Задача не решена'}
                        </div>
                        <div class="status-detail">
                            <strong>Статус:</strong> ${data.status || 'не указан'}
                        </div>
                    </div>

                    <div class="attempt-code">
                        <h4>📄 Код решения:</h4>
                        <pre><code class="language-python">${escapeHtml(data.code || '# Код не найден')}</code></pre>
                    </div>

                    <div class="attempt-tests">
                        <h4>🧪 Результаты тестов:</h4>
                        ${formatTestResults(data.result)}
                    </div>
                </div>
            `;

            resultsContent.innerHTML = html;

            // Подсветка кода
            if (typeof hljs !== 'undefined') {
                resultsContent.querySelectorAll('pre code').forEach(block => {
                    hljs.highlightElement(block);
                });
            }
        } else {
            resultsContent.innerHTML = `<div class="alert alert-danger">Ошибка: ${data.error || 'Неизвестная ошибка'}</div>`;
        }
    } catch (error) {
        console.error('Ошибка при загрузке результатов:', error);
        resultsContent.innerHTML = `<div class="alert alert-danger">Ошибка при загрузке результатов: ${error.message}</div>`;
    }
}

// Форматирование результатов тестов для формата из tester.py
function formatTestResults(result) {
    if (!result) return '<p class="text-muted">Нет данных о тестах</p>';

    // Если result - строка, пробуем распарсить как JSON
    if (typeof result === 'string') {
        try {
            result = JSON.parse(result);
        } catch (e) {
            return `<div class="alert alert-info">${escapeHtml(result)}</div>`;
        }
    }

    // Если result - массив тестов (формат из tester.py)
    if (Array.isArray(result) && result.length > 0) {
        const testsPassed = result.filter(t => t.passed === true).length;
        const totalTests = result.length;
        const percentage = totalTests > 0 ? Math.round((testsPassed / totalTests) * 100) : 0;

        let html = `
            <div class="test-summary-card">
                <div class="test-summary-header">
                    <h4>📊 Результаты тестирования</h4>
                </div>
                <div class="test-summary-stats">
                    <div class="stat-item">
                        <div class="stat-value">${totalTests}</div>
                        <div class="stat-label">Всего тестов</div>
                    </div>
                    <div class="stat-item success">
                        <div class="stat-value">${testsPassed}</div>
                        <div class="stat-label">Пройдено</div>
                    </div>
                    <div class="stat-item ${percentage >= 80 ? 'success' : (percentage >= 50 ? 'warning' : 'danger')}">
                        <div class="stat-value">${percentage}%</div>
                        <div class="stat-label">Успешность</div>
                    </div>
                </div>
                <div class="progress-bar-container">
                    <div class="progress-bar-fill" style="width: ${percentage}%; background: ${percentage >= 80 ? '#28a745' : (percentage >= 50 ? '#ffc107' : '#dc3545')};">
                        <span>${percentage}%</span>
                    </div>
                </div>
            </div>
        `;

        // Детали тестов
        html += '<div class="test-details-list"><h5>🔍 Детали тестов:</h5>';

        result.forEach((test, index) => {
            const testNum = index + 1;
            const passed = test.passed === true;
            const statusClass = passed ? 'passed' : 'failed';
            const statusIcon = passed ? '✅' : '❌';
            const statusText = passed ? 'Пройден' : 'Не пройден';

            // Получаем имя теста (из test_name или формируем)
            const testName = test.test_name || `Тест #${testNum}`;

            html += `
                <div class="test-detail-item ${statusClass}">
                    <div class="test-detail-header" onclick="toggleTestDetails(this)">
                        <div class="test-detail-title">
                            <span class="test-icon">${statusIcon}</span>
                            <strong>${escapeHtml(testName)}</strong>
                            <span class="test-status-badge ${statusClass}">${statusText}</span>
                        </div>
                        <span class="toggle-icon">▼</span>
                    </div>
                    <div class="test-detail-body" style="display: none;">
            `;

            if (!passed) {
                // Показываем ошибку
                if (test.error) {
                    html += `
                        <div class="test-error-message">
                            <div class="error-title">⚠️ Ошибка:</div>
                            <div class="error-content">${escapeHtml(test.error)}</div>
                        </div>
                    `;
                }

                // Входные данные
                if (test.input !== undefined && test.input !== null && test.input !== '') {
                    html += `
                        <div class="test-input">
                            <div class="diff-title">📥 Входные данные:</div>
                            <pre class="diff-content">${escapeHtml(String(test.input))}</pre>
                        </div>
                    `;
                }

                // Ожидаемый вывод
                if (test.expected !== undefined && test.expected !== null && test.expected !== '') {
                    html += `
                        <div class="expected-output">
                            <div class="diff-title">📋 Ожидаемый вывод:</div>
                            <pre class="diff-content">${escapeHtml(String(test.expected))}</pre>
                        </div>
                    `;
                }

                // Фактический вывод
                if (test.actual !== undefined && test.actual !== null) {
                    html += `
                        <div class="actual-output">
                            <div class="diff-title">📝 Полученный вывод:</div>
                            <pre class="diff-content">${escapeHtml(String(test.actual))}</pre>
                        </div>
                    `;
                }

                // Код возврата
                if (test.return_code !== undefined && test.return_code !== 0) {
                    html += `
                        <div class="return-code">
                            <div class="diff-title">🔢 Код возврата:</div>
                            <div class="code-content">${test.return_code}</div>
                        </div>
                    `;
                }
            } else {
                // Для пройденного теста показываем краткую информацию
                html += `
                    <div class="test-success-message">
                        <div class="success-icon">✅</div>
                        <div class="success-text">Тест пройден успешно!</div>
                    </div>
                `;

                // Если есть входные данные, показываем их (опционально)
                if (test.input !== undefined && test.input !== null && test.input !== '') {
                    html += `
                        <details class="test-input-details">
                            <summary>📥 Показать входные данные</summary>
                            <pre class="diff-content">${escapeHtml(String(test.input))}</pre>
                        </details>
                    `;
                }
            }

            html += `
                    </div>
                </div>
            `;
        });

        html += '</div>';

        // Итоговое сообщение
        if (testsPassed === totalTests) {
            html += '<div class="test-all-passed">🎉 Поздравляем! Все тесты пройдены успешно! 🎉</div>';
        } else if (testsPassed === 0) {
            html += '<div class="test-none-passed">💥 Ни один тест не пройден. Проверьте код и попробуйте снова.</div>';
        } else {
            html += `<div class="test-partial-passed">📈 Пройдено ${testsPassed} из ${totalTests} тестов (${percentage}%)</div>`;
        }

        return html;
    }

    // Если result - объект со статистикой
    if (result.tests_passed !== undefined || result.total_tests !== undefined) {
        return renderStatistics(result);
    }

    // Если есть message
    if (result.message) {
        return `<div class="alert alert-info">${escapeHtml(result.message)}</div>`;
    }

    // Если ничего не подошло
    return `
        <div class="test-debug">
            <h5>🔍 Отладочная информация</h5>
            <details>
                <summary>Показать структуру данных</summary>
                <pre class="debug-json">${escapeHtml(JSON.stringify(result, null, 2))}</pre>
            </details>
        </div>
    `;
}

// Функция для сворачивания/разворачивания деталей теста
function toggleTestDetails(element) {
    const body = element.nextElementSibling;
    const icon = element.querySelector('.toggle-icon');

    if (body && (body.style.display === 'none' || !body.style.display)) {
        body.style.display = 'block';
        if (icon) icon.textContent = '▲';
    } else if (body) {
        body.style.display = 'none';
        if (icon) icon.textContent = '▼';
    }
}

// Рендер статистики
function renderStatistics(data) {
    const testsPassed = data.tests_passed || 0;
    const totalTests = data.total_tests || 0;
    const percentage = totalTests > 0 ? Math.round((testsPassed / totalTests) * 100) : 0;

    let html = `
        <div class="test-summary-card">
            <div class="test-summary-header">
                <h4>📊 Результаты тестирования</h4>
            </div>
            <div class="test-summary-stats">
                <div class="stat-item">
                    <div class="stat-value">${totalTests}</div>
                    <div class="stat-label">Всего тестов</div>
                </div>
                <div class="stat-item success">
                    <div class="stat-value">${testsPassed}</div>
                    <div class="stat-label">Пройдено</div>
                </div>
                <div class="stat-item ${percentage >= 80 ? 'success' : (percentage >= 50 ? 'warning' : 'danger')}">
                    <div class="stat-value">${percentage}%</div>
                    <div class="stat-label">Успешность</div>
                </div>
            </div>
            <div class="progress-bar-container">
                <div class="progress-bar-fill" style="width: ${percentage}%;">
                    <span>${percentage}%</span>
                </div>
            </div>
        </div>
    `;

    if (data.message) {
        html += `<div class="test-message">${escapeHtml(data.message)}</div>`;
    }

    return html;
}

// Экранирование HTML
function escapeHtml(text) {
    if (text === undefined || text === null) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}
// Обработка загрузки файла
document.getElementById('programUploadForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const formData = new FormData(this);
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

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
            alert('Файл успешно загружен!');
            // Передаем program_id в окно тестирования
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
document.getElementById('programFile').addEventListener('change', function (e) {
    const file = e.target.files[0];
    if (file) {
        document.getElementById('programFileName').textContent = file.name;

        // Читаем содержимое файла для предпросмотра
        const reader = new FileReader();
        reader.onload = function (e) {
            document.getElementById('programContent').textContent = e.target.result;
        };
        reader.readAsText(file);
    }
});

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
const TASKS_ROOT = path.join(__dirname, 'tasks_for_tests');

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

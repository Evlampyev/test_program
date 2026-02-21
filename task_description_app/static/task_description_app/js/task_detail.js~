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


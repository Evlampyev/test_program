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
// Поиск учителя в выпадающем списке
document.getElementById('teacherSearch').addEventListener('keyup', function () {
    let searchText = this.value.toLowerCase();
    let select = document.querySelector('select[name="teacher"]');
    let options = select.options;

    for (let i = 1; i < options.length; i++) {
        let text = options[i].text.toLowerCase();
        if (text.includes(searchText)) {
            options[i].style.display = '';
        } else {
            options[i].style.display = 'none';
        }
    }
});

// Проверка существующего назначения
function checkExistingAssignment() {
    let classId = document.querySelector('select[name="school_class"]').value;
    let groupNumber = document.querySelector('select[name="group_number"]').value;
    let teacherId = document.querySelector('select[name="teacher"]').value;

    if (classId && groupNumber) {
        fetch(`/api/check-assignment/?class=${classId}&group=${groupNumber}`)
            .then(response => response.json())
            .then(data => {
                let infoDiv = document.getElementById('currentAssignmentInfo');
                let messageSpan = document.getElementById('assignmentMessage');

                if (data.exists) {
                    infoDiv.style.display = 'block';
                    infoDiv.className = 'alert alert-warning';
                    messageSpan.innerHTML = `<strong>Внимание!</strong> На эту группу уже назначен учитель ${data.teacher}. При сохранении назначение будет заменено.`;
                } else {
                    infoDiv.style.display = 'none';
                }
            });
    }
}

// Слушатели изменения полей
document.querySelector('select[name="school_class"]').addEventListener('change', checkExistingAssignment);
document.querySelector('select[name="group_number"]').addEventListener('change', checkExistingAssignment);

// Удаление назначения
function removeAssignment(assignmentId) {
    if (confirm('Вы уверены, что хотите удалить это назначение?')) {
        fetch('/api/remove-assignment/' + assignmentId + '/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': '{{ csrf_token }}',
                'Content-Type': 'application/json'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('assignment-' + assignmentId).remove();
                    alert('Назначение успешно удалено');
                } else {
                    alert('Ошибка при удалении');
                }
            });
    }
}

// Валидация формы перед отправкой
document.getElementById('assignForm').addEventListener('submit', function (e) {
    let teacher = document.querySelector('select[name="teacher"]').value;
    let schoolClass = document.querySelector('select[name="school_class"]').value;
    let group = document.querySelector('select[name="group_number"]').value;

    if (!teacher || !schoolClass || !group) {
        e.preventDefault();
        alert('Пожалуйста, заполните все поля');
    }
});

// Подсветка выбранного учителя
document.querySelector('select[name="teacher"]').addEventListener('change', function () {
    let selected = this.options[this.selectedIndex];
    if (selected.value) {
        // Можно добавить подсветку или дополнительную информацию
    }
});

// Анимация кнопки при отправке
document.getElementById('assignForm').addEventListener('submit', function () {
    let btn = document.getElementById('submitBtn');
    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Сохранение...';
    btn.disabled = true;
});
// assign_collection

// Выделить всех
document.getElementById('selectAll').addEventListener('change', function () {
    const checkboxes = document.querySelectorAll('.student-check');
    checkboxes.forEach(cb => cb.checked = this.checked);
});

// Снять выделение "Все", если снят один
document.querySelectorAll('.student-check').forEach(cb => {
    cb.addEventListener('change', function () {
        const allChecked = Array.from(document.querySelectorAll('.student-check')).every(cb => cb.checked);
        document.getElementById('selectAll').checked = allChecked;
    });
});
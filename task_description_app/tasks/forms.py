from django import forms
from .models import Task, DifficultyLevel


class TestCaseForm(forms.Form):
    """Форма для одного теста"""
    input_data = forms.CharField(
        label='Входные данные',
        widget=forms.Textarea(attrs={
            'class': 'form-control test-input',
            'rows': 3,
            'placeholder': 'Введите входные данные (каждая строка - отдельный тест?)'
        })
    )

    output_data = forms.CharField(
        label='Выходные данные',
        widget=forms.Textarea(attrs={
            'class': 'form-control test-output',
            'rows': 3,
            'placeholder': 'Введите ожидаемый результат'
        })
    )


class TaskAddForm(forms.ModelForm):
    """Форма для добавления новой задачи"""
    class_name = forms.CharField(
        label='Класс',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Например: 8 класс или 10 класс'
        })
    )
    topic = forms.CharField(
        label='Тема',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Например: Тема №1. Введение в программирование'
        })
    )
    lesson = forms.CharField(
        label='Урок',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Например: Урок 27 или Урок 84(38)'
        })
    )
    level = forms.ChoiceField(
        label='Уровень',
        choices=[
            ('Уровень_А', 'Уровень А'),
            ('Уровень_B', 'Уровень B'),
            ('Уровень_C', 'Уровень C'),
            ('Уровень_D', 'Уровень D'),
            ('Уровень_E', 'Уровень E'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Task
        fields = ['title', 'difficulty', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название задачи'
            }),
            'difficulty': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Краткое описание задачи (необязательно)'
            }),
        }


class TaskContentForm(forms.Form):
    """Форма для содержимого задачи"""
    task_md_content = forms.CharField(
        label='Описание задачи (task.md)',
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 15,
            'placeholder': '# Номер задачи\n\n## Условие\n\nОписание задачи...\n\n### Пример\n\nВход: 5 3\nВыход: 8'
        })
    )
    task_py_content = forms.CharField(
        label='Решение учителя (task.py)',
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'def solve():\n    # Ваш код\n    pass\n\nif __name__ == "__main__":\n    solve()'
        })
    )


# forms.py - добавьте эту форму
class TaskEditForm(forms.Form):
    """Форма для редактирования задачи"""
    title = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название задачи'})
    )
    difficulty = forms.ModelChoiceField(
        queryset=DifficultyLevel.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Краткое описание'})
    )

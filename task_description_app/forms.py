from django import forms
from .models import Task, DifficultyLevel
import os
import json
from django.conf import settings


class TaskAddForm(forms.ModelForm):
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

    # Поля для выбора/создания пути
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
            'placeholder': 'Например: Урок_27 или Урок_84(38)'
        })
    )

    level = forms.ChoiceField(
        label='Уровень',
        choices=[
            ('level_A', 'level_A'),
            ('level_B', 'level_B'),
            ('level_C', 'level_C'),
            ('level_D', 'level_D'),
            ('level_E', 'level_E'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    task_folder = forms.CharField(
        label='Папка задачи',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Например: task_001'
        })
    )


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

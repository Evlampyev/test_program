from django import forms
from django.conf import settings
from .models import Task, DifficultyLevel
import os
import json


# Создаем кастомное поле для множественной загрузки файлов
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


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
                'rows': 5,
                'placeholder': 'Введите описание задачи (необязательно)'
            }),
        }

    # Дополнительные поля для выбора пути
    class_level = forms.ChoiceField(
        label='Класс',
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    topic = forms.ChoiceField(
        label='Тема',
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    lesson = forms.ChoiceField(
        label='Урок',
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    level = forms.ChoiceField(
        label='Уровень',
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    task_folder = forms.CharField(
        label='Папка задачи',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Например: task_001',
            'readonly': True
        }),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Загружаем структуру из JSON файла

        json_path = os.path.join(settings.BASE_DIR, 'structure.json')
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                self.structure = json.load(f)
        except FileNotFoundError:
            self.structure = {}

        # Заполняем choices для классов
        class_choices = [('', '-- Выберите класс --')]
        for class_name in self.structure.keys():
            class_choices.append((class_name, class_name))
        self.fields['class_level'].choices = class_choices


class TaskFileUploadForm(forms.Form):
    """Форма для загрузки файлов задачи"""
    task_md = forms.FileField(
        label='Файл task.md',
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.md, .txt'
        })
    )

    task_py = forms.FileField(
        label='Файл task.py (решение учителя)',
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.py'
        })
    )

    # ИСПРАВЛЕНО: используем MultipleFileField вместо FileField
    test_files = MultipleFileField(
        label='Файлы тестов (test1.in, test1.out, test2.in, test2.out, ...)',
        required=True,
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': '.in,.out,.txt',
            'multiple': True
        })
    )
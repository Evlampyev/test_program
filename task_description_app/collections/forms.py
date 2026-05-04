# collections/forms.py
from django import forms

from users_app.models import SchoolClass
from . import Collection


class CollectionForm(forms.ModelForm):
    """Форма создания подборки задач"""

    target_class = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    target_group = forms.ChoiceField(
        choices=[('', '---------'), ('1', '1 группа'), ('2', '2 группа')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Collection
        fields = ['title', 'description', 'collection_type', 'target_class', 'target_group',
                  'is_public', 'show_results', 'time_limit']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название подборки'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Описание'}),
            'collection_type': forms.Select(attrs={'class': 'form-select'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_results': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'time_limit': forms.NumberInput(
                attrs={'class': 'form-control', 'placeholder': 'Минуты (оставьте пустым если без ограничений)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        classes = SchoolClass.objects.all().order_by('number', 'letter')

        class_choices = [('', '---------')]
        for cls in classes:
            if cls.letter:
                display_name = f"{cls.number}{cls.letter} класс"
            else:
                display_name = f"{cls.number} класс"
            class_choices.append((str(cls.number), display_name))

        self.fields['target_class'].choices = class_choices

    def clean(self):
        cleaned_data = super().clean()

        # Обрабатываем target_group
        target_group = cleaned_data.get('target_group')
        if target_group == '' or target_group is None:
            cleaned_data['target_group'] = None

        # Обрабатываем time_limit
        time_limit = cleaned_data.get('time_limit')
        if time_limit == '' or time_limit is None:
            cleaned_data['time_limit'] = None

        return cleaned_data


# Для контрольных работ и своих уроков
# class CollectionForm(forms.ModelForm):
#     """Форма создания подборки задач"""
#
#     # Переопределяем поля для выпадающих списков
#     target_class = forms.ChoiceField(
#         choices=[],
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-select'})
#     )
#
#     target_group = forms.ChoiceField(
#         choices=[('', '---------'), (1, '1 группа'), (2, '2 группа')],
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-select'})
#     )
#
#     class Meta:
#         model = Collection
#         fields = ['title', 'description', 'collection_type', 'target_class', 'target_group',
#                   'is_public', 'show_results', 'time_limit']
#         widgets = {
#             'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название подборки'}),
#             'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Описание'}),
#             'collection_type': forms.Select(attrs={'class': 'form-select'}),
#             'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#             'show_results': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#             'time_limit': forms.NumberInput(
#                 attrs={'class': 'form-control', 'placeholder': 'Минуты (оставьте пустым если без ограничений)'}),
#         }
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#
#         # Получаем уникальные классы из моделей SchoolClass или из профилей учеников
#         classes = SchoolClass.objects.all().order_by('number', 'letter')
#
#         # Формируем список choices для классов
#         class_choices = [('', '---------')]
#         for cls in classes:
#             # Если у класса есть буква, показываем "10А", иначе просто номер
#             if cls.letter:
#                 display_name = f"{cls.number}{cls.letter} класс"
#             else:
#                 display_name = f"{cls.number} класс"
#             class_choices.append((str(cls.number), display_name))
#
#         self.fields['target_class'].choices = class_choices
#
#         # Добавляем пустые значения для полей, которые могут быть None
#         if self.instance and self.instance.target_class:
#             self.initial['target_class'] = self.instance.target_class
#         if self.instance and self.instance.target_group:
#             self.initial['target_group'] = self.instance.target_group


class CollectionItemForm(forms.Form):
    """Форма для добавления задачи в подборку"""
    task_id = forms.IntegerField(widget=forms.HiddenInput())
    order = forms.IntegerField(initial=0, widget=forms.HiddenInput())
    max_score = forms.IntegerField(initial=10,
                                   widget=forms.NumberInput(attrs={'class': 'form-control', 'style': 'width: 80px;'}))

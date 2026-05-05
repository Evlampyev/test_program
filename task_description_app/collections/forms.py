# collections/forms.py
from django import forms

from users_app.models import SchoolClass
from . import Collection


class CollectionForm(forms.ModelForm):
    """Форма создания/редактирования подборки задач"""

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
            'target_class': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: 10 класс'}),
            'target_group': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '1 или 2'}),
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


class CollectionItemForm(forms.Form):
    """Форма для добавления задачи в подборку"""
    task_id = forms.IntegerField(widget=forms.HiddenInput())
    order = forms.IntegerField(initial=0, widget=forms.HiddenInput())
    max_score = forms.IntegerField(initial=10,
                                   widget=forms.NumberInput(attrs={'class': 'form-control', 'style': 'width: 80px;'}))


class CollectionEditForm(forms.ModelForm):
    """Форма для редактирования подборки (включая настройки времени)"""

    class Meta:
        model = Collection
        fields = ['title', 'description', 'collection_type', 'target_class', 'target_group',
                  'is_public', 'show_results', 'time_limit']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'collection_type': forms.Select(attrs={'class': 'form-select'}),
            'target_class': forms.TextInput(attrs={'class': 'form-control'}),
            'target_group': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_results': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'time_limit': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Минуты'}),
        }

    def clean_time_limit(self):
        time_limit = self.cleaned_data.get('time_limit')
        if time_limit == '' or time_limit is None:
            return None
        return time_limit

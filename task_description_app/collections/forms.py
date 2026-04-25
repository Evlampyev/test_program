from django import forms
from . import  Collection


# Для контрольных работ и своих уроков
class CollectionForm(forms.ModelForm):
    """Форма создания подборки задач"""

    class Meta:
        model = Collection
        fields = ['title', 'description', 'collection_type', 'target_class', 'target_group',
                  'is_public', 'show_results', 'time_limit']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'collection_type': forms.Select(attrs={'class': 'form-select'}),
            'target_class': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: 10 класс'}),
            'target_group': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_results': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'time_limit': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Минуты'}),
        }


class CollectionItemForm(forms.Form):
    """Форма для добавления задачи в подборку"""
    task_id = forms.IntegerField(widget=forms.HiddenInput())
    order = forms.IntegerField(initial=0, widget=forms.HiddenInput())
    max_score = forms.IntegerField(initial=10,
                                   widget=forms.NumberInput(attrs={'class': 'form-control', 'style': 'width: 80px;'}))


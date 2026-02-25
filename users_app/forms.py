from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import StudentProfile, Group, SchoolClass, TeacherProfile

User = get_user_model()


# Форма регистрации ученика
class StudentRegistrationForm(UserCreationForm):
    username = forms.CharField(
        label='Логин',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Придумайте логин'})
    )
    last_name = forms.CharField(
        label='Фамилия',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иванов'})
    )
    first_name = forms.CharField(
        label='Имя',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иван'})
    )
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Пароль'})
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Повторите пароль'})
    )

    # Поля для ученика
    class_number = forms.ChoiceField(
        label='Класс',
        choices=[(i, f'{i} класс') for i in range(1, 12)],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    class_letter = forms.ChoiceField(
        label='Буква класса',
        choices=[('А', 'А'), ('Б', 'Б'), ('В', 'В'), ('Г', 'Г')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    group_number = forms.ChoiceField(
        label='Группа',
        choices=[(1, 'Группа 1'), (2, 'Группа 2')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('username', 'last_name', 'first_name', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'student'
        user.set_password(self.cleaned_data['password1'])

        if commit:
            user.save()

            # Находим или создаем класс
            school_class, _ = SchoolClass.objects.get_or_create(
                number=self.cleaned_data['class_number'],
                letter=self.cleaned_data['class_letter']
            )

            # Находим группу
            group = Group.objects.filter(
                school_class=school_class,
                number=self.cleaned_data['group_number']
            ).first()

            # Создаем профиль ученика
            StudentProfile.objects.create(
                user=user,
                group=group
            )

        return user


# Форма регистрации учителя (для администратора)
class TeacherRegistrationForm(UserCreationForm):
    username = forms.CharField(label='Логин')
    last_name = forms.CharField(label='Фамилия')
    first_name = forms.CharField(label='Имя')
    middle_name = forms.CharField(label='Отчество', required=False)

    class Meta:
        model = User
        fields = ('username', 'last_name', 'first_name', 'middle_name', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'teacher'
        if commit:
            user.save()
            TeacherProfile.objects.create(user=user)
        return user


# Форма входа
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Логин',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите логин'
        })
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )
    user_type = forms.ChoiceField(
        choices=[('student', 'Ученик'), ('teacher', 'Учитель')],
        widget=forms.RadioSelect(attrs={'class': 'user-type-radio'}),
        initial='student'
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        user_type = cleaned_data.get('user_type')

        if username and password:
            from django.contrib.auth import authenticate
            user = authenticate(username=username, password=password)

            if user is None:
                raise forms.ValidationError("Неверный логин или пароль")

            if user.user_type != user_type:
                raise forms.ValidationError(
                    f"Этот пользователь зарегистрирован как {user.get_user_type_display()}. "
                    f"Выберите правильный тип пользователя."
                )

        return cleaned_data


# Форма назначения учителя на группу (для администратора)
class AssignTeacherForm(forms.Form):
    teacher = forms.ModelChoiceField(
        queryset=User.objects.filter(user_type='teacher'),
        label='Учитель'
    )
    school_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.all(),
        label='Класс'
    )
    group_number = forms.ChoiceField(
        choices=[(1, 'Группа 1'), (2, 'Группа 2')],
        label='Группа'
    )
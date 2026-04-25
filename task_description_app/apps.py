from django.apps import AppConfig


class TempTestsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'task_description_app'

class TaskDescriptionConfig(AppConfig):  # замените YourApp на имя вашего приложения
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'task_description_app'

    def ready(self):
        # import task_description_app.signals  # импортируем сигналы
        pass
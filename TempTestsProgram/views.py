from django.shortcuts import render


def about(request):
    from django.contrib.auth import get_user_model
    from task_description_app.models import Task
    from users_app.models import SchoolClass

    User = get_user_model()

    context = {
        'total_tasks': Task.objects.count(),
        'total_classes': SchoolClass.objects.count(),
        'total_teachers': User.objects.filter(user_type='teacher').count(),
        'total_students': User.objects.filter(user_type='student').count(),
    }
    return render(request, 'about.html', context)

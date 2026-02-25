from django.urls import path
from . import views

urlpatterns = [
    path('register/student/', views.student_register, name='student_register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('group/<int:group_id>/students/', views.group_students, name='group_students'),
    path('admin/assign-teacher/', views.assign_teacher, name='assign_teacher'),
]
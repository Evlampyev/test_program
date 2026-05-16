from django.urls import path
from . import views

urlpatterns = [
    path('register/student/', views.student_register, name='student_register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('group/<int:group_id>/students/', views.group_students, name='group_students'),
    path('student/<int:student_id>/delete/', views.delete_student, name='delete_student'),
    path('api/student-stats/<int:student_id>/', views.get_student_stats, name='student_stats'),
    path('api/reset-password/<int:student_id>/', views.reset_password, name='reset_password'),
    path('teacher/student/<int:student_id>/tasks/', views.student_tasks, name='student_tasks'),
    path('admin/assign-teacher/', views.assign_teacher, name='assign_teacher'),
    path('api/group-students-export/<int:group_id>/', views.group_students_export, name='group_students_export'),


]

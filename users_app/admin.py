from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StudentProfile, TeacherProfile, SchoolClass, Group


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'last_name', 'first_name', 'user_type', 'is_staff')
    list_filter = ('user_type', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительно', {'fields': ('user_type', 'middle_name')}),
    )


admin.site.register(User, CustomUserAdmin)
admin.site.register(TeacherProfile)
admin.site.register(SchoolClass)
admin.site.register(Group)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'group', 'solved_tasks', 'solved_tasks_preview']
    list_filter = ['group', 'group__school_class']
    search_fields = ['user__last_name', 'user__first_name']

    def solved_tasks_preview(self, obj):
        return obj.get_solved_tasks_display()

    solved_tasks_preview.short_description = "Решенные задачи"

# check_time.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TempTestsProgram.settings')
django.setup()

from django.conf import settings
from django.utils import timezone
from notifications.models import Notification


def check_time_settings():
    print("\n" + "=" * 60)
    print("ПРОВЕРКА НАСТРОЕК ВРЕМЕНИ")
    print("=" * 60)
    print(f"TIME_ZONE = {settings.TIME_ZONE}")
    print(f"USE_TZ = {settings.USE_TZ}")
    print()


def check_current_time():
    print("ТЕКУЩЕЕ ВРЕМЯ")
    print("-" * 40)
    now = timezone.now()
    print(f"timezone.now() = {now}")
    print(f"localtime = {timezone.localtime(now)}")
    print(f"datetime.now() = {timezone.datetime.now()}")
    print()


def check_notifications():
    print("УВЕДОМЛЕНИЯ")
    print("-" * 40)
    notifications = Notification.objects.all().order_by('-created_at')[:10]

    if not notifications:
        print("Нет уведомлений")
        return

    for n in notifications:
        print(f"\nID: {n.id}")
        print(f"  В БД: {n.created_at}")
        print(f"  Локальное: {timezone.localtime(n.created_at)}")
        print(f"  Формат: {n.created_at.strftime('%d.%m.%Y %H:%M')}")


if __name__ == '__main__':
    check_time_settings()
    check_current_time()
    check_notifications()
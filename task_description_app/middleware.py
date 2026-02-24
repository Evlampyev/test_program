# middleware.py
import pytz
from django.utils import timezone
from django.conf import settings

class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Активируем часовой пояс для всего запроса
        timezone.activate(pytz.timezone(settings.TIME_ZONE))
        response = self.get_response(request)
        return response
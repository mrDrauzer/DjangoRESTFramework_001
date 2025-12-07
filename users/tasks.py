from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
from celery import shared_task

from .models import User


@shared_task
def deactivate_inactive_users() -> int:
    """
    Блокирует пользователей, которые не заходили более месяца (по полю last_login).
    Возвращает количество деактивированных пользователей.
    """
    threshold = timezone.now() - timedelta(days=60)
    qs = User.objects.filter(is_active=True).filter(
        Q(last_login__lt=threshold) | Q(last_login__isnull=True)
    )
    updated = qs.update(is_active=False)
    return updated

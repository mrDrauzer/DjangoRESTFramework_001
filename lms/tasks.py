from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from celery import shared_task

from .models import Course, Subscription


@shared_task
def send_course_update_email(course_id: int, updated_kind: str = 'course') -> int:
    """
    Рассылает письма подписчикам курса об обновлении материалов.
    updated_kind: 'course' | 'lesson'
    Для случая 'lesson' действует «троттлинг»: не чаще одного письма в 4 часа.

    Возвращает число уведомлённых пользователей.
    """
    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        return 0

    now = timezone.now()

    if updated_kind == 'lesson':
        # Отправляем уведомление только если курс не обновлялся более 4 часов
        last_updated = course.updated_at
        if last_updated and (now - last_updated) < timedelta(hours=4):
            return 0

    # Получаем подписчиков
    subs = Subscription.objects.select_related('user').filter(course=course)
    emails = [s.user.email for s in subs if s.user and s.user.email]
    if not emails:
        # Обновим last_notified_at, чтобы не слать повторно слишком часто без получателей
        if updated_kind in ('course', 'lesson'):
            Course.objects.filter(pk=course.pk).update(last_notified_at=now)
        return 0

    subject = f"Обновления курса: {course.title}"
    if updated_kind == 'course':
        message = f"Курс '{course.title}' был обновлён. Зайдите, чтобы посмотреть изменения."
    else:
        message = f"В курсе '{course.title}' обновлены материалы уроков. Проверьте новые изменения."

    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'no-reply@example.com',
        recipient_list=emails,
        fail_silently=True,
    )

    # Обновляем момент последней рассылки
    Course.objects.filter(pk=course.pk).update(last_notified_at=now)
    return len(emails)

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal

from lms.models import Course, Lesson
from users.models import Payment


class Command(BaseCommand):
    help = 'Создаёт примерные платежи для демонстрации фильтров и эндпоинтов.'

    def handle(self, *args, **options):
        User = get_user_model()

        user = User.objects.order_by('id').first()
        if not user:
            self.stdout.write(
                self.style.ERROR(
                    'Нет пользователей. Создайте хотя бы одного пользователя.'
                )
            )
            return

        course = Course.objects.order_by('id').first()
        lesson = Lesson.objects.order_by('id').first()

        if not course and not lesson:
            self.stdout.write(
                self.style.ERROR(
                    'Нет данных курсов/уроков. Создайте хотя бы один курс или урок.'
                )
            )
            return

        created = 0

        if course:
            Payment.objects.create(user=user, course=course, amount=Decimal('1990.00'), method=Payment.Method.CASH)
            created += 1

        if lesson:
            Payment.objects.create(user=user, lesson=lesson, amount=Decimal('490.00'), method=Payment.Method.TRANSFER)
            created += 1

        self.stdout.write(self.style.SUCCESS(f'Создано платежей: {created}'))

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = "Создаёт базовые группы (например, 'moderators'). Запуск: python manage.py seed_groups"

    GROUPS = (
        'moderators',
    )

    def handle(self, *args, **options):
        created_any = False
        for name in self.GROUPS:
            group, created = Group.objects.get_or_create(name=name)
            if created:
                created_any = True
                self.stdout.write(self.style.SUCCESS(f"Группа '{name}' создана"))
            else:
                self.stdout.write(f"Группа '{name}' уже существует")
        if not created_any:
            self.stdout.write(self.style.WARNING('Новые группы не создавались'))

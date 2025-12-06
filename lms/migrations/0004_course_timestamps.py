from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lms', '0003_subscription'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='last_notified_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Последнее уведомление'),
        ),
        migrations.AddField(
            model_name='course',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Обновлено'),
        ),
    ]

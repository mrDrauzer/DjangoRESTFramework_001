from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('lms', '0001_initial'),
        ('users', '0002_alter_user_managers'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('paid_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата оплаты')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Сумма оплаты')),
                ('method', models.CharField(choices=[('cash', 'Наличные'), ('transfer', 'Перевод на счёт')], max_length=16, verbose_name='Способ оплаты')),
                ('course', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='lms.course', verbose_name='Оплаченный курс')),
                ('lesson', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='lms.lesson', verbose_name='Отдельно оплаченный урок')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'платёж',
                'verbose_name_plural': 'платежи',
                'ordering': ['-paid_at'],
            },
        ),
    ]

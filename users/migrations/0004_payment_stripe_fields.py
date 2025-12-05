from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_payment'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='stripe_product_id',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Stripe Product ID'),
        ),
        migrations.AddField(
            model_name='payment',
            name='stripe_price_id',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Stripe Price ID'),
        ),
        migrations.AddField(
            model_name='payment',
            name='stripe_session_id',
            field=models.CharField(blank=True, max_length=128, null=True, verbose_name='Stripe Session ID'),
        ),
        migrations.AddField(
            model_name='payment',
            name='stripe_checkout_url',
            field=models.URLField(blank=True, null=True, verbose_name='Ссылка на оплату (Checkout URL)'),
        ),
        migrations.AddField(
            model_name='payment',
            name='stripe_status',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Статус в Stripe'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='method',
            field=models.CharField(choices=[('cash', 'Наличные'), ('transfer', 'Перевод на счёт'), ('stripe', 'Stripe Checkout')], max_length=16, verbose_name='Способ оплаты'),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_payment_stripe_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='stripe_checkout_url',
            field=models.URLField(
                blank=True,
                null=True,
                max_length=2048,
                verbose_name='Ссылка на оплату (Checkout URL)'
            ),
        ),
    ]

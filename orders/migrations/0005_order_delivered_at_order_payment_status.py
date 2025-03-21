# Generated by Django 4.2 on 2025-03-19 18:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_payment_refund_status_alter_payment_payment_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='delivered_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='payment_status',
            field=models.BooleanField(default=False),
        ),
    ]

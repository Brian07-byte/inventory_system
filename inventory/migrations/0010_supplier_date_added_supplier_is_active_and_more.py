# Generated by Django 4.2 on 2025-03-27 15:38

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0009_alter_product_category_alter_product_supplier'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplier',
            name='date_added',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='supplier',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='supplier',
            name='supplier_code',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True),
        ),
    ]

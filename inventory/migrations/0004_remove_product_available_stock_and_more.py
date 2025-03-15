# Generated by Django 4.2 on 2025-03-08 08:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_product_available_stock_alter_stock_product'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='available_stock',
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventory.category'),
        ),
    ]

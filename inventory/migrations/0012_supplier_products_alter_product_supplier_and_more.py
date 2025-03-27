# Generated by Django 4.2 on 2025-03-27 16:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0011_alter_supplier_supplier_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplier',
            name='products',
            field=models.ManyToManyField(blank=True, related_name='suppliers', to='inventory.product'),
        ),
        migrations.AlterField(
            model_name='product',
            name='supplier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supplied_products', to='inventory.supplier'),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='supplier_code',
            field=models.CharField(blank=True, max_length=50, unique=True),
        ),
    ]

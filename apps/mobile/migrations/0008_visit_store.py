# Generated by Django 3.1.7 on 2025-06-15 18:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stores', '0001_initial'),
        ('mobile', '0007_auto_20241115_1257'),
    ]

    operations = [
        migrations.AddField(
            model_name='visit',
            name='store',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='stores.store', verbose_name='Магазин'),
        ),
    ]

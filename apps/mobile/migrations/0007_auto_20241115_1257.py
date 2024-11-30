# Generated by Django 3.1.7 on 2024-11-15 09:57

import apps.mobile.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0022_accountdocuments'),
        ('mobile', '0006_auto_20230129_2312'),
    ]

    operations = [
        migrations.AddField(
            model_name='visit',
            name='children',
            field=models.ManyToManyField(blank=True, related_name='visits', to='account.Child', verbose_name='Дети'),
        ),
        migrations.AlterField(
            model_name='visit',
            name='date',
            field=models.DateTimeField(blank=True, default=apps.mobile.models.now, null=True, verbose_name='Дата'),
        ),
    ]
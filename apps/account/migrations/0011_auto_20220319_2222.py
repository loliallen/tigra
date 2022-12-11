# Generated by Django 3.1.7 on 2022-03-19 19:22

import apps.account.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0010_auto_20220227_2339'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invintation',
            name='is_used_by_creator',
            field=models.BooleanField(blank=True, default=False, verbose_name='использован создателем'),
        ),
        migrations.AlterField(
            model_name='invintation',
            name='value',
            field=models.CharField(blank=True, default=apps.account.models.createCodeDigits6, max_length=6, unique=True, verbose_name='код'),
        ),
    ]
# Generated by Django 3.1.7 on 2022-06-01 08:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0014_auto_20220601_1032'),
    ]

    operations = [
        migrations.AddField(
            model_name='schedulernotify',
            name='body',
            field=models.TextField(default='-'),
        ),
        migrations.AddField(
            model_name='schedulernotify',
            name='title',
            field=models.TextField(default='-'),
        ),
    ]

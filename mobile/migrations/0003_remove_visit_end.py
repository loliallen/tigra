# Generated by Django 3.1.7 on 2022-02-27 20:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mobile', '0002_auto_20220223_2104'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='visit',
            name='end',
        ),
    ]

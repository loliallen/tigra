# Generated by Django 3.1.7 on 2022-02-23 18:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0006_auto_20220223_2126'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='children',
        ),
        migrations.RemoveField(
            model_name='user',
            name='visits',
        ),
    ]
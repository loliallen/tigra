# Generated by Django 3.1.7 on 2021-04-01 22:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0007_invintation_used'),
    ]

    operations = [
        migrations.AddField(
            model_name='invintation',
            name='visited',
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='device_token',
            field=models.TextField(default='', unique=True),
        ),
    ]

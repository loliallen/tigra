# Generated by Django 3.1.7 on 2021-03-30 06:12

from django.db import migrations, models
import mobile.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Visit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(blank=True, default=mobile.models.now, null=True)),
                ('duration', models.IntegerField(blank=True, null=True)),
                ('is_free', models.BooleanField(default=False)),
            ],
        ),
    ]

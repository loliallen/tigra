# Generated by Django 3.1.7 on 2021-04-11 12:43

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('account', '0001_initial'),
        ('mobile', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='visits',
            field=models.ManyToManyField(blank=True, default=[], related_name='visiter', to='mobile.Visit'),
        ),
    ]
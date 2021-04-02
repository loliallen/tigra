# Generated by Django 3.1.7 on 2021-04-01 13:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0003_remove_user_used_invintation'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='used_invintation',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='account.invintation'),
        ),
    ]

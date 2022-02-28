# Generated by Django 3.1.7 on 2022-02-27 20:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0009_remove_user_my_invintations'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invintation',
            name='used',
        ),
        migrations.RemoveField(
            model_name='invintation',
            name='visited',
        ),
        migrations.AddField(
            model_name='invintation',
            name='is_used_by_creator',
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AddField(
            model_name='invintation',
            name='used_by',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='invintation_used_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='invintation',
            name='creator',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='invintation_creator', to=settings.AUTH_USER_MODEL),
        ),
    ]

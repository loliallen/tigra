# Generated by Django 3.1.7 on 2022-06-01 07:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0013_auto_20220410_1737'),
    ]

    operations = [
        migrations.CreateModel(
            name='SchedulerNotify',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('trigger', models.TextField(choices=[('start', 'on_visit_start'), ('end', 'on_visit_end')])),
                ('minute_offset', models.IntegerField(default=0)),
            ],
        ),
        migrations.AddField(
            model_name='notification',
            name='scheduler',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='account.schedulernotify'),
        ),
    ]
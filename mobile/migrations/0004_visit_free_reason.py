# Generated by Django 3.1.7 on 2022-03-19 19:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mobile', '0003_remove_visit_end'),
    ]

    operations = [
        migrations.AddField(
            model_name='visit',
            name='free_reason',
            field=models.CharField(choices=[('CNT', 'Count'), ('INV', 'Invite')], max_length=255, null=True),
        ),
        migrations.RunSQL('''
            update mobile_visit
            set free_reason = 'INV'
            where is_free and is_active
        ''', reverse_sql=''),
        migrations.RunSQL('''
                update mobile_visit
                set free_reason = 'CNT'
                where is_free and not is_active
            ''', reverse_sql=''),
    ]

# Generated by Django 3.1.7 on 2022-12-11 20:54

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PromoBanner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('image', models.ImageField(upload_to='')),
                ('is_active', models.BooleanField(default=False)),
                ('link', models.URLField()),
                ('hyperlink', models.CharField(max_length=255)),
            ],
        ),
    ]

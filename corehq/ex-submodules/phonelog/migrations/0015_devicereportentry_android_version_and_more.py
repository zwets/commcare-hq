# Generated by Django 4.2.18 on 2025-03-25 10:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('phonelog', '0014_auto_20170718_2039'),
    ]

    operations = [
        migrations.AddField(
            model_name='devicereportentry',
            name='android_version',
            field=models.CharField(max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='devicereportentry',
            name='device_model',
            field=models.CharField(max_length=32, null=True),
        ),
    ]

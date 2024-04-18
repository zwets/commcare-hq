# Generated by Django 3.2.25 on 2024-04-18 13:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AppWorkflowConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domain', models.CharField(max_length=255)),
                ('app_id', models.CharField(max_length=255)),
                ('user_id', models.CharField(max_length=36)),
                ('name', models.CharField(max_length=255)),
                ('workflow', models.JSONField()),
                ('form_mode', models.CharField(choices=[('human', 'Human: Answer each question individually and submit form'), ('no_submit', "No Submit: Answer all questions but don't submit the form"), ('ignore', 'Ignore: Do not complete or submit forms')], max_length=255)),
                ('django_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('domain', 'user_id')},
            },
        ),
    ]

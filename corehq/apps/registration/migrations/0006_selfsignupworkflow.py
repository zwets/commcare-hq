# Generated by Django 4.2.11 on 2024-10-09 21:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0005_asyncsignuprequest'),
    ]

    operations = [
        migrations.CreateModel(
            name='SelfSignupWorkflow',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domain', models.CharField(max_length=255)),
                ('initiating_user', models.CharField(max_length=80)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('completed_on', models.DateTimeField(null=True)),
                ('subscribed_edition', models.CharField(choices=[('Community', 'Community'), ('Standard', 'Standard'), ('Pro', 'Pro'), ('Advanced', 'Advanced'),
                    ('Enterprise', 'Enterprise'), ('Paused', 'Paused'), ('Reseller', 'Reseller'), ('Managed Hosting', 'Managed Hosting')], max_length=25, null=True)),
            ],
            options={
                'indexes': [models.Index(fields=['domain', 'completed_on'], name='registratio_domain_362dd8_idx')],
            },
        ),
    ]

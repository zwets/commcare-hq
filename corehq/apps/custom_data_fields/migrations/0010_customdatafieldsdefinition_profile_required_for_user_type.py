# Generated by Django 4.2.15 on 2024-10-30 14:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_data_fields', '0009_field_required_for'),
    ]

    operations = [
        migrations.AddField(
            model_name='customdatafieldsdefinition',
            name='profile_required_for_user_type',
            field=models.JSONField(default=list),
        ),
    ]

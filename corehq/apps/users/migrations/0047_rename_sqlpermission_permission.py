# Generated by Django 3.2.13 on 2022-06-16 13:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0046_add_default_mobile_worker_role'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='SQLPermission',
            new_name='Permission',
        ),
    ]

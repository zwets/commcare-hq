# Generated by Django 3.2.23 on 2023-12-13 10:09

from django.db import migrations

from corehq.apps.users.models_role import Permission
from corehq.util.django_migrations import skip_on_fresh_install


@skip_on_fresh_install
def create_manage_domain_alerts_permission(*args, **kwargs):
    Permission.objects.get_or_create(value='manage_domain_alerts')


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0055_add_user_data'),
    ]

    operations = [
        migrations.RunPython(create_manage_domain_alerts_permission, migrations.RunPython.noop)
    ]

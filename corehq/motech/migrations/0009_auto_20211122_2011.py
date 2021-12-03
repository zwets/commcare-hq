# Generated by Django 2.2.24 on 2021-11-24 03:11

from django.db import migrations, models
from django.db.migrations import RunPython
from corehq.motech.utils import copy_api_auth_settings
from corehq.motech.const import OAUTH2_PWD
from corehq.util.django_migrations import skip_on_fresh_install


@skip_on_fresh_install
def migrate_api_settings(apps, schema_editor):
    ConnectionSettings = apps.get_model("motech", "ConnectionSettings")
    for connection in ConnectionSettings.objects.filter(
            api_auth_settings__in=['dhis2_auth_settings', 'moveit_automation_settings'],
            auth_type=OAUTH2_PWD,
    ):
        copy_api_auth_settings(connection)


class Migration(migrations.Migration):

    dependencies = [
        ('motech', '0008_requestlog_response_headers'),
    ]

    operations = [
        migrations.AddField(
            model_name='connectionsettings',
            name='pass_credentials_in_header',
            field=models.BooleanField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='connectionsettings',
            name='refresh_url',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='connectionsettings',
            name='token_url',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        RunPython(migrate_api_settings),
    ]
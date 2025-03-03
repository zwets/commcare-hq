# Generated by Django 4.2.18 on 2025-02-16 22:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("motech", "0017_connectionsettings_use_aes_cbc_encryption"),
        ("integration", "0008_kycconfig_provider_kycconfig_unique_domain_provider"),
    ]

    operations = [
        migrations.AlterField(
            model_name="kycconfig",
            name="connection_settings",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="motech.connectionsettings",
            ),
        ),
    ]

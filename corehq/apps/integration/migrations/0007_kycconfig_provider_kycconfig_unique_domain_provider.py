# Generated by Django 4.2.17 on 2025-01-29 08:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('integration', '0006_kycconfig'),
    ]

    operations = [
        migrations.AddField(
            model_name='kycconfig',
            name='provider',
            field=models.CharField(choices=[('mtn_kyc', 'MTN KYC')], default='mtn_kyc', max_length=25),
        ),
        migrations.AddConstraint(
            model_name='kycconfig',
            constraint=models.UniqueConstraint(fields=('domain', 'provider',), name='unique_domain_provider'),
        ),
    ]

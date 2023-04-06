# Generated by Django 3.2.18 on 2023-03-15 07:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0070_form_case_ids_case_importer_priv'),
    ]

    operations = [
        migrations.CreateModel(
            name='BillingAccountWebUserHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('record_date', models.DateField()),
                ('num_users', models.IntegerField(default=0)),
                ('billing_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounting.billingaccount')),
            ],
            options={
                'unique_together': {('billing_account', 'record_date')},
            },
        ),
    ]

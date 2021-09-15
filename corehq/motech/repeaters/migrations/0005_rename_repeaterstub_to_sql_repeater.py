# Generated by Django 2.2.24 on 2021-09-01 05:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('motech', '0008_requestlog_response_headers'),
        ('repeaters', '0004_attempt_strings'),
    ]

    operations = [
        migrations.CreateModel(
            name='SQLRepeater',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domain', models.CharField(max_length=126)),
                ('repeater_id', models.CharField(max_length=36)),
                ('is_paused', models.BooleanField(default=False)),
                ('next_attempt_at', models.DateTimeField(blank=True, null=True)),
                ('last_attempt_at', models.DateTimeField(blank=True, null=True)),
                ('connection_settings', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='motech.ConnectionSettings')),
            ],
            options={
                'db_table': 'repeaters_repeater',
            },
        ),
        migrations.RemoveField(
            model_name='sqlrepeatrecord',
            name='repeater_stub',
        ),
        migrations.DeleteModel(
            name='RepeaterStub',
        ),
        migrations.AddField(
            model_name='sqlrepeatrecord',
            name='repeater',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='repeat_records', to='repeaters.SQLRepeater'),
            preserve_default=False,
        ),
        migrations.AddIndex(
            model_name='sqlrepeater',
            index=models.Index(fields=['domain'], name='repeaters_r_domain_6fd257_idx'),
        ),
        migrations.AddIndex(
            model_name='sqlrepeater',
            index=models.Index(fields=['repeater_id'], name='repeaters_r_repeate_a7db73_idx'),
        ),
    ]
# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-25 09:14
from __future__ import absolute_import
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CCZHosting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('app_id', models.CharField(max_length=255)),
                ('version', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='CCZHostingLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.CharField(db_index=True, max_length=255, unique=True)),
                ('username', models.CharField(max_length=255)),
                ('password', models.CharField(max_length=255)),
                ('domain', models.CharField(max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name='cczhosting',
            name='link',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='icds.CCZHostingLink'),
        ),
    ]

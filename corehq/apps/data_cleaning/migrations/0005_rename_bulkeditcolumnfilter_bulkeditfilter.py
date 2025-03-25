# Generated by Django 4.2.18 on 2025-03-17 17:14

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('data_cleaning', '0004_alter_bulkeditcolumn_data_type_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='BulkEditFilter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filter_id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('index', models.IntegerField(default=0)),
                ('prop_id', models.CharField(max_length=255)),
                ('data_type', models.CharField(choices=[('text', 'text'), ('integer', 'integer'), ('phone_number', 'phone_number'), ('decimal', 'decimal'), ('date', 'date'), ('time', 'time'), ('datetime', 'datetime'), ('single_option', 'single_option'), ('multiple_option', 'multiple_option'), ('gps', 'gps'), ('barcode', 'barcode'), ('password', 'password')], default='text', max_length=15)),
                ('match_type', models.CharField(choices=[('exact', 'exact'), ('is_not', 'is_not'), ('starts', 'starts'), ('starts_not', 'starts_not'), ('is_empty', 'is_empty'), ('is_not_empty', 'is_not_empty'), ('missing', 'missing'), ('not_missing', 'not_missing'), ('fuzzy', 'fuzzy'), ('not_fuzzy', 'not_fuzzy'), ('phonetic', 'phonetic'), ('not_phonetic', 'not_phonetic'), ('lt', 'lt'), ('gt', 'gt'), ('lte', 'lte'), ('gte', 'gte'), ('is_any', 'is_any'), ('is_not_any', 'is_not_any'), ('is_all', 'is_all'), ('is_not_all', 'is_not_all')], default='exact', max_length=12)),
                ('value', models.TextField(blank=True, null=True)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='filters', to='data_cleaning.bulkeditsession')),
            ],
            options={
                'ordering': ['index'],
            },
        ),
        migrations.DeleteModel(
            name='BulkEditColumnFilter',
        ),
    ]

# Generated by Django 2.2.4 on 2019-12-11 13:42

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [('os2datascanner_report', '0003_jsonbfield'), ('os2datascanner_report', '0004_auto_20191210_1525')]

    dependencies = [
        ('os2datascanner_report', '0002_aliases'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='documentreport',
            options={'verbose_name_plural': 'Document report'},
        ),
        migrations.AddField(
            model_name='documentreport',
            name='data',
            field=django.contrib.postgres.fields.jsonb.JSONField(null=True),
        ),
        migrations.AlterField(
            model_name='documentreport',
            name='path',
            field=models.CharField(max_length=2000, verbose_name='Path'),
        ),
    ]

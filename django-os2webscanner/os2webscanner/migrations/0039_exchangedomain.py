# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-07-11 09:18
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('os2webscanner', '0038_auto_20180711_1023'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExchangeDomain',
            fields=[
                ('domain_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='os2webscanner.Domain')),
                ('userlist', models.FileField(upload_to='mailscan/users/')),
            ],
            options={
                'db_table': 'os2webscanner_exchangedomain',
            },
            bases=('os2webscanner.domain',),
        ),
    ]

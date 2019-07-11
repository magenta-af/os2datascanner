# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-06-24 16:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('os2datascanner', '0002_cqi_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='scanner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='locations', to='os2datascanner.Scanner', verbose_name='Scan'),
        ),
        migrations.AlterField(
            model_name='match',
            name='url',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='matches', to='os2datascanner.WebVersion', verbose_name='URL'),
        ),
    ]
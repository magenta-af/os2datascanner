# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-09-07 13:04
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('os2webscanner', '0043_auto_20180821_1439'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='regexrule',
            name='cpr_enabled',
        ),
        migrations.RemoveField(
            model_name='regexrule',
            name='do_modulus11',
        ),
        migrations.RemoveField(
            model_name='regexrule',
            name='ignore_irrelevant',
        ),
    ]

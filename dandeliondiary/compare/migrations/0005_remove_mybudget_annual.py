# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-10-08 03:06
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('compare', '0004_mybudgetgroup_group_list_order'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mybudget',
            name='annual',
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-25 02:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_auto_20160925_0016'),
    ]

    operations = [
        migrations.AddField(
            model_name='budgetgroup',
            name='group_list_order',
            field=models.IntegerField(default=0),
        ),
    ]

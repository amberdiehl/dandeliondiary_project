# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-10-12 03:27
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compare', '0007_auto_20161009_2045'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mybudget',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='mybudget',
            name='effective_date',
            field=models.DateField(default=datetime.datetime.now),
        ),
        migrations.AlterField(
            model_name='mybudgetcategory',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='mybudgetgroup',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]

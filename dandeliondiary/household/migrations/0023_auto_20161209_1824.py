# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-12-09 18:24
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('household', '0022_householdinvite'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rvhousehold',
            name='created_date',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now),
        ),
    ]

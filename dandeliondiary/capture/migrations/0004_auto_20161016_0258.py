# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-10-16 02:58
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('capture', '0003_auto_20161013_2050'),
    ]

    operations = [
        migrations.AlterField(
            model_name='myexpenseitem',
            name='google_place',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.GooglePlaceDetail'),
        ),
    ]

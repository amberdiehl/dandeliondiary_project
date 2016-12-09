# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-12-09 18:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('compare', '0009_mycategorytogoogletypes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mybudget',
            name='created_at',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='mybudget',
            name='effective_date',
            field=models.DateField(blank=True, default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='mybudgetcategory',
            name='created_at',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='mybudgetgroup',
            name='created_at',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-12-09 18:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('capture', '0005_myexpenseitem_expense_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='myexpenseitem',
            name='created_at',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='myexpenseitem',
            name='expense_date',
            field=models.DateField(blank=True, default=django.utils.timezone.now),
        ),
    ]

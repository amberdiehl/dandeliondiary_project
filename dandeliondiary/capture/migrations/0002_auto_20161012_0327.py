# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-10-12 03:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('capture', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expenseitem',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='googleplacedetail',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='googleplacetype',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-02-08 22:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('household', '0024_auto_20161209_1846'),
    ]

    operations = [
        migrations.AddField(
            model_name='household',
            name='subscription_status',
            field=models.CharField(default='Beta', max_length=7),
            preserve_default=False,
        ),
    ]

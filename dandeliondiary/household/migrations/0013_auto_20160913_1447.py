# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-13 14:47
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0002_fix_str'),
        ('household', '0012_auto_20160912_0020'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='householdmembers',
            name='household_member',
        ),
        migrations.AddField(
            model_name='householdmembers',
            name='member_account',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='account.Account'),
            preserve_default=False,
        ),
    ]

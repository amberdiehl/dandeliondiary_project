# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-12 00:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('household', '0011_auto_20160905_1530'),
    ]

    operations = [
        migrations.CreateModel(
            name='HouseholdMembers',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.RemoveField(
            model_name='householdmember',
            name='household',
        ),
        migrations.AddField(
            model_name='householdmembers',
            name='household_member',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='household.HouseholdMember'),
        ),
        migrations.AddField(
            model_name='householdmembers',
            name='household_membership',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='household.Household'),
        ),
    ]

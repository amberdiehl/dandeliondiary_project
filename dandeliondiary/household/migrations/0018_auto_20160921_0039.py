# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-21 00:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('household', '0017_auto_20160918_1639'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rvhousehold',
            name='children_status',
            field=models.IntegerField(blank=True, choices=[(0, 'No children'), (1, 'Visit'), (2, 'In household')], default=0),
        ),
        migrations.AlterField(
            model_name='rvhousehold',
            name='grandchildren_status',
            field=models.IntegerField(blank=True, choices=[(0, 'No grandchildren'), (1, 'Visit'), (2, 'In household')], default=0),
        ),
        migrations.AlterField(
            model_name='vehicle',
            name='finance',
            field=models.IntegerField(blank=True, choices=[(1, 'Cash'), (2, 'Gift'), (3, 'Loan - Bank'), (4, 'Loan - Dealer'), (5, 'Loan - Private')], default=0),
        ),
        migrations.AlterField(
            model_name='vehicle',
            name='fuel',
            field=models.IntegerField(blank=True, choices=[(1, 'Diesel'), (2, 'Electric'), (3, 'Gasoline'), (4, 'Hybrid')], default=0),
        ),
    ]

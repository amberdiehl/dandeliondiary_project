# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-12-11 19:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_auto_20161209_1846'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='googleplacetype',
            options={'ordering': ['type']},
        ),
        migrations.RemoveField(
            model_name='googleplacedetail',
            name='place_types',
        ),
        migrations.AddField(
            model_name='googleplacedetail',
            name='place_count',
            field=models.IntegerField(blank=True, default=0, verbose_name='Hit Count'),
        ),
        migrations.AddField(
            model_name='googleplacedetail',
            name='place_last_count',
            field=models.DateField(blank=True, default=django.utils.timezone.now, verbose_name='Last Hit Date'),
        ),
        migrations.AddField(
            model_name='googleplacedetail',
            name='place_lat',
            field=models.DecimalField(blank=True, decimal_places=7, default=0, max_digits=10, verbose_name='Latitude'),
        ),
        migrations.AddField(
            model_name='googleplacedetail',
            name='place_lng',
            field=models.DecimalField(blank=True, decimal_places=7, default=0, max_digits=10, verbose_name='Longitude'),
        ),
        migrations.AlterField(
            model_name='googleplacedetail',
            name='place_id',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
        migrations.AlterField(
            model_name='googleplacedetail',
            name='place_name',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-04 23:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('household', '0005_auto_20160904_1610'),
    ]

    operations = [
        migrations.AddField(
            model_name='rvhousehold',
            name='indicate_children',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='rvhousehold',
            name='indicate_pets',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='rvhousehold',
            name='children',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AlterField(
            model_name='rvhousehold',
            name='children_status',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
        migrations.AlterField(
            model_name='rvhousehold',
            name='grandchildren',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AlterField(
            model_name='rvhousehold',
            name='grandchildren_status',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
        migrations.AlterField(
            model_name='rvhousehold',
            name='pets_cat',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AlterField(
            model_name='rvhousehold',
            name='pets_dog',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AlterField(
            model_name='rvhousehold',
            name='pets_other',
            field=models.IntegerField(blank=True, default=0),
        ),
    ]
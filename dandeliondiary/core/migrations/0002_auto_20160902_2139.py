# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-02 21:39
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BugetModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('budget_model', models.CharField(max_length=32)),
                ('budget_model_description', models.TextField(default='description')),
            ],
        ),
        migrations.CreateModel(
            name='RigBrand',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('brand', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='RigModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('brand_model', models.CharField(max_length=128)),
                ('brand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.RigBrand')),
            ],
        ),
        migrations.CreateModel(
            name='RigPurchaseType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('purchase_type', models.CharField(max_length=32)),
                ('purchase_description', models.TextField(default='description')),
            ],
        ),
        migrations.CreateModel(
            name='RigStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rig_status', models.CharField(max_length=32)),
                ('rig_status_description', models.TextField(default='description')),
            ],
        ),
        migrations.CreateModel(
            name='RigType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rig_type', models.CharField(max_length=32)),
                ('rig_type_description', models.TextField(default='description')),
            ],
        ),
        migrations.CreateModel(
            name='Satisfaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('satisfaction_index', models.IntegerField(verbose_name=2)),
                ('satisfaction_description', models.CharField(max_length=12)),
                ('satisfaction_definition', models.TextField(default='definition')),
            ],
        ),
        migrations.CreateModel(
            name='UseType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('use_type', models.CharField(max_length=32)),
                ('use_type_description', models.TextField(default='description')),
            ],
        ),
        migrations.AddField(
            model_name='incometype',
            name='income_type_description',
            field=models.TextField(default='description'),
        ),
    ]
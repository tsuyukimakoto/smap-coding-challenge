# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-08-31 10:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_id', models.IntegerField(unique=True, verbose_name='User ID')),
            ],
            options={
                'ordering': ['data_id'],
            },
        ),
        migrations.CreateModel(
            name='Area',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=10, verbose_name='Area name')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Consumption',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('measured_datetime', models.DateTimeField()),
                ('year', models.IntegerField()),
                ('month', models.IntegerField()),
                ('day', models.IntegerField()),
                ('value', models.IntegerField()),
                ('float_value', models.FloatField()),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='consumption.Account')),
            ],
            options={
                'get_latest_by': 'measured_datetime',
            },
        ),
        migrations.CreateModel(
            name='Tariff',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=10, verbose_name='Tariff type')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='account',
            name='area',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='consumption.Area'),
        ),
        migrations.AddField(
            model_name='account',
            name='tariff',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='consumption.Tariff'),
        ),
        migrations.AddIndex(
            model_name='consumption',
            index=models.Index(fields=['measured_datetime'], name='idx_consumption__measured_dt'),
        ),
        migrations.AddIndex(
            model_name='consumption',
            index=models.Index(fields=['year', 'month', 'day'], name='idx_consumption__ymd'),
        ),
        migrations.AlterUniqueTogether(
            name='consumption',
            unique_together=set([('account', 'measured_datetime')]),
        ),
        migrations.AddIndex(
            model_name='account',
            index=models.Index(fields=['data_id'], name='idx_account__data_id'),
        ),
    ]
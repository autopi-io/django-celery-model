# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-01-25 10:08
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('djcelery_model', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='modeltaskmeta',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='modeltaskmeta',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='modeltaskmeta',
            name='state',
            field=models.PositiveIntegerField(choices=[(0, 'PENDING'), (1, 'STARTED'), (2, 'RETRY'), (3, 'FAILURE'), (4, 'SUCCESS')], default=0),
        ),
    ]

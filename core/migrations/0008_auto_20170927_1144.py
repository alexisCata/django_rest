# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-27 11:44
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_auto_20170918_1128'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='custom_fields',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='notification',
            name='type',
            field=models.CharField(choices=[('GENERIC', 'Generic'), ('EXAM', 'Exam'), ('TASK', 'Task')], default='GENERIC', max_length=10),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-10-10 08:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_notification_subject'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.CharField(choices=[('GENERIC', 'Generic'), ('EXAM', 'Exam'), ('TASK', 'Task'), ('ATTENDANCE', 'Attendance')], default='GENERIC', max_length=10),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-28 07:47
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_class_notification'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='target_class',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.Class'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='target_student',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notifications_received', to=settings.AUTH_USER_MODEL),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-10-03 11:56
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_auto_20171003_0955'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='study',
            new_name='subjects',
        ),
    ]

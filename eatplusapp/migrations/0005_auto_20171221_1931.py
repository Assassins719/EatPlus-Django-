# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-21 19:31
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eatplusapp', '0004_auto_20171205_1731'),
    ]

    operations = [
        migrations.RenameField(
            model_name='option',
            old_name='meal',
            new_name='item',
        ),
    ]

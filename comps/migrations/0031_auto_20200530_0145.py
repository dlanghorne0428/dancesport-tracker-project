# Generated by Django 3.0.4 on 2020-05-30 01:45

import cloudinary.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('comps', '0030_auto_20200530_0033'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comp',
            name='logo',
            field=cloudinary.models.CloudinaryField(max_length=255, verbose_name='logo'),
        ),
    ]

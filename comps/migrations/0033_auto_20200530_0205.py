# Generated by Django 3.0.4 on 2020-05-30 02:05

import cloudinary.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('comps', '0032_auto_20200530_0203'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comp',
            name='heatsheet_file',
            field=cloudinary.models.CloudinaryField(blank=True, max_length=255, verbose_name='heatsheet_file'),
        ),
    ]

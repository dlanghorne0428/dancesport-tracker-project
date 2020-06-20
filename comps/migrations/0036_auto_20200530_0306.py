# Generated by Django 3.0.4 on 2020-05-30 03:06

import cloudinary_storage.storage
import comps.models.comp
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comps', '0035_auto_20200530_0240'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comp',
            name='heatsheet_file',
            field=models.FileField(blank=True, storage=cloudinary_storage.storage.RawMediaCloudinaryStorage(), upload_to=comps.models.comp.comp_logo_path),
        ),
    ]

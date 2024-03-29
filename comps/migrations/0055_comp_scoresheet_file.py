# Generated by Django 4.0.4 on 2022-07-30 17:57

import cloudinary_storage.storage
import comps.models.comp
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comps', '0054_alter_comp_id_alter_comp_couple_id_alter_heat_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='comp',
            name='scoresheet_file',
            field=models.FileField(blank=True, storage=cloudinary_storage.storage.RawMediaCloudinaryStorage(), upload_to=comps.models.comp.comp_logo_path),
        ),
    ]

# Generated by Django 3.0.4 on 2020-03-29 22:57

import comps.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comps', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='comp',
            name='logo',
            field=models.ImageField(blank=True, upload_to=comps.models.comp_logo_path),
        ),
    ]

# Generated by Django 3.1.4 on 2021-06-18 16:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comps', '0046_auto_20210530_1836'),
    ]

    operations = [
        migrations.AddField(
            model_name='heat',
            name='dance_off',
            field=models.BooleanField(default=False),
        ),
    ]

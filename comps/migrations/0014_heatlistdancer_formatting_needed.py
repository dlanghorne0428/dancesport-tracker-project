# Generated by Django 3.0.4 on 2020-04-25 15:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comps', '0013_unmatchedheatentry_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='heatlistdancer',
            name='formatting_needed',
            field=models.BooleanField(default=False),
        ),
    ]

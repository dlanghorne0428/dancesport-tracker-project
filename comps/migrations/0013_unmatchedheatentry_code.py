# Generated by Django 3.0.4 on 2020-04-23 02:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comps', '0012_unmatchedheatentry'),
    ]

    operations = [
        migrations.AddField(
            model_name='unmatchedheatentry',
            name='code',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
    ]
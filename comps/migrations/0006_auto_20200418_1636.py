# Generated by Django 3.0.4 on 2020-04-18 16:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comps', '0005_compmngrdancer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='heatresult',
            name='points',
            field=models.FloatField(null=True),
        ),
    ]
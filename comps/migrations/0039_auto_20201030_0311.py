# Generated by Django 3.0.4 on 2020-10-30 03:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comps', '0038_auto_20200531_1505'),
    ]

    operations = [
        migrations.AlterField(
            model_name='heat',
            name='category',
            field=models.CharField(choices=[('PH', 'Pro heat'), ('NH', 'Heat'), ('SO', 'Solo')], default='NH', max_length=2),
        ),
    ]

# Generated by Django 3.0.4 on 2020-04-14 01:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rankings', '0005_auto_20200414_0110'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dancer',
            name='dancer_type',
            field=models.CharField(choices=[('PRO', 'Professional'), ('AM', 'Amateur'), ('JR', 'Junior')], default='PRO', max_length=3),
        ),
    ]

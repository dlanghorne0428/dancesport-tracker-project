# Generated by Django 3.1.4 on 2021-11-26 21:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rankings', '0010_dancer_name_fix_date'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='couple',
            options={'ordering': ['dancer_1']},
        ),
    ]

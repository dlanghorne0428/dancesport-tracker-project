# Generated by Django 4.0.7 on 2022-12-10 22:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('comps', '0060_alter_comp_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='heatlist_dancer',
            options={'ordering': ['comp']},
        ),
    ]

# Generated by Django 3.0.4 on 2020-04-29 03:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comps', '0018_auto_20200429_0344'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comp',
            name='process_state',
            field=models.CharField(choices=[('IN', 'Comp Initialized'), ('DL', 'Dancers Loaded'), ('DNF', 'Dancer Names Formatted'), ('HL', 'Heats Loaded'), ('HSD', 'Heat Levels Defined'), ('CEM', 'Heat Entries Matched'), ('SSL', 'Scoresheets Loaded'), ('RR', 'Results Resolved '), ('FIN', 'Processing Complete')], default='IN', max_length=3),
        ),
    ]

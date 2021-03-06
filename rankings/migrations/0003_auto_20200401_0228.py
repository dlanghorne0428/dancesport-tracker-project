# Generated by Django 3.0.4 on 2020-04-01 02:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rankings', '0002_couple'),
    ]

    operations = [
        migrations.AddField(
            model_name='couple',
            name='dancer_1',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='leader_instructor', to='rankings.Dancer'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='couple',
            name='dancer_2',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, related_name='follower_student', to='rankings.Dancer'),
            preserve_default=False,
        ),
    ]

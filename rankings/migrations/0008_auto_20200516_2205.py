# Generated by Django 3.0.4 on 2020-05-16 22:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rankings', '0007_auto_20200510_1543'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='couple',
            name='event_count',
        ),
        migrations.RemoveField(
            model_name='couple',
            name='rating',
        ),
        migrations.RemoveField(
            model_name='couple',
            name='total_points',
        ),
        migrations.AlterField(
            model_name='couple',
            name='couple_type',
            field=models.CharField(choices=[('PRC', 'Professionals'), ('PAC', 'Pro-Am'), ('JPC', 'Junior_Pro-Am'), ('AMC', 'Amateurs'), ('JAC', 'Junior_Amateurs')], default='PAC', max_length=3),
        ),
    ]

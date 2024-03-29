# Generated by Django 3.1.4 on 2021-11-26 21:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rankings', '0011_auto_20211126_2117'),
        ('comps', '0051_auto_20211108_0216'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comp_Couple',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shirt_number', models.CharField(blank=True, max_length=10)),
                ('comp', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='comps.comp')),
                ('couple', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='rankings.couple')),
            ],
        ),
    ]

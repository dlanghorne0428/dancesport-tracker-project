# Generated by Django 3.1.4 on 2021-07-22 23:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comps', '0048_auto_20210702_0229'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comp',
            name='url_data_format',
            field=models.CharField(choices=[('CM', 'Comp Manager'), ('CO', 'Comp Organizer'), ('ND', 'NDCA Premier'), ('NF', 'NDCA Premier - Feed'), ('O2', 'O2cm.com')], default='CM', max_length=2),
        ),
    ]

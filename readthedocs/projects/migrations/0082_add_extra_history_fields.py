# Generated by Django 2.2.24 on 2021-09-29 19:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0081_add_another_header'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalproject',
            name='extra_history_browser',
            field=models.CharField(blank=True, max_length=250, null=True, verbose_name='Browser user-agent'),
        ),
        migrations.AddField(
            model_name='historicalproject',
            name='extra_history_ip',
            field=models.CharField(blank=True, max_length=250, null=True, verbose_name='IP address'),
        ),
    ]

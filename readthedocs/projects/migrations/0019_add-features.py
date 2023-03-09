# Generated by Django 1.9.12 on 2017-10-27 12:55
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0018_fix-translation-model'),
    ]

    operations = [
        migrations.CreateModel(
            name='Feature',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('feature_id', models.CharField(max_length=32, unique=True, verbose_name='Feature identifier')),
                ('add_date', models.DateTimeField(auto_now_add=True, verbose_name='Date feature was added')),
                ('default_true', models.BooleanField(default=False, verbose_name='Historical default is True')),
            ],
        ),
        migrations.AddField(
            model_name='feature',
            name='projects',
            field=models.ManyToManyField(blank=True, to='projects.Project'),
        ),
    ]

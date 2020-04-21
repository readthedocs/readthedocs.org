# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0005_sync_project_model'),
    ]

    operations = [
        migrations.CreateModel(
            name='Domain',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(unique=True, verbose_name='URL')),
                ('machine', models.BooleanField(default=False, help_text='This URL was auto-created')),
                ('cname', models.BooleanField(default=False, help_text='This URL is a CNAME for the project')),
                ('canonical', models.BooleanField(default=False, help_text='This URL is the primary one where the documentation is served from.')),
                ('count', models.IntegerField(default=0, help_text='Number of times this domain has been hit.')),
                ('project', models.ForeignKey(related_name='domains', to='projects.Project', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('-canonical', '-machine', 'url'),
            },
        ),
    ]

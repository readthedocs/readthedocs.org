# Generated by Django 4.2.17 on 2025-02-18 21:38

from django.db import migrations, models
import readthedocs.projects.validators
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.before_deploy

    dependencies = [
        ('projects', '0147_addons_filetreediff_enabled_by_default'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicaladdonsconfig',
            name='extra_history_user_id',
            field=models.IntegerField(blank=True, null=True, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='historicaladdonsconfig',
            name='extra_history_user_username',
            field=models.CharField(max_length=150, null=True, verbose_name='username'),
        ),
        migrations.AlterField(
            model_name='historicalproject',
            name='extra_history_user_id',
            field=models.IntegerField(blank=True, null=True, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='historicalproject',
            name='extra_history_user_username',
            field=models.CharField(max_length=150, null=True, verbose_name='username'),
        ),
        migrations.AlterField(
            model_name='historicalproject',
            name='repo',
            field=models.CharField(help_text='Git repository URL', max_length=255, validators=[readthedocs.projects.validators.RepositoryURLValidator()], verbose_name='Repository URL'),
        ),
        migrations.AlterField(
            model_name='historicalproject',
            name='slug',
            field=models.SlugField(db_index=False, max_length=63, verbose_name='Slug'),
        ),
        migrations.AlterField(
            model_name='project',
            name='repo',
            field=models.CharField(help_text='Git repository URL', max_length=255, validators=[readthedocs.projects.validators.RepositoryURLValidator()], verbose_name='Repository URL'),
        ),
    ]

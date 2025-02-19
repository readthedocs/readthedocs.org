# Generated by Django 4.2.18 on 2025-02-03 21:58
from django_safemigrate import Safe

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields


class Migration(migrations.Migration):

    safe = Safe.before_deploy

    dependencies = [
        ('oauth', '0016_deprecate_old_vcs'),
    ]

    operations = [
        migrations.CreateModel(
            name='GitHubAppInstallation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('installation_id', models.PositiveBigIntegerField(db_index=True, help_text='The application installation ID', unique=True)),
                ('target_id', models.PositiveBigIntegerField(help_text='A GitHub account ID, it can be from a user or an organization')),
                ('target_type', models.CharField(choices=[('User', 'User'), ('Organization', 'Organization')], help_text='Account type that the target_id belongs to (user or organization)', max_length=255)),
                ('extra_data', models.JSONField(default=dict, help_text='Extra data returned by the webhook when the installation is created')),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='remoterepository',
            name='github_app_installation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='repositories', to='oauth.githubappinstallation', verbose_name='GitHub App Installation'),
        ),
    ]

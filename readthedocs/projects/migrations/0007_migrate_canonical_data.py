# -*- coding: utf-8 -*-
from django.db import migrations, transaction


def migrate_canonical(apps, schema_editor):
    Project = apps.get_model('projects', 'Project')
    for project in Project.objects.all():
        if project.canonical_url:
            try:
                with transaction.atomic():
                    project.domains.create(
                        url=project.canonical_url,
                        canonical=True,
                    )
                    print('Added {url} to {project}'.format(url=project.canonical_url, project=project.name))
            except Exception as e:
                print(e)
                print('Failed adding {url} to {project}'.format(
                    url=project.canonical_url, project=project.name,
                ))


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0006_add_domain_models'),
    ]

    operations = [
        migrations.RunPython(migrate_canonical),
    ]

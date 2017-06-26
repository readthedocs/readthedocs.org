# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from __future__ import absolute_import
from django.db import migrations
from django.db import transaction


def migrate_canonical(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    for project in Project.objects.all():
        if project.canonical_url:
            try:
                with transaction.atomic():
                    project.domains.create(
                        url=project.canonical_url,
                        canonical=True,
                    )
                    print(u"Added {url} to {project}".format(url=project.canonical_url, project=project.name))
            except Exception as e:
                print(e)
                print(u"Failed adding {url} to {project}".format(
                    url=project.canonical_url, project=project.name
                ))


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0006_add_domain_models'),
    ]

    operations = [
        migrations.RunPython(migrate_canonical)
    ]

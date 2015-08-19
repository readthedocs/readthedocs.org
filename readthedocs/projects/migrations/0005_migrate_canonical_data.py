# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def migrate_canonical(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    for project in Project.objects.all():
        if project.canonical_url:
            domain = project.domains.create(
                url=project.canonical_url,
                canonical=True,
            )
            print "Added {url} to {project}".format(url=domain.url, project=project.name)


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0004_add_cname_modeling'),
    ]

    operations = [
        migrations.RunPython(migrate_canonical)
    ]

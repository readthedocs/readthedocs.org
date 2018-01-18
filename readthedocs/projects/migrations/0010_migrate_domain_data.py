# -*- coding: utf-8 -*-
from __future__ import (absolute_import, print_function, unicode_literals)

from django.db import models, migrations
from future.backports.urllib.parse import urlparse

import readthedocs.core.validators


def migrate_url(apps, schema_editor):
    Domain = apps.get_model("projects", "Domain")
    Domain.objects.filter(count=0).delete()
    for domain in Domain.objects.all():
        if domain.project.superprojects.count() or domain.project.main_language_project:
            print("{project} is a subproject or translation. Deleting domain.".format(
                project=domain.project.slug))
            domain.delete()
            continue
        parsed = urlparse(domain.url)
        if parsed.scheme or parsed.netloc:
            domain_string = parsed.netloc
        else:
            domain_string = parsed.path
        try:
            domain.domain = domain_string
            domain.save()
            print(u"Added {domain} from {url}".format(url=domain.url, domain=domain_string))
        except Exception as e:
            print(e)
            print(u"Failed {domain} from {url}".format(url=domain.url, domain=domain_string))

        dms = Domain.objects.filter(domain=domain_string).order_by('-count')
        if dms.count() > 1:
            for dm in list(dms)[1:]:
                dm.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0009_add_domain_field'),
    ]

    operations = [
        migrations.RunPython(migrate_url),
        migrations.AlterField(
            model_name='domain',
            name='domain',
            field=models.CharField(unique=True, max_length=255, verbose_name='Domain', validators=[readthedocs.core.validators.DomainNameValidator()]),

        ),
    ]

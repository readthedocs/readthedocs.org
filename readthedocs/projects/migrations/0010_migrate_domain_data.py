# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.db import transaction
import django.contrib.sites.models

from urlparse import urlparse


def migrate_url(apps, schema_editor):
    Domain = apps.get_model("projects", "Domain")
    for domain in Domain.objects.all():
        if domain.project.subprojects.fist() or domain.project.main_language_project:
            print "{project} is a subproject or translation. Not setting domain".format(
                project=domain.project)
            continue
        parsed = urlparse(domain.url)
        if parsed.scheme or parsed.netloc:
            domain_string = parsed.netloc
        else:
            domain_string = parsed.path
        try:
            with transaction.atomic():
                domain.domain = domain_string
                domain.save()
                print u"Added {domain} from {url}".format(url=domain.url, domain=domain_string)
        except Exception, e:
            print e
            print u"Failed {domain} from {url}".format(url=domain.url, domain=domain_string)


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0009_add_domain_field'),
    ]

    operations = [
        migrations.RunPython(migrate_url),
        migrations.AlterField(
            model_name='domain',
            name='domain',
            field=models.CharField(unique=True, max_length=255, verbose_name='Domain', validators=[django.contrib.sites.models._simple_domain_name_validator]),
        ),
    ]

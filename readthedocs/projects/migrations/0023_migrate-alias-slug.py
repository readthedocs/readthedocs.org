# Generated by Django 1.9.12 on 2017-12-21 16:31
import re

from django.db import migrations
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()

    def migrate_data(apps, schema_editor):
        # Keep things that slugify wouldn't normally accept,
        # so that we don't break a bunch of folks URL's.
        # They will have to change them on update.
        invalid_chars_re = re.compile("[^-._a-zA-Z0-9]")
        ProjectRelationship = apps.get_model("projects", "ProjectRelationship")
        for p in ProjectRelationship.objects.all():
            if p.alias and invalid_chars_re.match(p.alias):
                new_alias = invalid_chars_re.sub("", p.alias)
                p.alias = new_alias
                p.save()

    def reverse(apps, schema_editor):
        pass

    dependencies = [
        ("projects", "0022_add-alias-slug"),
    ]

    operations = [
        migrations.RunPython(migrate_data, reverse),
    ]

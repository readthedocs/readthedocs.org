"""Rebuild documentation for all projects"""

from __future__ import absolute_import
from django.core.management.base import BaseCommand

from readthedocs.builds.models import Version
from readthedocs.projects.tasks import update_docs


class Command(BaseCommand):

    help = __doc__

    def handle(self, *args, **options):
        for version in Version.objects.filter(active=True, built=False):
            update_docs.run(version.project_id, record=False,
                            version_pk=version.pk)

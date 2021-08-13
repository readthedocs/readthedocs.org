"""Imports tags for projects without tags from GitHub."""
import time

from django.core.management.base import BaseCommand

from readthedocs.projects.models import Project
from readthedocs.projects.tag_utils import import_tags


class Command(BaseCommand):

    help = __doc__

    def handle(self, *args, **options):
        queryset = Project.objects.filter(tags=None).filter(repo__contains='github.com')
        project_total = queryset.count()

        for i, project in enumerate(queryset.iterator()):
            self.stdout.write(
                '[{}/{}] Fetching tags for {}'.format(i + 1, project_total, project.slug)
            )

            tags = import_tags(project)
            if tags:
                self.stdout.write('Set tags for {}: {}'.format(project.slug, tags))

            # Sleeping half a second should keep us under 5k requests/hour
            time.sleep(0.5)

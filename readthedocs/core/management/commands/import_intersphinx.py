from django.core.management.base import BaseCommand

from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Version
from readthedocs.projects.tasks import update_intersphinx


class Command(BaseCommand):
    def handle(self, *args, **options):
        for version in Version.objects.filter(slug=LATEST):
            update_intersphinx(version.pk)

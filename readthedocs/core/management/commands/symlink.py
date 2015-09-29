import logging

from django.core.management.base import BaseCommand

from readthedocs.projects import utils
from readthedocs.projects.models import Project

log = logging.getLogger(__name__)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('projects', nargs='+', type=str)

    def handle(self, *args, **options):
        for slug in options['projects']:
            utils.symlink(project=Project.objects.get(slug=slug))

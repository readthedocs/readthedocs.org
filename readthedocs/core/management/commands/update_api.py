import logging
from optparse import make_option

from django.core.management.base import BaseCommand
from readthedocs.projects import tasks
from readthedocs.api.client import api


log = logging.getLogger(__name__)


class Command(BaseCommand):
    """Custom management command to rebuild documentation for all projects on
    the site. Invoked via ``./manage.py update_repos``.
    """

    def add_arguments(self, parser):
        parser.add_argument('--docker', action='store_true', default=False)

    def handle(self, *args, **options):
        docker = options.get('docker', False)
        if len(args):
            for slug in args:
                project_data = api.project(slug).get()
                p = tasks.make_api_project(project_data)
                log.info("Building %s" % p)
                tasks.update_docs.run(pk=p.pk, docker=docker)

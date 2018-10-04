"""
Build documentation using the API and not hitting a database.

Usage::

    ./manage.py update_api <slug>
"""

from __future__ import absolute_import
import logging

from django.core.management.base import BaseCommand

from readthedocs.api.client import api
from readthedocs.projects import tasks
from readthedocs.projects.models import APIProject


log = logging.getLogger(__name__)


class Command(BaseCommand):

    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument('--docker', action='store_true', default=False)
        parser.add_argument('projects', nargs='+', type=str)

    def handle(self, *args, **options):
        docker = options.get('docker', False)
        for slug in options['projects']:
            project_data = api.project(slug).get()
            p = APIProject(**project_data)
            log.info("Building %s", p)
            # pylint: disable=no-value-for-parameter
            tasks.update_docs_task(p.pk, docker=docker)

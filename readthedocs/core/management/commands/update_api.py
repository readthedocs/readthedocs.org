"""
Build documentation using the API and not hitting a database.

Usage::

    ./manage.py update_api <slug>
"""

from __future__ import absolute_import
import logging

from django.core.management.base import BaseCommand
from readthedocs.projects import tasks
from readthedocs.api.client import api


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
            p = tasks.make_api_project(project_data)
            log.info("Building %s", p)
            tasks.update_docs.run(pk=p.pk, docker=docker)

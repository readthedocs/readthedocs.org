"""Update symlinks for projects"""

from __future__ import absolute_import
import logging

from django.core.management.base import BaseCommand

from readthedocs.projects import tasks

from readthedocs.projects.models import Project

log = logging.getLogger(__name__)


class Command(BaseCommand):

    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument('projects', nargs='+', type=str)

    def handle(self, *args, **options):
        projects = options['projects']
        if 'all' in projects:
            queryset = Project.objects.all()
        else:
            queryset = Project.objects.filter(slug__in=projects)
        for proj in queryset:
            tasks.symlink_project(project_pk=proj.pk)

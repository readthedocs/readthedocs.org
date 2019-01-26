# -*- coding: utf-8 -*-

"""Update symlinks for projects."""

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
            pks = Project.objects.values_list('pk', flat=True)
        else:
            pks = Project.objects.filter(
                slug__in=projects,
            ).values_list('pk', flat=True)
        for proj in pks:
            try:
                tasks.symlink_project(project_pk=proj)
            except Exception:
                log.exception('Failed symlink management command')

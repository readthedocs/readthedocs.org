# -*- coding: utf-8 -*-

"""
Custom management command to rebuild documentation for all projects.

Invoked via ``./manage.py update_repos``.
"""

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import logging

from django.core.management.base import BaseCommand

from readthedocs.builds.models import Build, Version
from readthedocs.core.utils import trigger_build
from readthedocs.projects import tasks
from readthedocs.projects.models import Project

log = logging.getLogger(__name__)


class Command(BaseCommand):

    """Management command for rebuilding documentation on projects."""

    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument('slugs', nargs='+', type=str)

        parser.add_argument(
            '-f',
            action='store_true',
            dest='force',
            default=False,
            help='Force a build in sphinx',
        )

        parser.add_argument(
            '-V',
            dest='version',
            default='all',
            help='Build a version, or all versions',
        )

    def handle(self, *args, **options):
        force = options['force']
        version = options['version']

        if options.get('slugs', []):
            for slug in options['slugs']:
                if version and version != 'all':
                    log.info('Updating version %s for %s', version, slug)
                    for version in Version.objects.filter(
                            project__slug=slug,
                            slug=version,
                    ):
                        trigger_build(project=version.project, version=version)
                elif version == 'all':
                    log.info('Updating all versions for %s', slug)
                    for version in Version.objects.filter(
                            project__slug=slug,
                            active=True,
                            uploaded=False,
                    ):

                        build = Build.objects.create(
                            project=version.project,
                            version=version,
                            type='html',
                            state='triggered',
                        )

                        # pylint: disable=no-value-for-parameter
                        tasks.update_docs_task(
                            version.project_id,
                            build_pk=build.pk,
                            version_pk=version.pk,
                        )
                else:
                    p = Project.all_objects.get(slug=slug)
                    log.info('Building %s', p)
                    trigger_build(project=p, force=force)
        else:
            if version == 'all':
                log.info('Updating all versions')
                for version in Version.objects.filter(
                        active=True,
                        uploaded=False,
                ):
                    # pylint: disable=no-value-for-parameter
                    tasks.update_docs_task(
                        version.project_id,
                        force=force,
                        version_pk=version.pk,
                    )
            else:
                log.info('Updating all docs')
                for project in Project.objects.all():
                    # pylint: disable=no-value-for-parameter
                    tasks.update_docs_task(
                        project.pk,
                        force=force,
                    )

"""
Custom management command to rebuild documentation for all projects.

Invoked via ``./manage.py update_repos``.
"""

import logging

from django.core.management.base import BaseCommand

from readthedocs.builds.constants import EXTERNAL, INTERNAL
from readthedocs.builds.models import Version
from readthedocs.core.utils import trigger_build
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
                        trigger_build(project=version.project, version=version)
                elif version == INTERNAL:
                    log.info('Updating all internal versions for %s', slug)
                    for version in Version.internal.filter(
                            project__slug=slug,
                            active=True,
                            uploaded=False,
                    ):
                        trigger_build(project=version.project, version=version)
                elif version == EXTERNAL:
                    log.info('Updating all external versions for %s', slug)
                    for version in Version.external.filter(
                            project__slug=slug,
                            active=True,
                            uploaded=False,
                    ):
                        trigger_build(project=version.project, version=version)
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
                    trigger_build(project=version.project, version=version)

                log.info('Updating all docs')
                for project in Project.objects.all():
                    # pylint: disable=no-value-for-parameter
                    default_version = project.get_default_version()
                    version = project.versions.get(slug=default_version)
                    trigger_build(project=version.project, version=version)

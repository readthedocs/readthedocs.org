"""
Custom management command to rebuild documentation for all projects.

Invoked via ``./manage.py update_repos``.
"""

import structlog

from django.core.management.base import BaseCommand

from readthedocs.builds.constants import EXTERNAL, INTERNAL
from readthedocs.builds.models import Version
from readthedocs.core.utils import trigger_build
from readthedocs.projects.models import Project

log = structlog.get_logger(__name__)


class Command(BaseCommand):

    """Management command for rebuilding documentation on projects."""

    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument('--slugs', nargs='+', type=str)

        parser.add_argument(
            '-V',
            dest='version',
            default='all',
            help='Build a version, or all versions',
        )

    def handle(self, *args, **options):
        version = options['version']
        slugs = options.get('slugs', [])

        if slugs:
            for slug in slugs:
                if version == 'all':
                    log.info('Updating all versions.', project_slug=slug)
                    for version in Version.objects.filter(
                            project__slug=slug,
                            active=True,
                            uploaded=False,
                    ):
                        trigger_build(project=version.project, version=version)
                elif version == INTERNAL:
                    log.info('Updating all internal versions.', project_slug=slug)
                    for version in Version.internal.filter(
                            project__slug=slug,
                            active=True,
                            uploaded=False,
                    ):
                        trigger_build(project=version.project, version=version)
                elif version == EXTERNAL:
                    log.info('Updating all external versions.', project_slug=slug)
                    for version in Version.external.filter(
                            project__slug=slug,
                            active=True,
                            uploaded=False,
                    ):
                        trigger_build(project=version.project, version=version)
                elif version:
                    log.info(
                        'Updating version for project.',
                        version_slug=version.slug,
                        project_slug=slug,
                    )
                    for version in Version.objects.filter(
                            project__slug=slug,
                            slug=version,
                    ):
                        trigger_build(project=version.project, version=version)
                else:
                    p = Project.all_objects.get(slug=slug)
                    log.info('Building ...', project_slug=p.slug)
                    trigger_build(project=p)
        else:
            if version == 'all':
                log.info('Updating all versions')
                for version in Version.objects.filter(
                        active=True,
                        uploaded=False,
                ):
                    trigger_build(project=version.project, version=version)
            elif version == INTERNAL:
                log.info('Updating all internal versions')
                for version in Version.internal.filter(
                        active=True,
                        uploaded=False,
                ):
                    trigger_build(project=version.project, version=version)
            elif version == EXTERNAL:
                log.info('Updating all external versions')
                for version in Version.external.filter(
                        active=True,
                        uploaded=False,
                ):
                    trigger_build(project=version.project, version=version)
            elif version:
                log.info('Updating version.', version_slug=version.slug)
                for version in Version.objects.filter(
                        slug=version,
                ):
                    trigger_build(project=version.project, version=version)

            else:
                log.info('Updating all docs')
                for project in Project.objects.all():
                    # pylint: disable=no-value-for-parameter
                    default_version = project.get_default_version()
                    version = project.versions.get(slug=default_version)
                    trigger_build(project=version.project, version=version)

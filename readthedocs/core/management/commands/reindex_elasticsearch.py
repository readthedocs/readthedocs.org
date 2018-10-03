"""Reindex Elastic Search indexes"""

from __future__ import absolute_import
import logging
from optparse import make_option

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.conf import settings

from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Version
from readthedocs.projects.tasks import update_search

log = logging.getLogger(__name__)


class Command(BaseCommand):

    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            '-p',
            dest='project',
            default='',
            help='Project to index'
        )

    def handle(self, *args, **options):
        """Build/index all versions or a single project's version"""
        project = options['project']

        queryset = Version.objects.all()

        if project:
            queryset = queryset.filter(project__slug=project)
            if not queryset.exists():
                raise CommandError(
                    'No project with slug: {slug}'.format(slug=project))
            log.info("Building all versions for %s", project)
        elif getattr(settings, 'INDEX_ONLY_LATEST', True):
            queryset = queryset.filter(slug=LATEST)

        for version in queryset:
            log.info("Reindexing %s", version)
            try:
                commit = version.project.vcs_repo(version.slug).commit
            except:  # noqa
                # An exception can be thrown here in production, but it's not
                # documented what the exception here is
                commit = None

            try:
                update_search(version.pk, commit,
                              delete_non_commit_files=False)
            except Exception as e:
                log.exception('Reindex failed for %s, %s', version, e)

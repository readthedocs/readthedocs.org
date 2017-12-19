# -*- coding: utf-8 -*-
"""Reindex Elastic Search indexes."""

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import logging
import socket
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Version
from readthedocs.projects.tasks import update_search

log = logging.getLogger(__name__)


class Command(BaseCommand):

    help = __doc__
    option_list = BaseCommand.option_list + (
        make_option('-p',
                    dest='project',
                    default='',
                    help='Project to index'),
        make_option('-l',
                    dest='only_latest',
                    default=False,
                    action='store_true',
                    help='Only index latest'),
    )

    def handle(self, *args, **options):
        """Build/index all versions or a single project's version."""
        project = options['project']
        only_latest = options['only_latest']

        queryset = Version.objects.filter(active=True)

        if project:
            queryset = queryset.filter(project__slug=project)
            if not queryset.exists():
                raise CommandError(
                    u'No project with slug: {slug}'.format(slug=project))
            log.info(u'Building all versions for %s', project)
        if only_latest:
            log.warning('Indexing only latest')
            queryset = queryset.filter(slug=LATEST)

        for version_pk, version_slug, project_slug in queryset.values_list(
                'pk', 'slug', 'project__slug'):
            log.info(u'Reindexing %s:%s' % (project_slug, version_slug))
            try:
                update_search.apply_async(
                    kwargs=dict(
                        version_pk=version_pk,
                        commit='reindex',
                        delete_non_commit_files=False
                    ),
                    priority=0,
                    queue=socket.gethostname()
                )
            except Exception:
                log.exception(u'Reindexing failed for %s:%s' % (project_slug, version_slug))

# -*- coding: utf-8 -*-

"""Generate metadata for all projects."""

import logging

from django.core.management.base import BaseCommand

from readthedocs.core.utils import broadcast
from readthedocs.projects import tasks
from readthedocs.projects.models import Project


log = logging.getLogger(__name__)


class Command(BaseCommand):

    help = __doc__

    def handle(self, *args, **options):
        queryset = Project.objects.all()
        for p in queryset:
            log.info('Generating metadata for %s', p)
            try:
                broadcast(
                    type='app',
                    task=tasks.update_static_metadata,
                    args=[p.pk],
                )
            except Exception:
                log.exception('Build failed for %s', p)

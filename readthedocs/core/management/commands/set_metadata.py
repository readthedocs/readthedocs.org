"""Generate metadata for all projects"""

from __future__ import absolute_import
import logging

from django.core.management.base import BaseCommand

from readthedocs.projects import tasks
from readthedocs.projects.models import Project
from readthedocs.core.utils import broadcast

log = logging.getLogger(__name__)


class Command(BaseCommand):

    help = __doc__

    def handle(self, *args, **options):
        queryset = Project.objects.all()
        for p in queryset:
            log.info("Generating metadata for %s", p)
            try:
                broadcast(type='app', task=tasks.update_static_metadata, args=[p.pk])
            except Exception:
                log.error('Build failed for %s', p, exc_info=True)

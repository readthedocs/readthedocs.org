import logging
from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings

from projects import tasks
from projects.models import Project

log = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        queryset = Project.objects.all()
        for p in queryset:
            log.info("Generating metadata for %s" % p)
            try:
                tasks.update_static_metadata(p.pk)
            except Exception:
                log.error('Build failed for %s' % p, exc_info=True)

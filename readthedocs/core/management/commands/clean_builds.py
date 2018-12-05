"""Clean up stable build paths per project version"""

from __future__ import absolute_import
from datetime import timedelta
import logging
from optparse import make_option

from django.core.management.base import BaseCommand
from django.db.models import Max
from django.utils import timezone

from readthedocs.builds.models import Build, Version

log = logging.getLogger(__name__)


class Command(BaseCommand):

    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            dest='days',
            type='int',
            default=365,
            help='Find builds older than DAYS days, default: 365'
        )

        parser.add_argument(
            '--dryrun',
            action='store_true',
            dest='dryrun',
            help='Perform dry run on build cleanup'
        )

    def handle(self, *args, **options):
        """Find stale builds and remove build paths"""
        max_date = timezone.now() - timedelta(days=options['days'])
        queryset = (Build.objects
                    .values('project', 'version')
                    .annotate(max_date=Max('date'))
                    .filter(max_date__lt=max_date)
                    .order_by('-max_date'))
        for build in queryset:
            try:
                # Get version from build version id, perform sanity check on
                # latest build date
                version = Version.objects.get(id=build['version'])
                latest_build = version.builds.latest('date')
                if latest_build.date > max_date:
                    log.warning(
                        '%s is newer than %s',
                        latest_build,
                        max_date,
                    )
                path = version.get_build_path()
                if path is not None:
                    log.info(
                        'Found stale build path for %s at %s, last used on %s',
                        version,
                        path,
                        latest_build.date,
                    )
                    if not options['dryrun']:
                        version.clean_build_path()
            except Version.DoesNotExist:
                pass

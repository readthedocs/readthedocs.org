from datetime import datetime, timedelta
import logging
from optparse import make_option

from django.core.management.base import BaseCommand
from django.db.models import Max

from builds.models import Build, Version
from builds.utils import clean_build_path

log = logging.getLogger(__name__)


class Command(BaseCommand):

    help = ('Clean up stale build paths per project version')

    option_list = BaseCommand.option_list + (
        make_option('--days',
                    dest='days',
                    type='int',
                    default=365,
                    help='Find builds older than DAYS days, default: 365'),
        make_option('--dryrun',
                    action='store_true',
                    dest='dryrun',
                    help='Perform dry run on build cleanup'),
    )

    def handle(self, *args, **options):
        '''
        Find stale builds and remove build paths
        '''
        max_date = datetime.now() - timedelta(days=options['days'])
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
                    log.warn('{0} is newer than {1}'.format(
                        latest_build, max_date))
                    next
                path = version.get_build_path()
                if path is not None:
                    log.info(
                        ('Found stale build path for {0} '
                         'at {1}, last used on {2}').format(
                            version, path, latest_build.date))
                    if not options['dryrun']:
                        clean_build_path(version)
            except Version.DoesNotExist:
                pass

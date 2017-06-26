"""Sync builds to the current machine"""

from __future__ import absolute_import
from datetime import datetime, timedelta
import logging
from optparse import make_option

from django.core.management.base import BaseCommand

from readthedocs.builds.models import Version
from readthedocs.projects.tasks import move_files
from readthedocs.core.utils import broadcast

log = logging.getLogger(__name__)


class Command(BaseCommand):

    help = __doc__

    option_list = BaseCommand.option_list + (
        make_option('--days',
                    dest='days',
                    type='int',
                    default=365,
                    help='Find builds older than DAYS days, default: 365'),
        make_option('--broadcast',
                    action='store_true',
                    dest='broadcast',
                    help='Use the current machine'),
    )

    def handle(self, *args, **options):
        """Find stale builds and remove build paths"""
        max_date = datetime.now() - timedelta(days=options['days'])
        versions = Version.objects.filter(
            builds__date__gt=max_date,
            builds__success=True,
        ).distinct()
        print('Syncing {} versions'.format(versions.count()))
        for version in versions:
            build = version.builds.first()
            kwargs = {
                'version_pk': version.pk,
                'hostname': build.builder,
                'html': True,
                'localmedia': True,
                'search': False,
                'pdf': version.project.enable_pdf_build,
                'epub': version.project.enable_epub_build,
            }
            if options['broadcast']:
                move_files.delay(*args)
                broadcast(type='app', task=move_files, kwargs=kwargs)
            else:
                move_files(**kwargs)

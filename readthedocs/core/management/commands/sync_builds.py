import logging

from django.core.management.base import BaseCommand
from optparse import make_option
from builds.models import Version
from core.utils import copy_to_app_servers

log = logging.getLogger(__name__)

class Command(BaseCommand):
    """Custom management command to rebuild documentation for all projects on
    the site. Invoked via ``./manage.py update_repos``.
    """

    option_list = BaseCommand.option_list + (
        make_option('-V',
            dest='version',
            default=None,
            help='Build a version, or all versions'
            ),
        make_option('-c',
            action='store_true',
            dest='checkout',
            default=False,
            help='sync checkouts'
            ),
        )

    def handle(self, *args, **options):
        version = options['version']
        if len(args):
            for slug in args:
                log.info("Updating all versions for %s" % slug)
                for version in Version.objects.filter(project__slug=slug,
                                                      active=True):
                    path = version.project.rtd_build_path(version.slug)
                    copy_to_app_servers(path, path)
        else:
            log.info("Updating all versions")
            for version in Version.objects.filter(active=True):
                try:
                    log.info("Syncing %s" % version)
                    if options['checkout']:
                        path = version.project.checkout_path(version.slug)
                    else:
                        path = version.project.rtd_build_path(version.slug)
                    copy_to_app_servers(path, path)
                except Exception, e:
                    log.error("Failed to update %s" % version, exc_info=True)

    @property
    def help(self):
        return Command.__doc__

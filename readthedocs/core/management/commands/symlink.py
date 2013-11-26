import logging

from django.core.management.base import BaseCommand

from projects import tasks
from tastyapi import apiv2 as api

log = logging.getLogger(__name__)

class Command(BaseCommand):
    def handle(self, *args, **options):
        if len(args):
            for slug in args:
                version_data = api.version().get(project=slug, slug='latest')['results'][0]
                v = tasks.make_api_version(version_data)
                log.info("Symlinking %s" % v)
                tasks.symlink_subprojects(v)
                tasks.symlink_cnames(v)
                tasks.symlink_translations(v)

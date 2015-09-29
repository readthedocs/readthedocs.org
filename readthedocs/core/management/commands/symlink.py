import logging

from django.core.management.base import BaseCommand
from django.conf import settings

from readthedocs.projects import utils
from readthedocs.projects.models import Project

import redis

log = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        if len(args):
            if args[0] == "cnames":
                log.info("Updating all CNAME Symlinks")
                redis_conn = redis.Redis(**settings.REDIS)
                slugs = redis_conn.keys('rtd_slug:v1:*')
                slugs = [slug.replace("rtd_slug:v1:", "") for slug in slugs]
                for slug in slugs:
                    try:
                        log.info("Got slug from redis: %s" % slug)
                        utils.symlink(project=Project.objects.get(slug=slug))
                    except Exception, e:
                        print e
            else:
                for slug in args:
                    utils.symlink(project=Project.objects.get(slug=slug))

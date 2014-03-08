import logging
from optparse import make_option

from django.core.management.base import BaseCommand
from projects import tasks
from tastyapi import api


log = logging.getLogger(__name__)


class Command(BaseCommand):
    """Custom management command to rebuild documentation for all projects on
    the site. Invoked via ``./manage.py update_repos``.
    """

    def handle(self, *args, **options):
        if len(args):
            for slug in args:
                version_data = api.version(slug).get(slug="latest")['objects'][0]
                version = tasks.make_api_version(version_data)
                log.info("Building %s" % version)
                tasks.docker_build(version_pk=version.pk)

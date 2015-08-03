import logging

from django.core.management.base import BaseCommand
from django.conf import settings

from readthedocs.builds.constants import LATEST
from readthedocs.projects import tasks, utils


log = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        if len(args):
            for slug in args:
                tasks.update_imported_docs(
                    utils.version_from_slug(slug, LATEST).pk
                )

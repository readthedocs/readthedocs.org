"""Trigger build for project slug."""

import structlog

from django.core.management.base import LabelCommand

from readthedocs.builds.constants import LATEST
from readthedocs.projects.utils import version_from_slug
from readthedocs.projects.tasks.builds import sync_repository_task


log = structlog.get_logger(__name__)


class Command(LabelCommand):

    help = __doc__

    def handle_label(self, label, **options):
        version = version_from_slug(label, LATEST)
        sync_repository_task.delay(version.pk)

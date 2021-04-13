# -*- coding: utf-8 -*-

"""Trigger build for project slug."""

import logging

from django.core.management.base import LabelCommand

from readthedocs.builds.constants import LATEST
from readthedocs.projects import tasks, utils


log = logging.getLogger(__name__)


class Command(LabelCommand):

    help = __doc__

    def handle_label(self, label, **options):
        version = utils.version_from_slug(label, LATEST)
        tasks.sync_repository_task(version.pk)

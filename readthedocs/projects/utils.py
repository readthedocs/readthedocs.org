# -*- coding: utf-8 -*-

"""Utility functions used by projects."""

import logging
import os

from django.conf import settings


log = logging.getLogger(__name__)


# TODO make this a classmethod of Version
def version_from_slug(slug, version):
    from readthedocs.builds.models import Version, APIVersion
    from readthedocs.restapi.client import api
    if getattr(settings, 'DONT_HIT_DB', True):
        version_data = api.version().get(
            project=slug,
            slug=version,
        )['results'][0]
        v = APIVersion(**version_data)
    else:
        v = Version.objects.get(project__slug=slug, slug=version)
    return v

# -*- coding: utf-8 -*-

"""Constants for the builds app."""

from django.conf import settings
from django.utils.translation import ugettext_lazy as _


BUILD_STATE_TRIGGERED = 'triggered'
BUILD_STATE_CLONING = 'cloning'
BUILD_STATE_INSTALLING = 'installing'
BUILD_STATE_BUILDING = 'building'
BUILD_STATE_FINISHED = 'finished'

BUILD_STATE = (
    (BUILD_STATE_TRIGGERED, _('Triggered')),
    (BUILD_STATE_CLONING, _('Cloning')),
    (BUILD_STATE_INSTALLING, _('Installing')),
    (BUILD_STATE_BUILDING, _('Building')),
    (BUILD_STATE_FINISHED, _('Finished')),
)

BUILD_TYPES = (
    ('html', _('HTML')),
    ('pdf', _('PDF')),
    ('epub', _('Epub')),
    # There is currently no support for building man/dash formats, but we keep
    # it there since the DB might still contain those values for legacy
    # projects.
    ('man', _('Manpage')),
    ('dash', _('Dash')),
)

BRANCH = 'branch'
TAG = 'tag'
PULL_REQUEST = 'pull_request'
UNKNOWN = 'unknown'

VERSION_TYPES = (
    (BRANCH, _('Branch')),
    (TAG, _('Tag')),
    (PULL_REQUEST, _('Pull Request')),
    (UNKNOWN, _('Unknown')),
)

LATEST = settings.RTD_LATEST
LATEST_VERBOSE_NAME = settings.RTD_LATEST_VERBOSE_NAME

STABLE = settings.RTD_STABLE
STABLE_VERBOSE_NAME = settings.RTD_STABLE_VERBOSE_NAME

# Those names are specialcased version names. They do not correspond to
# branches/tags in a project's repository.
NON_REPOSITORY_VERSIONS = (
    LATEST,
    STABLE,
)

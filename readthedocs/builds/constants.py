"""Constants for the builds app."""

from __future__ import absolute_import
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

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
UNKNOWN = 'unknown'

VERSION_TYPES = (
    (BRANCH, _('Branch')),
    (TAG, _('Tag')),
    (UNKNOWN, _('Unknown')),
)

LATEST = getattr(settings, 'RTD_LATEST', 'latest')
LATEST_VERBOSE_NAME = getattr(settings, 'RTD_LATEST_VERBOSE_NAME', 'latest')

STABLE = getattr(settings, 'RTD_STABLE', 'stable')
STABLE_VERBOSE_NAME = getattr(settings, 'RTD_STABLE_VERBOSE_NAME', 'stable')

# Those names are specialcased version names. They do not correspond to
# branches/tags in a project's repository.
NON_REPOSITORY_VERSIONS = (
    LATEST,
    STABLE,
)

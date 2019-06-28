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

# Manager name for Internal Versions or Builds.
# ie: Versions and Builds Excluding pull request/merge request Versions and Builds.
INTERNAL = 'internal'
# Manager name for External Versions or Builds.
# ie: Only pull request/merge request Versions and Builds.
EXTERNAL = 'external'

BRANCH = 'branch'
TAG = 'tag'
UNKNOWN = 'unknown'

VERSION_TYPES = (
    (BRANCH, _('Branch')),
    (TAG, _('Tag')),
    (EXTERNAL, _('External')),
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

# GitHub Build Statuses
GITHUB_BUILD_STATE_FAILURE = 'failure'
GITHUB_BUILD_STATE_PENDING = 'pending'
GITHUB_BUILD_STATE_SUCCESS = 'success'

# GitHub Build Statuses
GITLAB_BUILD_STATE_FAILURE = 'failed'
GITLAB_BUILD_STATE_PENDING = 'pending'
GITLAB_BUILD_STATE_SUCCESS = 'success'

# General Build Statuses
BUILD_STATUS_FAILURE = 'failed'
BUILD_STATUS_PENDING = 'pending'
BUILD_STATUS_SUCCESS = 'success'

# Used to select correct Build status to be sent for each service
SELECT_BUILD_STATUS = {
    BUILD_STATUS_FAILURE: {
        'github': GITHUB_BUILD_STATE_FAILURE,
        'gitlab': GITLAB_BUILD_STATE_FAILURE,
    },
    BUILD_STATUS_PENDING: {
        'github': GITHUB_BUILD_STATE_PENDING,
        'gitlab': GITLAB_BUILD_STATE_PENDING,
    },
    BUILD_STATUS_SUCCESS: {
        'github': GITHUB_BUILD_STATE_SUCCESS,
        'gitlab': GITLAB_BUILD_STATE_SUCCESS,
    },
}

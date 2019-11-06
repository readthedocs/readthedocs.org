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
EXTERNAL_TEXT = _('External')

BRANCH = 'branch'
BRANCH_TEXT = _('Branch')
TAG = 'tag'
TAG_TEXT = _('Tag')
UNKNOWN = 'unknown'
UNKNOWN_TEXT = _('Unknown')

VERSION_TYPES = (
    (BRANCH, BRANCH_TEXT),
    (TAG, TAG_TEXT),
    (EXTERNAL, EXTERNAL_TEXT),
    (UNKNOWN, UNKNOWN_TEXT),
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

# General Build Statuses
BUILD_STATUS_FAILURE = 'failed'
BUILD_STATUS_PENDING = 'pending'
BUILD_STATUS_SUCCESS = 'success'

# GitHub Build Statuses
GITHUB_BUILD_STATUS_FAILURE = 'failure'
GITHUB_BUILD_STATUS_PENDING = 'pending'
GITHUB_BUILD_STATUS_SUCCESS = 'success'

# GitLab Build Statuses
GITLAB_BUILD_STATUS_FAILURE = 'failed'
GITLAB_BUILD_STATUS_PENDING = 'pending'
GITLAB_BUILD_STATUS_SUCCESS = 'success'

# Used to select correct Build status and description to be sent to each service API
SELECT_BUILD_STATUS = {
    BUILD_STATUS_FAILURE: {
        'github': GITHUB_BUILD_STATUS_FAILURE,
        'gitlab': GITLAB_BUILD_STATUS_FAILURE,
        'description': 'Read the Docs build failed!',
    },
    BUILD_STATUS_PENDING: {
        'github': GITHUB_BUILD_STATUS_PENDING,
        'gitlab': GITLAB_BUILD_STATUS_PENDING,
        'description': 'Read the Docs build is in progress!',
    },
    BUILD_STATUS_SUCCESS: {
        'github': GITHUB_BUILD_STATUS_SUCCESS,
        'gitlab': GITLAB_BUILD_STATUS_SUCCESS,
        'description': 'Read the Docs build succeeded!',
    },
}

RTD_BUILD_STATUS_API_NAME = 'continuous-documentation/read-the-docs'

GITHUB_EXTERNAL_VERSION_NAME = 'Pull Request'
GITLAB_EXTERNAL_VERSION_NAME = 'Merge Request'
GENERIC_EXTERNAL_VERSION_NAME = 'External Version'


# Automation rules

ALL_VERSIONS = 'all-versions'
ALL_VERSIONS_REGEX = r'.*'
SEMVER_VERSIONS = 'semver-versions'
SEMVER_VERSIONS_REGEX = r'^v?(\d+\.)(\d+\.)(\d+)(-.+)?$'


PREDEFINED_MATCH_ARGS = (
    (ALL_VERSIONS, _('Any version')),
    (SEMVER_VERSIONS, _('SemVer versions')),
    (None, _('Custom match')),
)

PREDEFINED_MATCH_ARGS_VALUES = {
    ALL_VERSIONS: ALL_VERSIONS_REGEX,
    SEMVER_VERSIONS: SEMVER_VERSIONS_REGEX,
}

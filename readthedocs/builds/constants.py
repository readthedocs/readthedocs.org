"""Constants for the builds app."""

from django.conf import settings
from django.utils.translation import gettext_lazy as _


# BUILD_STATE is our *INTERNAL* representation of build states.
# This is not to be confused with external representations of 'status'
# that are sent back to Git providers.
BUILD_STATE_TRIGGERED = "triggered"
BUILD_STATE_CLONING = "cloning"
BUILD_STATE_INSTALLING = "installing"
BUILD_STATE_BUILDING = "building"
BUILD_STATE_UPLOADING = "uploading"
BUILD_STATE_FINISHED = "finished"
BUILD_STATE_CANCELLED = "cancelled"

BUILD_STATE = (
    (BUILD_STATE_TRIGGERED, _("Triggered")),
    (BUILD_STATE_CLONING, _("Cloning")),
    (BUILD_STATE_INSTALLING, _("Installing")),
    (BUILD_STATE_BUILDING, _("Building")),
    (BUILD_STATE_UPLOADING, _("Uploading")),
    (BUILD_STATE_FINISHED, _("Finished")),
    (BUILD_STATE_CANCELLED, _("Cancelled")),
)

BUILD_FINAL_STATES = (
    BUILD_STATE_FINISHED,
    BUILD_STATE_CANCELLED,
)

BUILD_TYPES = (
    ("html", _("HTML")),
    ("pdf", _("PDF")),
    ("epub", _("Epub")),
    # There is currently no support for building man/dash formats, but we keep
    # it there since the DB might still contain those values for legacy
    # projects.
    ("man", _("Manpage")),
    ("dash", _("Dash")),
)

# Manager name for Internal Versions or Builds.
# ie: Versions and Builds Excluding pull request/merge request Versions and Builds.
INTERNAL = "internal"
# Manager name for External Versions or Builds.
# ie: Only pull request/merge request Versions and Builds.
EXTERNAL = "external"
EXTERNAL_TEXT = _("External")

BRANCH = "branch"
BRANCH_TEXT = _("Branch")
TAG = "tag"
TAG_TEXT = _("Tag")
UNKNOWN = "unknown"
UNKNOWN_TEXT = _("Unknown")

VERSION_TYPES = (
    (BRANCH, BRANCH_TEXT),
    (TAG, TAG_TEXT),
    (EXTERNAL, EXTERNAL_TEXT),
    (UNKNOWN, UNKNOWN_TEXT),
)
EXTERNAL_VERSION_STATE_OPEN = "open"
EXTERNAL_VERSION_STATE_CLOSED = "closed"
EXTERNAL_VERSION_STATES = (
    (EXTERNAL_VERSION_STATE_OPEN, _("Open")),
    (EXTERNAL_VERSION_STATE_CLOSED, _("Closed")),
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

# General build statuses, i.e. the status that is reported back to the
# user on a Git Provider. This not the same as BUILD_STATE which the internal
# representation.
BUILD_STATUS_FAILURE = "failed"
BUILD_STATUS_PENDING = "pending"
BUILD_STATUS_SUCCESS = "success"

# GitHub Build Statuses
GITHUB_BUILD_STATUS_FAILURE = "failure"
GITHUB_BUILD_STATUS_PENDING = "pending"
GITHUB_BUILD_STATUS_SUCCESS = "success"

# GitLab Build Statuses
GITLAB_BUILD_STATUS_FAILURE = "failed"
GITLAB_BUILD_STATUS_PENDING = "pending"
GITLAB_BUILD_STATUS_SUCCESS = "success"

# Used to select correct Build status and description to be sent to each service API
SELECT_BUILD_STATUS = {
    BUILD_STATUS_FAILURE: {
        "github": GITHUB_BUILD_STATUS_FAILURE,
        "gitlab": GITLAB_BUILD_STATUS_FAILURE,
        "description": "Read the Docs build failed!",
    },
    BUILD_STATUS_PENDING: {
        "github": GITHUB_BUILD_STATUS_PENDING,
        "gitlab": GITLAB_BUILD_STATUS_PENDING,
        "description": "Read the Docs build is in progress!",
    },
    BUILD_STATUS_SUCCESS: {
        "github": GITHUB_BUILD_STATUS_SUCCESS,
        "gitlab": GITLAB_BUILD_STATUS_SUCCESS,
        "description": "Read the Docs build succeeded!",
    },
}

GITHUB_EXTERNAL_VERSION_NAME = "Pull Request"
GITLAB_EXTERNAL_VERSION_NAME = "Merge Request"
GENERIC_EXTERNAL_VERSION_NAME = "External Version"


# Automation rules

ALL_VERSIONS = "all-versions"
ALL_VERSIONS_REGEX = r".*"
SEMVER_VERSIONS = "semver-versions"

# Pattern referred from
# https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
# without naming the capturing groups and with the addition of
# allowing an optional "v" prefix.
SEMVER_VERSIONS_REGEX = r"^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"  # noqa


PREDEFINED_MATCH_ARGS = (
    (ALL_VERSIONS, _("Any version")),
    (SEMVER_VERSIONS, _("SemVer versions")),
    (None, _("Custom match")),
)

PREDEFINED_MATCH_ARGS_VALUES = {
    ALL_VERSIONS: ALL_VERSIONS_REGEX,
    SEMVER_VERSIONS: SEMVER_VERSIONS_REGEX,
}

BUILD_STATUS_NORMAL = "normal"
BUILD_STATUS_CHOICES = ((BUILD_STATUS_NORMAL, "Normal"),)


MAX_BUILD_COMMAND_SIZE = 1000000  # This keeps us under Azure's upload limit

LOCK_EXPIRE = 60 * 180  # Lock expires in 3 hours

# All artifact types supported by Read the Docs.
# They match the output directory (`_readthedocs/<artifact type>`)
ARTIFACT_TYPES = (
    "html",
    "json",
    "htmlzip",
    "pdf",
    "epub",
)
# Artifacts that are not deleted when uploading to the storage,
# even if they weren't re-built in the build process.
UNDELETABLE_ARTIFACT_TYPES = (
    "html",
    "json",
)
# Artifacts that expect one and only one file in the output directory.
# NOTE: currently, this is a limitation that we are consider to remove
# https://github.com/readthedocs/readthedocs.org/issues/9931#issuecomment-1403415757
ARTIFACT_TYPES_WITHOUT_MULTIPLE_FILES_SUPPORT = (
    "htmlzip",
    "epub",
    "pdf",
)

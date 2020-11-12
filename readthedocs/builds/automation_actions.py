"""
Actions used for the automation rules.

Each function will receive the following args:

- version: The version object where the action will be applied
- match_result: The result from the match option
- action_arg: An additional argument to apply the action
"""

import logging

from readthedocs.builds.utils import match_regex
from readthedocs.core.utils import trigger_build
from readthedocs.projects.constants import PRIVATE, PUBLIC

log = logging.getLogger(__name__)


def activate_version(version, match_result, action_arg, *args, **kwargs):
    """
    Sets version as active.

    It triggers a build if the version isn't built.
    """
    version.active = True
    version.save()
    if not version.built:
        trigger_build(
            project=version.project,
            version=version
        )


def build_external_version(version, match_result, action_arg, version_data, **kwargs):
    """
    Build an external version if matches the given base branch.

    :param action_arg: A pattern to match the base branch.
    :param version_data: `ExternalVersionData` instance.
    :returns: A boolean indicating if the build was triggered.
    """
    base_branch_regex = action_arg
    result = match_regex(
        base_branch_regex,
        version_data.base_branch,
    )
    if result:
        trigger_build(
            project=version.project,
            version=version,
            commit=version.identifier,
        )
        return True
    return False


def set_default_version(version, match_result, action_arg, *args, **kwargs):
    """
    Sets version as the project's default version.

    The version is activated first.
    """
    activate_version(version, match_result, action_arg)
    project = version.project
    project.default_version = version.slug
    project.save()


def hide_version(version, match_result, action_arg, *args, **kwargs):
    """
    Sets version as hidden.

    It also activates the version and triggers a build.
    """
    version.hidden = True
    version.save()

    if not version.active:
        activate_version(version, match_result, action_arg)


def set_public_privacy_level(version, match_result, action_arg, *args, **kwargs):
    """Sets the privacy_level of the version to public."""
    version.privacy_level = PUBLIC
    version.save()


def set_private_privacy_level(version, match_result, action_arg, *args, **kwargs):
    """Sets the privacy_level of the version to private."""
    version.privacy_level = PRIVATE
    version.save()


def delete_version(version, match_result, action_arg, *args, **kwargs):
    """Delete a version if isn't marked as the default version."""
    if version.project.default_version == version.slug:
        log.info(
            "Skipping deleting default version. project=%s version=%s",
            version.project.slug, version.slug,
        )
        return
    version.delete()

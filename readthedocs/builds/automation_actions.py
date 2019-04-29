"""
Actions used for the automation rules.

Each function will receive the following args:

- version: The version object where the action will be applied
- match_result: The result from the match option
- action_arg: An additional argument to apply the action
"""

from readthedocs.core.utils import trigger_build


def activate_version(version, match_result, action_arg, *args, **kwargs):
    """
    Sets version as active

    It triggers a build if the version isn't built.
    """
    version.active = True
    version.save()
    if not version.built:
        trigger_build(
            project=version.project,
            version=version
        )


def set_default_version(version, match_result, action_arg, *args, **kwargs):
    """
    Sets version as the project's default version.

    The version is activated first.
    """
    activate_version(version, match_result, action_arg)
    project = version.project
    project.default_version = version.slug
    project.save()

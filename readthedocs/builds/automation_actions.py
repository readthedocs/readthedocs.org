"""
Actions used for the automation rules.

Each function will receive the following args:

- version: The version object where the action will be applied
- match_result: The result from the match option
- action_arg: An additional argument to apply the action
"""


def activate_version(version, match_result, action_arg, *args, **kwargs):
    version.active = True
    version.save()


def set_default_version(version, match_result, action_arg, *args, **kwargs):
    project = version.project
    project.default_version = version.verbose_name
    project.save()

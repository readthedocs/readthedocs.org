"""
Actions used for the automation rules.

Each function will receive the following args:

- version: The version object where the action will be applied
- match_result: The result from the match option
- action_arg: An additional argument to apply the action
"""


def activate_version_from_regex(
        version, match_result, action_arg, *args, **kwargs
):
    version.active = True
    version.save()

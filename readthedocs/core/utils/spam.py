"""
Spam fighting utilities.

This is a proxy for the spam fighting utilities that are in
the readthedocsext.spamfighting private module.
"""

from django.conf import settings

from readthedocs.core.permissions import AdminPermission


def get_spam_score(project):
    if "readthedocsext.spamfighting" in settings.INSTALLED_APPS:
        from readthedocsext.spamfighting.utils import spam_score

        return spam_score(project)
    return 0


def is_spammer(user):
    """
    Determine if the user is a spammer.

    A user is considered a spammer if they are banned or if any of the projects
    they have access to have reached the dashboard denied threshold.
    """
    if user.profile.banned:
        return True

    for project in AdminPermission.projects(user=user, admin=True, member=True):
        if get_spam_score(project) >= settings.RTD_SPAM_THRESHOLD_DONT_SHOW_DASHBOARD:
            return True

    return False

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


def is_spam_project(project):
    """
    Determine if the project is spam.

    A project is considered spam if it has reached the dashboard denied threshold,
    or if has been explicitly marked as spam by an admin (which is the maximum score).
    """
    return get_spam_score(project) >= settings.RTD_SPAM_THRESHOLD_DONT_SHOW_DASHBOARD


def is_spammer(user):
    """
    Determine if the user is a spammer.

    A user is considered a spammer if they are banned or if any of the projects
    they have access to have reached the dashboard denied threshold.
    """
    if user.is_anonymous:
        return False

    if user.profile.banned:
        return True

    for project in AdminPermission.projects(user=user, admin=True, member=True):
        if is_spam_project(project):
            return True

    return False


def is_spam_organization(organization):
    """
    Determine if the organization is spam.

    An organization is considered spam if:

    - Any of its owners are banned.
    - Any of its projects are considered spam.
    """
    for owner in organization.owners.all():
        if owner.profile.banned:
            return True

    for project in organization.projects.all():
        if is_spam_project(project):
            return True

    return False

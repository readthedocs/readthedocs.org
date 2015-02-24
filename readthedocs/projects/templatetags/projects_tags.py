from django import template

from distutils2.version import NormalizedVersion
from projects.utils import mkversion

register = template.Library()


def make_version(version):
    ver = mkversion(version)
    if not ver:
        if version.slug == 'latest':
            return NormalizedVersion('99999.0', error_on_huge_major_num=False)
        elif version.slug == 'stable':
            return NormalizedVersion('9999.0', error_on_huge_major_num=False)
        else:
            return NormalizedVersion('999.0', error_on_huge_major_num=False)
    return ver


@register.filter
def sort_version_aware(versions):
    """
    Takes a list of versions objects and sort them caring about version schemes
    """
    sorted_verisons = sorted(versions,
                             key=make_version,
                             reverse=True)
    return sorted_verisons


@register.filter
def is_project_user(user, project):
    """
    Return if user is a member of project.users
    """
    return user in project.users.all()

from django import template

register = template.Library()


@register.filter
def sort_version_aware(versions):
    """
    Takes a list of versions objects and sort them caring about version schemes
    """
    from distutils2.version import NormalizedVersion
    from projects.utils import mkversion
    fallback = NormalizedVersion('99999999.0', error_on_huge_major_num=False)
    return sorted(versions,
                  key=lambda v: (mkversion(v) or fallback),
                  reverse=True)


@register.filter
def is_project_user(user, project):
    """
    Return if user is a member of project.users
    """
    return user in project.users.all()

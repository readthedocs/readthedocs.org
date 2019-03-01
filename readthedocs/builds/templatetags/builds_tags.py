# -*- coding: utf-8 -*-

from django import template


register = template.Library()


@register.simple_tag
def is_latest_built_success(version):
    """
    Checks the build status of the passed version.

    Returns true if the latest build for the ``version``
    is passed else returns false.
    """
    res = version.builds.all().order_by('-date')
    if res.exists():
        return res.first().success

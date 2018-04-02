"""Build template tags and filters"""

from django import template
from readthedocs.projects.constants import PRIVATE

register = template.Library()


@register.filter
def get_docs_url(build):
    version = build.version
    private = version.privacy_level == PRIVATE
    return version.project.get_docs_url(
        version_slug=version.slug,
        private=private
    )

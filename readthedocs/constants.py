"""Common constants"""

from __future__ import absolute_import
from readthedocs.builds.version_slug import VERSION_SLUG_REGEX
from readthedocs.projects.constants import LANGUAGES_REGEX, PROJECT_SLUG_REGEX


pattern_opts = {
    'project_slug': PROJECT_SLUG_REGEX,
    'lang_slug': LANGUAGES_REGEX,
    'version_slug': VERSION_SLUG_REGEX,
    'filename_slug': '(?:.*)',
    'integer_pk': r'[\d]+',
}

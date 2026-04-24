"""Common constants."""

import re

from readthedocs.builds.version_slug import VERSION_SLUG_REGEX
from readthedocs.projects.constants import DOWNLOADABLE_MEDIA_TYPES
from readthedocs.projects.constants import LANGUAGES_REGEX
from readthedocs.projects.constants import PROJECT_SLUG_REGEX


pattern_opts = {
    "project_slug": PROJECT_SLUG_REGEX,
    "lang_slug": LANGUAGES_REGEX,
    "version_slug": VERSION_SLUG_REGEX,
    "filename_slug": "(?:.*)",
    "integer_pk": r"[\d]+",
    "downloadable_type": "|".join(re.escape(type_) for type_ in DOWNLOADABLE_MEDIA_TYPES),
}

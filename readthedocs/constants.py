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

def get_pattern(name: str) -> str:
    """
    Return a regex pattern from pattern_opts by name.
    Raises KeyError if the pattern does not exist.
    """
    return pattern_opts[name]


def list_patterns() -> list[str]:
    """
    Return a list of all available pattern names.
    """
    return list(pattern_opts.keys())
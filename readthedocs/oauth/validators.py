"""Validators for the OAuth app."""

import re

from django.core.validators import URLValidator
from django.utils.deconstruct import deconstructible


# Pattern for ``git@github.com:user/repo`` SSH format used by GitHub, GitLab, and Bitbucket
_RE_GIT_USER_SSH = re.compile(r"^[\w.+-]+@[^:]+:[^/][^:]*$")


@deconstructible
class SshURLValidator:
    """
    Validate SSH repository URLs.

    Accepts both standard SSH URL format (``ssh://git@github.com/user/repo.git``)
    and the git user format (``git@github.com:user/repo.git``) commonly used
    by GitHub, GitLab, and Bitbucket.
    """

    def __call__(self, value):
        if _RE_GIT_USER_SSH.match(value):
            return
        URLValidator(schemes=["ssh"])(value)

    def __eq__(self, other):
        return isinstance(other, SshURLValidator)


@deconstructible
class CloneURLValidator:
    """
    Validate repository clone URLs.

    Accepts HTTP, HTTPS, SSH, and git URLs, as well as the git user SSH format
    (``git@github.com:user/repo.git``) commonly used by GitHub, GitLab, and Bitbucket.
    """

    def __call__(self, value):
        if _RE_GIT_USER_SSH.match(value):
            return
        URLValidator(schemes=["http", "https", "ssh", "git"])(value)

    def __eq__(self, other):
        return isinstance(other, CloneURLValidator)

"""Project version handling."""
import unicodedata

from packaging.version import InvalidVersion, Version

from readthedocs.builds.constants import (
    LATEST_VERBOSE_NAME,
    STABLE_VERBOSE_NAME,
    TAG,
)
from readthedocs.vcs_support.backends import backend_cls


def parse_version_failsafe(version_string):
    """
    Parse a version in string form and return Version object.

    If there is an error parsing the string
    or the version doesn't have a "comparable" version number,
    ``None`` is returned.

    :param version_string: version as string object (e.g. '3.10.1')
    :type version_string: str or unicode

    :returns: version object created from a string object

    :rtype: packaging.version.Version
    """
    if not isinstance(version_string, str):
        uni_version = version_string.decode('utf-8')
    else:
        uni_version = version_string

    final_form = ''

    try:
        normalized_version = unicodedata.normalize('NFKD', uni_version)
        ascii_version = normalized_version.encode('ascii', 'ignore')
        final_form = ascii_version.decode('ascii')
        return Version(final_form)
    except InvalidVersion:
        # Handle the special case of 1.x, 2.x or 1.0.x, 1.1.x
        if final_form and '.x' in final_form:
            return parse_version_failsafe(final_form.replace('.x', '.0'))
    except UnicodeError:
        pass

    return None


def comparable_version(version_string, repo_type=None):
    """
    Can be used as ``key`` argument to ``sorted``.

    The ``LATEST`` version shall always beat other versions in comparison.
    ``STABLE`` should be listed second. If we cannot figure out the version
    number then we sort it to the bottom of the list.

    If `repo_type` is given, it adds the default "master" version
    from the VCS (master, default, trunk).
    This version is highest than LATEST and STABLE.

    :param version_string: version as string object (e.g. '3.10.1' or 'latest')
    :type version_string: str or unicode

    :param repo_type: Repository type from which the versions are generated.

    :returns: a comparable version object (e.g. 'latest' -> Version('99999.0'))

    :rtype: packaging.version.Version
    """
    highest_versions = []
    if repo_type:
        backend = backend_cls.get(repo_type)
        if backend.fallback_branch:
            highest_versions.append(backend.fallback_branch)
    highest_versions.extend([LATEST_VERBOSE_NAME, STABLE_VERBOSE_NAME])

    comparable = parse_version_failsafe(version_string)
    if not comparable:
        if version_string in highest_versions:
            position = highest_versions.index(version_string)
            version_number = str(999999 - position)
            comparable = Version(version_number)
        else:
            comparable = Version('0.01')
    return comparable


def sort_versions(version_list):
    """
    Take a list of Version models and return a sorted list.

    This only considers versions with comparable version numbers.
    It excludes versions like "latest" and "stable".

    :param version_list: list of Version models
    :type version_list: list(readthedocs.builds.models.Version)

    :returns: sorted list in descending order (latest version first) of versions

    :rtype: list(tupe(readthedocs.builds.models.Version,
            packaging.version.Version))
    """
    versions = []
    for version_obj in version_list:
        version_slug = version_obj.verbose_name
        comparable_version = parse_version_failsafe(version_slug)
        if comparable_version:
            versions.append((version_obj, comparable_version))

    return list(
        sorted(
            versions,
            key=lambda version_info: version_info[1],
            reverse=True,
        ),
    )


def highest_version(version_list):
    """
    Return the highest version for a given ``version_list``.

    :rtype: tupe(readthedocs.builds.models.Version, packaging.version.Version)
    """
    versions = sort_versions(version_list)
    if versions:
        return versions[0]
    return (None, None)


def determine_stable_version(version_list):
    """
    Determine a stable version for version list.

    :param version_list: list of versions
    :type version_list: list(readthedocs.builds.models.Version)

    :returns: version considered the most recent stable one or ``None`` if there
              is no stable version in the list

    :rtype: readthedocs.builds.models.Version
    """
    versions = sort_versions(version_list)
    versions = [
        (version_obj, comparable)
        for version_obj, comparable in versions
        if not comparable.is_prerelease
    ]

    if versions:
        # We take preference for tags over branches. If we don't find any tag,
        # we just return the first branch found.
        for version_obj, comparable in versions:
            if version_obj.type == TAG:
                return version_obj

        version_obj, comparable = versions[0]
        return version_obj
    return None

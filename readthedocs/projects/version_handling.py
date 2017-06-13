"""Project version handling"""
from __future__ import absolute_import

import unicodedata
from collections import defaultdict

from builtins import (object, range)
from packaging.version import Version
from packaging.version import InvalidVersion
import six

from readthedocs.builds.constants import LATEST_VERBOSE_NAME
from readthedocs.builds.constants import STABLE_VERBOSE_NAME


def get_major(version):
    # pylint: disable=protected-access
    return version._version.release[0]


def get_minor(version):
    # pylint: disable=protected-access
    try:
        return version._version.release[1]
    except IndexError:
        return 0


class VersionManager(object):

    """Prune list of versions based on version windows"""

    def __init__(self):
        self._state = defaultdict(lambda: defaultdict(list))

    def add(self, version):
        self._state[get_major(version)][get_minor(version)].append(version)

    def prune_major(self, num_latest):
        all_keys = sorted(set(self._state.keys()))
        major_keep = []
        for __ in range(num_latest):
            if all_keys:
                major_keep.append(all_keys.pop(-1))
        for to_remove in all_keys:
            del self._state[to_remove]

    def prune_minor(self, num_latest):
        for major, minors in list(self._state.items()):
            all_keys = sorted(set(minors.keys()))
            minor_keep = []
            for __ in range(num_latest):
                if all_keys:
                    minor_keep.append(all_keys.pop(-1))
            for to_remove in all_keys:
                del self._state[major][to_remove]

    def prune_point(self, num_latest):
        for major, minors in list(self._state.items()):
            for minor in list(minors.keys()):
                try:
                    self._state[major][minor] = sorted(
                        set(self._state[major][minor]))[-num_latest:]
                except TypeError:
                    # Raise these for now.
                    raise

    def get_version_list(self):
        versions = []
        for major_val in list(self._state.values()):
            for version_list in list(major_val.values()):
                versions.extend(version_list)
        versions = sorted(versions)
        return [
            version.public
            for version in versions
            if not version.is_prerelease]


def version_windows(versions, major=1, minor=1, point=1):
    """Return list of versions that have been pruned to version windows

    Uses :py:class:`VersionManager` to prune the list of versions

    :param versions: List of version strings
    :param major: Major version window
    :param minor: Minor version window
    :param point: Point version window
    """
    # TODO: This needs some documentation on how VersionManager etc works and
    # some examples what the expected outcome is.

    version_identifiers = []
    for version_string in versions:
        try:
            version_identifiers.append(Version(version_string))
        except (InvalidVersion, UnicodeEncodeError):
            pass

    major_version_window = major
    minor_version_window = minor
    point_version_window = point

    manager = VersionManager()
    for v in version_identifiers:
        manager.add(v)
    manager.prune_major(major_version_window)
    manager.prune_minor(minor_version_window)
    manager.prune_point(point_version_window)
    return manager.get_version_list()


def parse_version_failsafe(version_string):
    if not isinstance(version_string, six.text_type):
        uni_version = version_string.decode('utf-8')
    else:
        uni_version = version_string

    try:
        normalized_version = unicodedata.normalize('NFKD', uni_version)
        ascii_version = normalized_version.encode('ascii', 'ignore')
        final_form = ascii_version.decode('ascii')
        return Version(final_form)
    except (UnicodeError, InvalidVersion):
        return None


def comparable_version(version_string):
    """This can be used as ``key`` argument to ``sorted``.

    The ``LATEST`` version shall always beat other versions in comparison.
    ``STABLE`` should be listed second. If we cannot figure out the version
    number then we sort it to the bottom of the list.
    """
    comparable = parse_version_failsafe(version_string)
    if not comparable:
        if version_string == LATEST_VERBOSE_NAME:
            comparable = Version('99999.0')
        elif version_string == STABLE_VERBOSE_NAME:
            comparable = Version('9999.0')
        else:
            comparable = Version('0.01')
    return comparable


def sort_versions(version_list):
    """Takes a list of ``Version`` models and return a sorted list,

    The returned value is a list of two-tuples. The first is the actual
    ``Version`` model instance, the second is an instance of
    ``packaging.version.Version``. They are ordered in descending order (latest
    version first).
    """
    versions = []
    for version_obj in version_list:
        version_slug = version_obj.verbose_name
        comparable_version = parse_version_failsafe(version_slug)
        if comparable_version:
            versions.append((version_obj, comparable_version))

    return list(sorted(
        versions,
        key=lambda version_info: version_info[1],
        reverse=True))


def highest_version(version_list):
    versions = sort_versions(version_list)
    if versions:
        return versions[0]
    return (None, None)


def determine_stable_version(version_list):
    """Determine a stable version for version list

    Takes a list of ``Version`` model instances and returns the version
    instance which can be considered the most recent stable one. It will return
    ``None`` if there is no stable version in the list.
    """
    versions = sort_versions(version_list)
    versions = [
        (version_obj, comparable)
        for version_obj, comparable in versions
        if not comparable.is_prerelease]
    if versions:
        version_obj, comparable = versions[0]
        return version_obj
    return None

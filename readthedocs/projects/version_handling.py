from collections import defaultdict
from packaging.version import Version
from packaging.version import InvalidVersion

from builds.constants import LATEST_VERBOSE_NAME
from builds.constants import STABLE_VERBOSE_NAME


def get_major(version):
    return version._version.release[0]


def get_minor(version):
    try:
        return version._version.release[1]
    except IndexError:
        return 0


class VersionManager(object):
    def __init__(self):
        self._state = defaultdict(lambda: defaultdict(list))

    def add(self, version):
        self._state[get_major(version)][get_minor(version)].append(version)

    def prune_major(self, num_latest):
        all_keys = sorted(set(self._state.keys()))
        major_keep = []
        for to_keep in range(num_latest):
            if len(all_keys) > 0:
                major_keep.append(all_keys.pop(-1))
        for to_remove in all_keys:
            del self._state[to_remove]

    def prune_minor(self, num_latest):
        for major, minors in self._state.items():
            all_keys = sorted(set(minors.keys()))
            minor_keep = []
            for to_keep in range(num_latest):
                if len(all_keys) > 0:
                    minor_keep.append(all_keys.pop(-1))
            for to_remove in all_keys:
                del self._state[major][to_remove]

    def prune_point(self, num_latest):
        for major, minors in self._state.items():
            for minor in minors.keys():
                try:
                    self._state[major][minor] = sorted(set(self._state[major][minor]))[-num_latest:]
                except TypeError, e:
                    # Raise these for now.
                    raise

    def get_version_list(self):
        versions = []
        for major_val in self._state.values():
            for version_list in major_val.values():
                versions.extend(version_list)
        versions = sorted(versions)
        return [version.base_version for version in versions]


def version_windows(versions, major=1, minor=1, point=1):
    # TODO: This needs some documentation on how VersionManager etc works and
    # some examples what the expected outcome is.

    version_identifiers = []
    for version_string in versions:
        try:
            version_identifiers.append(Version(version_string))
        except InvalidVersion:
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
    try:
        return Version(version_string)
    except InvalidVersion:
        return None


def comparable_version(version_string):
    """This can be used as ``key`` argument to ``sorted``.

    The ``LATEST`` version shall always beat other versions in comparision.
    ``STABLE`` should be listed second. If we cannot figure out the version
    number then we still assume it's bigger than all other versions since we
    cannot predict what it is."""

    comparable = parse_version_failsafe(version_string)
    if not comparable:
        if version_string == LATEST_VERBOSE_NAME:
            comparable = Version('99999.0')
        elif version_string == STABLE_VERBOSE_NAME:
            comparable = Version('9999.0')
        else:
            comparable = Version('999.0')
    return comparable


def highest_version(version_list):
    versions = []
    for version_obj in version_list:
        version_slug = version_obj.verbose_name
        comparable_version = parse_version_failsafe(version_slug)
        if comparable_version:
            versions.append((version_obj, comparable_version))

    versions = list(sorted(
        versions,
        key=lambda version_info: version_info[1],
        reverse=True))
    if versions:
        return versions[0]
    else:
        return [None, None]

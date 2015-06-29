from collections import defaultdict
from packaging.version import parse
from packaging.version import LegacyVersion


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
        parsed = parse(version_string)
        # We do not want to handle legacy versions as we don't know if they
        # actually contain information about major, minor, point releases.
        if not isinstance(parsed, LegacyVersion):
            version_identifiers.append(parse(version_string))

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

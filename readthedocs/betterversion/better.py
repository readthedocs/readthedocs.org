from distlib.version import AdaptiveVersion
from collections import defaultdict

class BetterVersion(AdaptiveVersion):
    @property 
    def major_version(self):
        return self._parts[0][0]

    @property 
    def minor_version(self):
        # catch index error, maybe?
        try:
            return self._parts[0][1]
        except IndexError, e:
            return 0


class VersionManager(object):

    _state = defaultdict(lambda: defaultdict(list))

    def add(self, version):
        self._state[version.major_version][version.minor_version].append(version)

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



def version_windows(versions, major=1, minor=1, point=1, flat=False):
    major_version_window = major
    minor_version_window = minor
    point_version_window = point
    
    manager = VersionManager()
    [ manager.add(v) for v in versions]
    manager.prune_major(major_version_window)
    manager.prune_minor(minor_version_window)
    manager.prune_point(point_version_window)

    final_map = manager._state

    if flat:
        ret = []
        for major_val in final_map.values():
            for version_list in major_val.values():
                ret.extend(version_list)
        return ret
    else:
        return final_map


result = [[0.1, 0.2],
          [1.4, 1.5, 1.6, 1.7],
          [2.0]]

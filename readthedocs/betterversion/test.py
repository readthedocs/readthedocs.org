import unittest

from better import version_windows, BetterVersion 

class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.versions = [
            BetterVersion("0.1.0"), 
            BetterVersion("0.2.0"),
            BetterVersion("0.2.1"),
            BetterVersion("0.3.0"),
            BetterVersion("0.3.1"),
            BetterVersion("1.1.0"),
            BetterVersion("1.2.0"),
            BetterVersion("1.3.0"),
            BetterVersion("2.1.0"),
            BetterVersion("2.2.0"),
            BetterVersion("2.3.0"),
            BetterVersion("2.3.1"),
            BetterVersion("2.3.2"),
            BetterVersion("2.3.3"),
        ]

    def test_major(self):
        #import ipdb; ipdb.set_trace()
        major_versions = version_windows(self.versions, major=1)
        self.assertEqual(len(major_versions), 1)

        major_versions = version_windows(self.versions, major=2)
        self.assertEqual(len(major_versions), 2)

        major_versions = version_windows(self.versions, major=3)
        self.assertEqual(len(major_versions), 3)

        major_versions = version_windows(self.versions, major=4)
        self.assertEqual(len(major_versions), 3)

    def test_minor(self):
        #import ipdb; ipdb.set_trace()
        minor_versions = version_windows(self.versions, minor=1)
        self.assertEqual(len(minor_versions[2]), 1)

        minor_versions = version_windows(self.versions, minor=2)
        self.assertEqual(len(minor_versions[2]), 2)

        minor_versions = version_windows(self.versions, minor=3)
        self.assertEqual(len(minor_versions[2]), 3)
        
        minor_versions = version_windows(self.versions, minor=4)
        self.assertEqual(len(minor_versions[2]), 3)

    def test_point(self):
        #import ipdb; ipdb.set_trace()
        point_versions = version_windows(self.versions, point=1)
        self.assertEqual(len(point_versions[2][3]), 1)

        point_versions = version_windows(self.versions, point=2)
        self.assertEqual(len(point_versions[2][3]), 2)

        point_versions = version_windows(self.versions, point=3)
        self.assertEqual(len(point_versions[2][3]), 3)
        
        point_versions = version_windows(self.versions, point=4)
        self.assertEqual(len(point_versions[2][3]), 4)

        point_versions = version_windows(self.versions, point=5)
        print point_versions[2][3]
        self.assertEqual(len(point_versions[2][3]), 4)

    def test_sort(self):
        final_versions = version_windows(self.versions, major=2, minor=2, point=1)
        self.assertTrue(final_versions[1][2][0] == BetterVersion('1.2.0'))
        self.assertTrue(final_versions[1][3][0] == BetterVersion('1.3.0'))
        self.assertTrue(final_versions[2][3][0] == BetterVersion('2.3.3'))
        self.assertTrue(final_versions[2][3][0] != BetterVersion('2.3.0'))

        final_versions = version_windows(self.versions, major=1, minor=2, point=2)
        # 1 major version
        self.assertEqual(final_versions[1], {})
        # 2 minor versions
        self.assertEqual(len(final_versions[2]), 2)
        # 2 point versions
        self.assertEqual(len(final_versions[2][3]), 2)
        final_versions = version_windows(self.versions, major=1, minor=2, point=3)
        # 2 point versions
        self.assertEqual(len(final_versions[2][3]), 3)

    def test_flat(self):
        final_versions = version_windows(self.versions, major=2, minor=2, point=1, flat=True)
        self.assertEqual(len(final_versions), 4)
        self.assertEqual(
            final_versions, 
            [BetterVersion('1.2.0'), BetterVersion('1.3.0'), BetterVersion('2.2.0'), BetterVersion('2.3.3')]
        )

        final_versions = version_windows(self.versions, major=3, minor=2, point=1, flat=True)
        self.assertEqual(len(final_versions), 6)
        self.assertEqual(
            final_versions, 
            [BetterVersion('0.2.1'), BetterVersion('0.3.1'), BetterVersion('1.2.0'), BetterVersion('1.3.0'), BetterVersion('2.2.0'), BetterVersion('2.3.3')]
        )

        final_versions = version_windows(self.versions, major=3, minor=2, point=2, flat=True)
        self.assertEqual(len(final_versions), 9)

if __name__ == '__main__':
    unittest.main()

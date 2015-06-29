import unittest

from betterversion.better import version_windows


class TestVersionWindows(unittest.TestCase):
    def setUp(self):
        self.versions = [
            '0.1.0',
            '0.2.0',
            '0.2.1',
            '0.3.0',
            '0.3.1',
            '1.1.0',
            '1.2.0',
            '1.3.0',
            '2.1.0',
            '2.2.0',
            '2.3.0',
            '2.3.1',
            '2.3.2',
            '2.3.3',
        ]

    def test_major(self):
        major_versions = version_windows(self.versions, major=1)
        self.assertEqual(major_versions, ['2.3.3'])

        major_versions = version_windows(self.versions, major=2)
        self.assertEqual(major_versions, ['1.3.0', '2.3.3'])

        major_versions = version_windows(self.versions, major=3)
        self.assertEqual(major_versions, ['0.3.1', '1.3.0', '2.3.3'])

        major_versions = version_windows(self.versions, major=4)
        self.assertEqual(major_versions, ['0.3.1', '1.3.0', '2.3.3'])

    def test_minor(self):
        minor_versions = version_windows(self.versions, minor=1)
        self.assertEqual(minor_versions, ['2.3.3'])

        minor_versions = version_windows(self.versions, minor=2)
        self.assertEqual(minor_versions, ['2.2.0', '2.3.3'])

        minor_versions = version_windows(self.versions, minor=3)
        self.assertEqual(minor_versions, ['2.1.0', '2.2.0', '2.3.3'])

        minor_versions = version_windows(self.versions, minor=4)
        self.assertEqual(minor_versions, ['2.1.0', '2.2.0', '2.3.3'])

    def test_point(self):
        point_versions = version_windows(self.versions, point=1)
        self.assertEqual(point_versions, ['2.3.3'])

        point_versions = version_windows(self.versions, point=2)
        self.assertEqual(point_versions, ['2.3.2', '2.3.3'])

        point_versions = version_windows(self.versions, point=3)
        self.assertEqual(point_versions, ['2.3.1', '2.3.2', '2.3.3'])

        point_versions = version_windows(self.versions, point=4)
        self.assertEqual(point_versions, ['2.3.0', '2.3.1', '2.3.2', '2.3.3'])

        point_versions = version_windows(self.versions, point=5)
        self.assertEqual(point_versions, ['2.3.0', '2.3.1', '2.3.2', '2.3.3'])

    def test_sort(self):
        final_versions = version_windows(self.versions,
                                         major=2, minor=2, point=1)

        self.assertEqual(final_versions, ['1.2.0', '1.3.0', '2.2.0', '2.3.3'])
        self.assertTrue('2.3.0' not in final_versions)

        final_versions = version_windows(self.versions,
                                         major=1, minor=2, point=2)

        # There is no 1.x in this list.
        # There are two 2.x versions.
        # There are two point releases if available.
        self.assertEqual(final_versions, ['2.2.0', '2.3.2', '2.3.3'])

        final_versions = version_windows(self.versions,
                                         major=1, minor=2, point=3)
        self.assertEqual(final_versions, ['2.2.0', '2.3.1', '2.3.2', '2.3.3'])


if __name__ == '__main__':
    unittest.main()

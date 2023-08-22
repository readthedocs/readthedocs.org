from django.test import TestCase

from readthedocs.subscriptions.constants import TYPE_AUDIT_LOGS, TYPE_CONCURRENT_BUILDS
from readthedocs.subscriptions.products import RTDProductFeature


class TestRTDProductFeature(TestCase):
    def test_add_feature(self):
        feature_a = RTDProductFeature(TYPE_CONCURRENT_BUILDS, value=1)
        feature_b = RTDProductFeature(TYPE_CONCURRENT_BUILDS, value=2)
        feature_c = feature_a + feature_b

        self.assertEqual(feature_c.unlimited, False)
        self.assertEqual(feature_c.value, 3)
        self.assertEqual(feature_c.type, TYPE_CONCURRENT_BUILDS)

    def test_add_feature_unlimited(self):
        feature_a = RTDProductFeature(TYPE_CONCURRENT_BUILDS, value=1)
        feature_b = RTDProductFeature(TYPE_CONCURRENT_BUILDS, unlimited=True)
        feature_c = feature_a + feature_b

        self.assertEqual(feature_c.unlimited, True)
        self.assertEqual(feature_c.type, TYPE_CONCURRENT_BUILDS)

    def test_add_different_features(self):
        feature_a = RTDProductFeature(TYPE_CONCURRENT_BUILDS, value=1)
        feature_b = RTDProductFeature(TYPE_AUDIT_LOGS, value=2)

        with self.assertRaises(ValueError):
            feature_a + feature_b

    def test_multiply_feature(self):
        feature_a = RTDProductFeature(TYPE_CONCURRENT_BUILDS, value=3)
        feature_b = feature_a * 2

        self.assertEqual(feature_b.value, 6)
        self.assertEqual(feature_b.unlimited, False)
        self.assertEqual(feature_b.type, TYPE_CONCURRENT_BUILDS)

        feature_a = RTDProductFeature(TYPE_CONCURRENT_BUILDS, value=3)
        feature_b = feature_a * 1

        self.assertEqual(feature_b.value, 3)
        self.assertEqual(feature_b.unlimited, False)
        self.assertEqual(feature_b.type, TYPE_CONCURRENT_BUILDS)

    def test_multiply_feature_unlimited(self):
        feature_a = RTDProductFeature(TYPE_CONCURRENT_BUILDS, unlimited=True)
        feature_b = feature_a * 2

        self.assertEqual(feature_b.unlimited, True)
        self.assertEqual(feature_b.type, TYPE_CONCURRENT_BUILDS)

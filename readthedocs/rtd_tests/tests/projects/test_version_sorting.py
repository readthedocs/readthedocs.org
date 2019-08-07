from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.constants import BRANCH
from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.projects.templatetags.projects_tags import sort_version_aware


class SortVersionsTest(TestCase):

    def setUp(self):
        self.project = get(Project)

    def test_basic_sort(self):
        identifiers = ['1.0', '2.0', '1.1', '1.9', '1.10']
        for identifier in identifiers:
            get(
                Version,
                project=self.project,
                type=BRANCH,
                identifier=identifier,
                verbose_name=identifier,
                slug=identifier,
            )

        versions = list(Version.objects.filter(project=self.project))
        self.assertEqual(
            ['latest', '2.0', '1.10', '1.9', '1.1', '1.0'],
            [v.slug for v in sort_version_aware(versions)],
        )

    def test_sort_wildcard(self):
        identifiers = ['1.0.x', '2.0.x', '1.1.x', '1.9.x', '1.10.x']
        for identifier in identifiers:
            get(
                Version,
                project=self.project,
                type=BRANCH,
                identifier=identifier,
                verbose_name=identifier,
                slug=identifier,
            )

        versions = list(Version.objects.filter(project=self.project))
        self.assertEqual(
            ['latest', '2.0.x', '1.10.x', '1.9.x', '1.1.x', '1.0.x'],
            [v.slug for v in sort_version_aware(versions)],
        )

    def test_sort_alpha(self):
        identifiers = ['banana', 'apple', 'carrot']
        for identifier in identifiers:
            get(
                Version,
                project=self.project,
                type=BRANCH,
                identifier=identifier,
                verbose_name=identifier,
                slug=identifier,
            )

        versions = list(Version.objects.filter(project=self.project))
        self.assertEqual(
            ['latest', 'carrot', 'banana', 'apple'],
            [v.slug for v in sort_version_aware(versions)],
        )
